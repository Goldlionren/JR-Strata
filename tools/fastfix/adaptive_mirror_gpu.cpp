// Narrow real-GGUF exchange + captured-graph/payload regression. Run only inside an approved GPU window.
#include "strata/core/gguf_expert_source.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"
#include "strata/kernels/resident_plan_mirror.hpp"
#include "strata/kernels/verify_kernels.hpp"
#include "strata/verify_payload.hpp"
#include "strata/sycl_verify_guard.hpp"
#include "strata/kernels/elementwise.hpp"
#include "strata/sycl_failed_work.hpp"
#include "strata/sycl_queue.hpp"
#include <array>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <future>
namespace ex=sycl::ext::oneapi::experimental;
void check(bool ok,const char* what) { if(!ok)throw std::runtime_error(what); }
uint32_t hash(const uint8_t* p,size_t n) {uint32_t h=2166136261u;for(size_t i=0;i<n;++i)h=(h^p[i])*16777619u;return h;}
int main(int argc,char** argv) try {
 check(argc==3,"usage: fastfix_adaptive_mirror PACK GGUF_SHARD1");
 auto& q=dpct::get_in_order_queue();
 const std::array<int,3> layers={0,32,46};constexpr int NL=48,NE=512;
 std::string err;check(strata::kernels::cpu::expert_layout_load(argv[1],NL,NE,err),err.c_str());
 const auto& lay=strata::kernels::cpu::expert_layout();
 // Source owns pinned blocks; the failure guard drains before cache/source owners unwind.
 strata::core::GgufExpertSource src;check(src.open(argv[2],NL,NE,err),err.c_str());
 strata::core::ExpertCache cache;
 strata::failed_work::FailureGuard failed{[]()noexcept{strata::drain_device_or_exit("adaptive mirror probe failed before owner cleanup");}};
 std::vector<int64_t> sizes;std::vector<std::pair<int64_t,int64_t>> missing;
 for(int l:layers){sizes.push_back((int64_t)lay.blob_bytes(l));missing.emplace_back(l,1);}
 check(cache.open_sized(sizes,NL,NE,err),err.c_str());
 std::vector<int32_t> res(NL*NE,-1);
 std::vector<std::vector<uint8_t>> refs;
 std::array<uint32_t,6> refhash{};
 for(size_t i=0;i<layers.size();++i)for(int e=0;e<2;++e){
   const int l=layers[i];refs.emplace_back((size_t)lay.blob_bytes(l));
   check(src.read_into(l,e,refs.back().data(),refs.back().size()),"independent GGUF read");
   refhash[i*2+e]=hash(refs.back().data(),refs.back().size());
   if(e==0){int slot=cache.admit(l,e);check(slot>=0,"admit");res[(size_t)l*NE]=slot;
     check(cache.fill_slot_blocking(slot,refs.back().data(),err,(int64_t)refs.back().size()),err.c_str());}
 }
 check(src.mirror(missing,64ull<<20,1,err)==3,err.c_str());
 const auto mirror_bytes=src.mirrored_bytes();
 auto* dres=sycl::malloc_device<int32_t>(res.size(),q);
 auto* mirrors=sycl::malloc_device<unsigned long long>(res.size(),q);
 auto* offsets=sycl::malloc_device<unsigned long long>(3,q);
 auto* ids=sycl::malloc_device<int32_t>(2,q);
 auto* plans=sycl::malloc_device<int32_t>(3*64,q);
 auto* skips=sycl::malloc_device<uint32_t>(3,q);
 auto* observations=(strata::aplan::Device*)strata::host_malloc_polled(3*sizeof(strata::aplan::Device),q);
 auto* got=sycl::malloc_host<uint32_t>(6,q);
 check(dres&&mirrors&&offsets&&ids&&plans&&skips&&observations&&got,"probe allocation");
 std::vector<unsigned long long> table;
 auto publish=[&]{src.mirror_table(table);q.memcpy(mirrors,table.data(),table.size()*8).wait_and_throw();
   q.memcpy(dres,res.data(),res.size()*4).wait_and_throw();};publish();
 const int32_t routes[2]={0,1};q.memcpy(ids,routes,sizeof routes).wait_and_throw();
 q.memcpy(offsets,cache.slot_offsets(),3*sizeof(uint64_t)).wait_and_throw();
 strata::kernels::resident_plan_set_mirror(dres,mirrors);
 uint8_t* base=cache.device_slot(0);
 ex::command_graph graph(q.get_context(),q.get_device());graph.begin_recording(q);
 for(size_t i=0;i<layers.size();++i){
   const int l=layers[i];const size_t bytes=(size_t)lay.blob_bytes(l);
   strata::kernels::resident_plan_observed(ids,2,2,dres+l*NE,NE,base,offsets,(long long)lay.max_blob,
      plans+i*64,2,skips+i,7,&q,observations+i);
   q.single_task([=]{for(int e=0;e<2;++e){const int32_t slot=dres[l*NE+e];
      const uint8_t* p=slot<0?(const uint8_t*)mirrors[l*NE+e]:base+offsets[slot];
      uint32_t h=2166136261u;for(size_t j=0;j<bytes;++j)h=(h^p[j])*16777619u;got[i*2+e]=h;}});
 }
 graph.end_recording(q);auto executable=graph.finalize();
 auto verify=[&]{for(size_t i=0;i<3;++i){observations[i]={};observations[i].expected=7;observations[i].generation=src.mirror_generation();}
   q.ext_oneapi_graph(executable).wait_and_throw();
   for(size_t i=0;i<6;++i)check(got[i]==refhash[i],"captured graph weight hash");
   for(size_t i=0;i<3;++i)check(observations[i].decision==1&&observations[i].route.missing==0&&
      observations[i].route.resident==1&&observations[i].route.mirrored==1,"captured resident/mirror coverage");};
 verify();
 auto* copy=dpct::get_current_device().create_queue(true);
 for(unsigned w=1;w<=12;++w){
   std::vector<strata::adaptive_mirror::Swap> batch;
   for(int l:layers){const size_t in=(size_t)l*NE+(w%2),out=(size_t)l*NE+((w+1)%2);batch.push_back({in,out,res[out]});}
   const auto before=res;
   std::promise<void> gate;auto release=gate.get_future().share();
   copy->submit([release](sycl::handler& h){h.host_task([release]{release.wait();});});
   // Release first on any synchronous failure; never leave a blocked task behind an exception.
   bool queued=false;try{queued=src.exchange_async(batch,res,cache,*copy,err);}catch(...){gate.set_value();throw;}
   bool rejected=false;if(queued){try{(void)src.device_alias(layers[0],0);}catch(const std::logic_error&){rejected=true;}}
   const bool unchanged=res==before;
   gate.set_value();check(queued,err.c_str());check(rejected&&unchanged,"early alias/residency publication");
   check(src.finish_exchanges(res,cache,err),err.c_str());copy->wait_and_throw();
   check(src.mirrored_bytes()==mirror_bytes,"mirror growth");
   for(const auto& s:batch)check(src.device_alias(s.in/NE,s.in%NE)==nullptr&&
      src.pinned(s.out/NE,s.out%NE)&&res[s.in]==s.slot&&res[s.out]==-1,"ownership commit");
   publish();verify();
 }
 dpct::get_current_device().destroy_queue(copy);
 strata::kernels::resident_plan_set_mirror(nullptr,nullptr);
 sycl::free(dres,q);sycl::free(mirrors,q);sycl::free(offsets,q);sycl::free(ids,q);sycl::free(plans,q);sycl::free(skips,q);
 strata::host_free_polled(observations,q);sycl::free(got,q);
 std::puts("PASS: actual GGUF mirror, 12 delayed exchange generations, layers0/32/46, independent full-blob hashes, reused captured plan");
 // Real doorbell launchers publish separate per-layer payloads. Host reads only after deliberate GPU-ahead
 // execution; same address layout as Verifier::record_window/run, T=1/4/6 and both grouping choices.
 constexpr int MAX_T=6,N=16,K=10,L=48;
 auto* hx=(float*)strata::host_malloc_polled(L*MAX_T*N*4,q);
 auto* hi=(int32_t*)strata::host_malloc_polled(L*MAX_T*K*4,q);
 auto* hw=(float*)strata::host_malloc_polled(L*MAX_T*K*4,q);
 auto* seq=(uint32_t*)strata::host_malloc_polled(64,q);
 auto* x=sycl::malloc_device<float>(L*MAX_T*N,q);
 auto* id=sycl::malloc_device<int32_t>(L*MAX_T*K,q);
 auto* weight=sycl::malloc_device<float>(L*MAX_T*K,q);
 check(hx&&hi&&hw&&seq&&x&&id&&weight,"payload allocation");
 std::vector<float> rx(L*MAX_T*N),rw(L*MAX_T*K);std::vector<int32_t> ri(L*MAX_T*K);
 for(int T:{1,4,6})for(bool split:{false,true}){
   const int groups=split&&T>1?2:1,half=groups==2?T/2:T;
   ex::command_graph g(q.get_context(),q.get_device());g.begin_recording(q);
   for(int l=0;l<L;++l)for(int group=0;group<groups;++group){int tb=group==0?0:half,te=group==0?half:T;
     const size_t at=strata::verify_payload::row(l,0,MAX_T,tb);
     strata::kernels::doorbell_publish(x+at*N,id+at*K,weight+at*K,(te-tb)*N,(te-tb)*K,
        hx+at*N,hi+at*K,hw+at*K,seq,&q);
   }
   g.end_recording(q);auto e=g.finalize();
   for(int w=1;w<=2;++w){
     for(size_t i=0;i<rx.size();++i)rx[i]=(float)(w*10000+i);
     for(size_t i=0;i<ri.size();++i){ri[i]=(int32_t)((i+w)%512);rw[i]=(float)(i+w)/32;}
     q.memcpy(x,rx.data(),rx.size()*4).wait_and_throw();q.memcpy(id,ri.data(),ri.size()*4).wait_and_throw();
     q.memcpy(weight,rw.data(),rw.size()*4).wait_and_throw();seq[0]=0;
     q.ext_oneapi_graph(e).wait_and_throw();check(seq[0]==(unsigned)(L*groups),"payload progress");
     for(int l=0;l<L;++l)for(int t=0;t<T;++t){size_t at=strata::verify_payload::row(l,0,MAX_T,t);
       check(std::memcmp(hx+at*N,rx.data()+at*N,N*4)==0&&std::memcmp(hi+at*K,ri.data()+at*K,K*4)==0&&
         std::memcmp(hw+at*K,rw.data()+at*K,K*4)==0,"delayed host layer payload mismatch");}
   }
 }
 q.wait_and_throw();for(void* p:{(void*)hx,(void*)hi,(void*)hw,(void*)seq})strata::host_free_polled(p,q);
 sycl::free(x,q);sycl::free(id,q);sycl::free(weight,q);
 std::puts("PASS: captured doorbell payloads with GPU-ahead host delays, T=1/4/6, split/unsplit, changing windows");failed.accepted=true;return 0;
} catch(const std::exception& e) {
 std::fprintf(stderr,"FAIL: %s\n",e.what());strata::drain_device_or_exit("adaptive mirror GPU probe exception");return 1;
}
