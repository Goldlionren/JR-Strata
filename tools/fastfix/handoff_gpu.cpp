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
 // GPU writes become host input only after the same explicit wait used by historical MTP.
 auto* out=(float*)strata::host_malloc_polled(64,q);
 for(int w=1;w<=12;++w) {
   out[0]=-1;out[1]=-1;
   q.single_task([=]{out[0]=float(w);out[1]=.75f;});q.wait_and_throw();
   check(strata::core::valid_draft_result((int)out[0],out[1],100));check(out[0]==w);
 }
 strata::host_free_polled(out,q);strata::host_free_polled(f,q);strata::host_free_polled(seq,q);sycl::free(skip,q);
 puts("PASS: 12 changing readiness rounds, skipped mirror plans, all three timeout latches, completed host outputs");return 0;
} catch(const std::exception& e){std::fprintf(stderr,"FAIL: %s\n",e.what());return 1;}
