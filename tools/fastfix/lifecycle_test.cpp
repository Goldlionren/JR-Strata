#include "strata/failed_work.hpp"
#include "strata/readiness_policy.hpp"
#include <array>
#include <cassert>
#include <cstdio>
#include <stdexcept>
#include <vector>
using strata::failed_work::drain;
struct Queue { int ready_at=0, queries=0, finishes=0; bool query_error=false, async_error=false; };
struct Rig {
    int tick=0; std::array<Queue,3> q{};
    auto run(int deadline=8) {
        return drain(q.size(), [&](size_t i) {
            ++q[i].queries;
            if(q[i].query_error) throw std::runtime_error("lost queue");
            return tick>=q[i].ready_at;
        }, [&](size_t i) {
            ++q[i].finishes;
            assert(tick>=q[i].ready_at);
            if(q[i].async_error) throw std::runtime_error("async DMA failure");
        }, [&]{return tick>=deadline;}, [&]{++tick;});
    }
};
int main() {
    int cases=0;
    { Rig r;r.q[0].ready_at=99;auto x=r.run();assert(!x.complete&&!x.safe());assert(r.q[0].finishes==0);++cases; }
    { Rig r;r.q[1].ready_at=5;auto x=r.run();assert(x.safe()&&r.tick==5);for(auto q:r.q)assert(q.finishes==1);++cases; }
    { Rig r;r.q[0].query_error=true;r.q[1].ready_at=2;auto x=r.run();assert(!x.safe()&&x.error);assert(r.q[1].queries==9);++cases; }
    { Rig r;r.q[0].async_error=true;auto x=r.run();assert(x.complete&&!x.safe());assert(r.q[1].finishes==1&&r.q[2].finishes==1);++cases; }
    { Rig r;r.q[0].ready_at=99;r.q[1].ready_at=3;bool freed=false,retained=false,poisoned=false;
      { strata::failed_work::FailureGuard guard{[&]() noexcept {poisoned=true;auto x=r.run();retained=!x.safe();}};
      }
      if(!retained)freed=true;
      assert(poisoned&&retained&&!freed);++cases; }
    { Rig r;bool failed=false; {strata::failed_work::FailureGuard guard{[&]() noexcept {failed=true;r.run();}};guard.accepted=true;}
      assert(!failed&&r.q[0].queries==0);++cases; } // zero drain on successful window
    { unsigned flag=0;std::vector<strata::failed_work::Publication> callbacks;
      for(unsigned w=1;w<=300;++w)callbacks.push_back({&flag,w}); // beyond old 256-entry argument reuse
      for(unsigned w=1;w<=300;++w){callbacks[w-1]([](unsigned*p,unsigned v){*p=v;});assert(flag==w);}++cases; }
    { for(bool mtp:{false,true})for(int w=1;w<=12;++w){Rig r;r.q[0].ready_at=1;r.q[1].ready_at=2;r.q[2].ready_at=mtp?3:0;
      auto x=r.run();assert(x.safe()&&r.tick==(mtp?3:2));}++cases; }
    { using namespace strata::readiness;assert(plan(0,0,33,0)==Plan::reject);
      assert(plan(33,99,34,34)==Plan::reject);assert(plan(0,0,33,33)==Plan::device);
      assert(plan(0,33,33,0)==Plan::host);assert(plan(0,34,33,0)==Plan::host);++cases; }
    { unsigned f[4]={0};auto load=[](const unsigned*p){return *p;};auto store=[](unsigned*p,unsigned v){*p=v;};
      strata::readiness::timeout(f,33,30,0,load,store);strata::readiness::timeout(f,48,47,48,load,store);
      assert(f[1]==33&&f[2]==30&&f[3]==0);++cases; }
    { Rig r;bool poisoned=false;try {strata::failed_work::FailureGuard guard{[&]()noexcept{poisoned=true;assert(r.run().safe());}};
      throw std::runtime_error("partial graph submission");}catch(const std::runtime_error&){}
      assert(poisoned&&r.q[1].finishes==1);++cases; }
    std::printf("PASS: %d lifecycle/readiness fault-injection cases (CPU policy; GPU behavior pending)\n",cases);
}
