#include "strata/aplan_observation.hpp"
#include "strata/readiness_policy.hpp"
#include "strata/failed_work.hpp"
#include <array>
#include <cassert>
#include <cstdio>
using namespace strata::aplan;
using strata::readiness::Plan;
struct Machine {
    Device d{}; uint32_t a=0,b=0,m=0,skip=0; bool complete=true,copy_complete=true,poison=false;
    void window(uint64_t generation,uint32_t ring) {
        assert(complete&&copy_complete&&!poison);d={};d.generation=generation;d.expected=ring;a=b=m=skip=0;complete=false;
    }
    void route(bool covered) {d.entered=d.expected;d.entries=10;d.decision=covered?1:2;
        if(covered)skip=d.skip_written=d.expected;else{d.route.missing=1;d.shared_bad=1;}}
    Plan consume_a(uint32_t visible) {d.wait[0]={d.expected,skip,visible,visible,0,d.expected};
        auto p=strata::readiness::plan(0,visible,d.expected,skip);d.copy_action=uint32_t(p)+1;return p;}
    void publish_a() {assert(d.entered);a=d.expected;} // metadata may precede DMA completion
    void submit_copy() {copy_complete=false;}
    void finish_copy() {copy_complete=true;b=d.expected;}
    bool weights_ready() const {return skip==d.expected || (b>=d.expected&&copy_complete);}
};
int main(){int cases=0;
 {int32_t ids[]={0,1,2},s[]={0,-1,-1};unsigned long long m[]={0,123,0};auto r=inspect(ids,s,m,3,3);
  assert(r.resident==1&&r.mirrored==1&&r.missing==1&&r.first_bad==2&&r.expert==2);++cases;}
 {int32_t ids[]={-1,512,1},s[]={-1,-1,2};unsigned long long m[]={0,0,0};auto r=inspect(ids,s,m,3,512);
  assert(r.invalid==2&&r.missing==0&&r.resident==1);++cases;}
 {Machine x;x.window(896,47);x.route(false);x.a=40;assert(x.consume_a(40)==Plan::reject);
  assert(classify(x.d,896,47)==Finding::rejected_routes);x.publish_a();assert(x.a==47);++cases;} // delayed host, later final A is not proof of visibility failure
 {Machine x;x.window(896,47);x.route(false);x.publish_a();assert(x.consume_a(40)==Plan::reject);
  assert(x.a==47);++cases;} // distinct injected stale consumer, same timeout symptom
 {Machine x;x.window(896,47);x.route(true);assert(x.consume_a(0)==Plan::device);
  assert(classify(x.d,896,47)==Finding::completed);++cases;}
 {Machine x;x.window(896,47);x.route(true);x.skip=0;assert(x.consume_a(40)==Plan::reject);
  assert(classify(x.d,896,47)==Finding::skip_mismatch);++cases;}
 {Machine x;x.window(896,47);assert(classify(x.d,896,47)==Finding::incomplete);++cases;} // producer node never reached
 {Machine x;x.window(896,47);x.route(true);assert(classify(x.d,896,47)==Finding::incomplete);++cases;} // downstream waiter not reached
 {Machine x;x.window(896,47);x.route(false);x.d.route.missing=0;
  assert(classify(x.d,896,47)==Finding::unexplained_reject);++cases;}
 {Machine x;x.window(896,47);x.route(false);x.publish_a();x.submit_copy();
  assert(x.consume_a(x.a)==Plan::host&&!x.weights_ready());x.finish_copy();assert(x.weights_ready());++cases;}
 {Machine x;x.window(896,47);x.route(true);x.consume_a(0);
  assert(classify(x.d,897,47)==Finding::incomplete&&classify(x.d,896,33)==Finding::incomplete);++cases;}
 {for(bool mtp:{false,true}){Machine x;for(uint64_t w=1;w<=1000;++w){x.window(w,47);x.route(true);
  assert(x.consume_a(0)==Plan::device);assert(classify(x.d,w,47)==Finding::completed);
  x.complete=true;assert(!mtp||x.copy_complete);}}++cases;}
 {uint32_t f[4]={};auto l=[](const uint32_t*p){return *p;};auto s=[](uint32_t*p,uint32_t v){*p=v;};
  strata::readiness::timeout(f,33,30,0,l,s);strata::readiness::timeout(f,47,40,0,l,s);
  assert(f[1]==33&&f[2]==30);assert(strata::readiness::plan(f[1],48,48,48)==Plan::reject);++cases;}
 {bool freed=false,poison=false;int tick=0;
  {strata::failed_work::FailureGuard g{[&]()noexcept{poison=true;auto r=strata::failed_work::drain(2,
    [&](size_t i){return i==1&&tick>=2;},[](size_t){},[&]{return tick>=5;},[&]{++tick;});freed=r.safe();}};}
  assert(poison&&!freed);++cases;}
 // Exact source invariant: a static complement mirror plus a completed adaptive swap.
 // No DMA fault or stale readiness is needed to create a new uncovered expert.
 {int32_t ids[]={0,1},slots[]={0,-1};unsigned long long mirror[]={0,123};
  auto before=inspect(ids,slots,mirror,2,2);assert(before.missing==0);
  slots[0]=-1;slots[1]=0; // swap completes and the new residency is published
  auto after=inspect(ids,slots,mirror,2,2);assert(after.missing==1&&after.expert==0);++cases;}
 // Adaptive-off control: preserve startup slots and static complement through changing windows.
 {for (bool enabled : {false,true}) {
    int32_t ids[64]={},slots[64]={};unsigned long long mirror[64]={};
    for(int i=0;i<64;++i){slots[i]=(i%2==0)?i/2:-1;mirror[i]=(i%2)?123ull+16*i:0ull;}
    const auto startup=std::array<int32_t,2>{slots[0],slots[1]};
    int swaps=0;
    for(int w=1;w<=1000;++w){
        // Serving gate: usage is initialized only when both adaptation controls are positive.
        const bool usage_nonempty=enabled;
        if(usage_nonempty && w%4==0 && swaps==0){slots[1]=slots[0];slots[0]=-1;++swaps;}
        for(int t : {1,4,6}){
            const int n=t*10;
            int32_t routed_slots[64];unsigned long long routed_mirror[64];
            for(int i=0;i<n;++i){ids[i]=(i+w)%64;routed_slots[i]=slots[ids[i]];routed_mirror[i]=mirror[ids[i]];}
            auto inspected=inspect(ids,routed_slots,routed_mirror,n,64);
            if(!enabled)assert(inspected.missing==0&&inspected.invalid==0);
        }
    }
    if(!enabled)assert(swaps==0&&slots[0]==startup[0]&&slots[1]==startup[1]);
    else {int32_t id[]={0},sl[]={slots[0]};unsigned long long mir[]={mirror[0]};assert(swaps==1&&inspect(id,sl,mir,1,64).missing==1);}
 }++cases;}
 std::printf("PASS: %d deterministic A-plan state/fault cases; CPU evidence only, not GPU visibility proof; record bytes=%zu\n",cases,sizeof(Device));
}
