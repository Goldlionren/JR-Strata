// Small independent IQ4_NL oracle; same tests can use a captured SYCL copy.
#include <atomic>
#include "strata/kernels/ngram.hpp"
#include <algorithm>
#include <bit>
#include <cstdio>
#include <fstream>
#include <future>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef PLEFIX_GPU
#include <sycl/sycl.hpp>
#include "strata/sycl_queue.hpp"
#include "strata/kernels/elementwise.hpp"
#include <sycl/ext/oneapi/experimental/graph.hpp>
#endif
namespace k = strata::kernels;
void require(bool ok, const std::string& why) { if (!ok) throw std::runtime_error(why); }
void le(std::ofstream& f, uint64_t v, int n) { for(int i=0;i<n;++i) f.put(char(v>>(8*i))); }
void str(std::ofstream& f, const std::string& s) { le(f,s.size(),8); f.write(s.data(),s.size()); }
constexpr unsigned R=4096;
constexpr int codebook[]={-127,-104,-83,-65,-49,-35,-22,-10,1,13,25,38,53,69,89,113};
float oracle(unsigned row, unsigned col) { return float(codebook[(row+col)%16]); }
void table(const std::string& path) {
    std::ofstream f(path,std::ios::binary);
    f.write("GGUF",4); le(f,3,4); le(f,1,8); le(f,1,8);
    str(f,"general.architecture"); le(f,8,4); str(f,"strata-ple");
    str(f,"per_layer_token_embd.weight"); le(f,2,4); le(f,160,8); le(f,R,8); le(f,20,4); le(f,0,8);
    while (f.tellp()%32) f.put(0);
    for(unsigned row=0;row<R;++row) for(unsigned b=0;b<5;++b) {
        le(f,0x3c00,2); // fp16 scale exactly 1, independent expected integer values
        for(unsigned j=0;j<16;++j) f.put(char(((row+b*32+j)%16)|(((row+b*32+j+16)%16)<<4)));
    }
    require(bool(f),"write synthetic table");
}
int main(int argc,char**argv) try {
    require(argc==2,"usage: ple_staging_test NEW_SYNTHETIC_GGUF_PATH");
    require(!std::ifstream(argv[1]).good(),"refuse existing file"); table(argv[1]);
    unsigned windows=0, submissions=0;
    for (auto mode : {k::PleIo::Direct,k::PleIo::Mmap}) {
      k::PleIoOptions io; io.mode=mode; io.cache_rows=1024; io.max_inflight=16; io.keepalive_ms=0;
      k::PleTable t; std::string err; require(t.open(argv[1],err,io),err);
      if(mode==k::PleIo::Direct) t.set_injected_delay_us(2000); // collect must finish before submission
      for(int T : {1,4,6}) {
        const size_t n=T*k::PLE_N_HEADS*k::PLE_HEAD_DIM;
        std::vector<float> storage(n,-999), result(n);
        float* h=storage.data();
#ifdef PLEFIX_GPU
        sycl::queue q{sycl::gpu_selector_v,sycl::property::queue::in_order{}};
        h=static_cast<float*>(strata::host_malloc_polled(n*sizeof(float),q)); float* d=sycl::malloc_device<float>(n,q);
        require(h && d,"USM allocation");
        namespace ex=sycl::ext::oneapi::experimental;
        ex::command_graph graph(q.get_context(),q.get_device());
        graph.begin_recording(q); k::copy_from_mapped(d,h,n,&q); graph.end_recording(q);
        auto executable=graph.finalize();
#endif
        for(int request=0;request<3;++request) for(int w=0;w<5;++w) {
          std::vector<uint32_t> rows(T*k::PLE_N_HEADS);
          for(size_t i=0;i<rows.size();++i) rows[i]=w==3?37:(request*701+w*127+i*41)%R;
          std::fill(h,h+n,-999);
          for(int j=0;j<T;++j) t.prefetch_rows(rows.data()+j*k::PLE_N_HEADS);
          unsigned gathers=0;
          ++gathers; require(t.gather_batch(rows.data(),T,h,err),err);
          std::atomic_thread_fence(std::memory_order_seq_cst);
          require(gathers==1,"exactly one staging gather");
          ++submissions;
#ifdef PLEFIX_GPU
          q.ext_oneapi_graph(executable).wait_and_throw();
          q.memcpy(result.data(),d,n*sizeof(float)).wait_and_throw();
#else
          // CPU consumer, not a claim of SYCL visibility. GPU variant above is a separate gate.
          auto done=std::async(std::launch::async,[&]{std::copy(h,h+n,result.begin());}); done.get();
#endif
          for(size_t i=0;i<n;++i) require(result[i]==oracle(rows[i/k::PLE_HEAD_DIM],i%k::PLE_HEAD_DIM),"stale/wrong row at window "+std::to_string(w));
          ++windows;
        }
#ifdef PLEFIX_GPU
        q.wait_and_throw(); sycl::free(d,q); strata::host_free_polled(h,q);
#endif
      }
      const auto before=submissions;
      // Real gather failure from incompatible in-flight single-token state: no graph may be submitted.
      uint32_t rows[k::PLE_N_HEADS]={}; float out[k::PLE_N_HEADS*k::PLE_HEAD_DIM];
      require(t.issue(rows),"single issue");
      if(t.gather_batch(rows,1,out,err)) ++submissions;
      require(submissions==before && !err.empty(),"failure submitted graph"); require(t.collect(out,err),err);
    }
    // Independent hash oracle verifies oldest/newest history and EOS cut semantics.
    auto c=k::ple_artifact_consts();
    for(int T : {1,4,6}) {
      std::vector<int32_t> tokens(T),prev(T*2); std::vector<uint32_t> rows(T*16);
      for(int i=0;i<T;++i) { tokens[i]=101+i;prev[2*i]=i?tokens[i-1]:-1;prev[2*i+1]=i?211+i:k::PLE_EOS_TOKEN_ID; }
      k::ngram_rows(tokens.data(),prev.data(),T,c,rows.data());
      for(int i=0;i<T;++i) for(int h=0;h<16;++h) {
        uint64_t mix=uint64_t(tokens[i])*c.mult[0]; bool cut=false;
        for(int j=1;j<=1+h/8;++j) {
          auto v=prev[2*i+2-j]; cut=cut || v<0 || v==k::PLE_EOS_TOKEN_ID;
          mix^=uint64_t(cut?k::PLE_EOS_TOKEN_ID:v)*c.mult[j];
        }
        require(rows[i*16+h]==mix%c.vocab[h]+c.offset[h],"history hash oracle");
      }
    }
    std::remove(argv[1]);
    std::printf("PASS: %u windows, T=1/4/6, 3 request histories, changed/repeated rows, Direct/Mmap IQ4_NL independent oracle, delayed IO, error-before-submit, history oracle\n",windows);
    return 0;
} catch(const std::exception& e) { std::fprintf(stderr,"FAIL: %s\n",e.what()); return 1; }
