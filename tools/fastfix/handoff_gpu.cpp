#include "strata/failed_work.hpp"
#include <future>
#include "strata/sycl_verify_guard.hpp"
#include "strata/kernels/resident_plan_mirror.hpp"
// Test the real SYCL wait launchers, including skipped device plans and expired host readiness.
#include "strata/sycl_queue.hpp"
#include "strata/kernels/verify_kernels.hpp"
#include "strata/kernels/elementwise.hpp"
#include "strata/core/fastfix_output.hpp"
#include <stdexcept>
#include <cstdio>
int main() try {
 auto& q=dpct::get_in_order_queue();
 auto* f=(uint32_t*)strata::host_malloc_polled(64,q);
 auto* seq=(uint32_t*)strata::host_malloc_polled(64,q);
 auto* skip=sycl::malloc_device<uint32_t>(1,q);
 if(!f||!seq||!skip) throw std::runtime_error("allocation");
 auto check=[&](bool ok){if(!ok) throw std::runtime_error("readiness latch mismatch");};
 for(unsigned w=1;w<=12;++w) {
   f[0]=w;f[1]=0;seq[0]=w;
   strata::kernels::wait_flag_ge(f,w,&q); strata::kernels::doorbell_wait(f,seq,&q);
   q.wait_and_throw();check(f[1]==0);
   f[0]=0;f[1]=0;q.memcpy(skip,&w,4).wait_and_throw();
   strata::kernels::wait_flag_ge_or(f,w,skip,&q);q.wait_and_throw();check(f[1]==0);
   q.memset(skip,0,4).wait_and_throw();
   strata::kernels::wait_flag_ge_or(f,w,skip,&q);q.wait_and_throw();check(f[1]==w);
   f[1]=0;strata::kernels::wait_flag_ge(f,w,&q);q.wait_and_throw();check(f[1]==w);
   f[1]=0;strata::kernels::doorbell_wait(f,seq,&q);q.wait_and_throw();check(f[1]==w);
 }

 // Captured graph must reject an unavailable plan WITHOUT reading its source.
 // nullptr deliberately catches accidental reads; only four count words may change.
 auto* plan=sycl::malloc_device<int32_t>(16,q);
 int32_t hp[16];
 for(unsigned w=1;w<=12;++w) {
   for(int i=0;i<16;++i)hp[i]=123;
   q.memcpy(plan,hp,sizeof hp).wait_and_throw();
   f[0]=0;f[1]=f[2]=f[3]=0;q.memset(skip,0,4).wait_and_throw();
   namespace ex=sycl::ext::oneapi::experimental;
   ex::command_graph graph(q.get_context(),q.get_device());
   graph.begin_recording(q);
   strata::kernels::wait_verify_ready(f,w,skip,nullptr,&q);
   strata::kernels::copy_verify_plan(plan,nullptr,16,skip,w,f,&q);
   graph.end_recording(q);
   auto exec=graph.finalize();q.ext_oneapi_graph(exec).wait_and_throw();
   q.memcpy(hp,plan,sizeof hp).wait_and_throw();
   check(f[1]==w&&f[2]==0&&f[3]==0);
   for(int i=0;i<16;++i)check(hp[i]==(i<4?0:123));
   // A later expired B wait cannot overwrite first-failure evidence or consume weights.
   strata::kernels::wait_verify_ready(f,w+1,nullptr,plan,&q);q.wait_and_throw();check(f[1]==w);
   q.memcpy(hp,plan,sizeof hp).wait_and_throw();for(int i=0;i<4;++i)check(hp[i]==0);
 }
 sycl::free(plan,q);
 // Exercise diagnostic coverage inside a real captured resident-plan graph, without expert arithmetic.
 // One graph is reused across covered/missing/invalid routes and generation identities.
 {
   auto* dres=sycl::malloc_device<int32_t>(2,q);
   auto* ids=sycl::malloc_device<int32_t>(2,q);
   auto* mirror=sycl::malloc_device<unsigned long long>(2,q);
   auto* cache=sycl::malloc_device<uint8_t>(64,q);
   auto* pl=sycl::malloc_device<int32_t>(64,q);
   auto* host=(int32_t*)strata::host_malloc_polled(256,q);
   auto* obs=(strata::aplan::Device*)strata::host_malloc_polled(sizeof(strata::aplan::Device),q);
   if(!dres||!ids||!mirror||!cache||!pl||!host||!obs)throw std::runtime_error("diagnostic allocation");
   for(int i=0;i<64;++i)host[i]=0;
   int32_t res[]={0,-1};q.memcpy(dres,res,sizeof res).wait_and_throw();
   strata::kernels::resident_plan_set_mirror(dres,mirror);
   namespace ex=sycl::ext::oneapi::experimental;
   ex::command_graph graph(q.get_context(),q.get_device());
   graph.begin_recording(q);
   strata::kernels::resident_plan_observed(ids,2,2,dres,2,cache,nullptr,32,pl,2,skip,7,&q,obs);
   strata::kernels::wait_verify_ready(f,7,skip,nullptr,&q,&obs->wait[0]);
   strata::kernels::copy_verify_plan(pl,host,32,skip,7,f,&q,obs);
   graph.end_recording(q);auto exec=graph.finalize();
   for(unsigned w=1;w<=4;++w){
     *obs={};obs->generation=w;obs->expected=7;
     int32_t route[]={0,w==3?9:1};unsigned long long mirrors[]={0,w==2?0ull:(unsigned long long)host};
     q.memcpy(ids,route,sizeof route).wait_and_throw();q.memcpy(mirror,mirrors,sizeof mirrors).wait_and_throw();
     f[0]=7;f[1]=f[2]=f[3]=0;
     q.ext_oneapi_graph(exec).wait_and_throw();
     const bool covered=w==1||w==4;
     check(obs->entered==7&&obs->generation==w&&obs->wait[0].exited==7);
     check(obs->decision==(covered?1u:2u)&&obs->copy_action==(covered?2u:3u));
     check(obs->route.invalid==(w==3?1u:0u)&&obs->route.missing==(w==2?1u:0u));
     if(covered)check(obs->skip_written==7&&obs->route.mirrored==1&&obs->route.resident==1);
   }
   strata::kernels::resident_plan_set_mirror(nullptr,nullptr);
   sycl::free(dres,q);sycl::free(ids,q);sycl::free(mirror,q);sycl::free(cache,q);sycl::free(pl,q);
   strata::host_free_polled(host,q);strata::host_free_polled(obs,q);
   puts("PASS: 4 captured A-plan diagnostic generations, mixed mirror/device, missing/invalid routes");
 }
 // A deliberately withheld DMA host task proves readiness cannot publish early.
 // No arbitrary delay: a future controls release; the copy queue stays in-order.
 {
   sycl::queue copy(q.get_context(),q.get_device(),
       [](sycl::exception_list es){for(auto e:es)std::rethrow_exception(e);},
       sycl::property_list{sycl::property::queue::in_order{}});
   auto* target=sycl::malloc_device<int>(1,q);
   for(unsigned w=1;w<=12;++w) {
     std::promise<void> gate;auto opened=gate.get_future().share();
     int input=int(w),output=-1;f[0]=0;
     copy.submit([opened](sycl::handler& h){h.host_task([opened]{opened.wait();});});
     auto moved=copy.memcpy(target,&input,sizeof input);
     const strata::failed_work::Publication publication{f,w};
     auto published=copy.submit([publication,moved](sycl::handler& h){
       h.depends_on(moved);
       h.host_task([publication]{publication([](unsigned* p,unsigned v){__atomic_store_n(p,v,__ATOMIC_SEQ_CST);});});
     });
     const bool not_ready=__atomic_load_n(f,__ATOMIC_SEQ_CST)==0 &&
       published.get_info<sycl::info::event::command_execution_status>()!=sycl::info::event_command_status::complete;
     gate.set_value();copy.wait_and_throw(); // release before any assertion can throw
     check(not_ready&&f[0]==w);
     q.memcpy(&output,target,sizeof output).wait_and_throw();check(output==input);
   }
   sycl::free(target,q);
 }
 // GPU writes become host input only after the same explicit wait used by historical MTP.
 auto* out=(float*)strata::host_malloc_polled(64,q);
 for(int w=1;w<=12;++w) {
   out[0]=-1;out[1]=-1;
   q.single_task([=]{out[0]=float(w);out[1]=.75f;});q.wait_and_throw();
   check(strata::core::valid_draft_result((int)out[0],out[1],100));check(out[0]==w);
 }
 strata::host_free_polled(out,q);strata::host_free_polled(f,q);strata::host_free_polled(seq,q);sycl::free(skip,q);
 puts("PASS: 12 captured guarded-plan rounds plus 12 changing readiness rounds, skipped mirror plans, all three timeout latches, completed host outputs");return 0;
} catch(const std::exception& e){std::fprintf(stderr,"FAIL: %s\n",e.what());return 1;}
