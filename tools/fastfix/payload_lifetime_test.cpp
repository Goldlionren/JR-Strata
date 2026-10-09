#include "strata/verify_payload.hpp"
#include "strata/failed_work.hpp"
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <vector>
using strata::verify_payload::row;
struct Window {
    static constexpr int L=48, MT=6, N=17, K=10;
    struct Payload { std::array<float,N> x; std::array<int32_t,K> ids; std::array<float,K> weights; };
    std::vector<Payload> snapshots=std::vector<Payload>(L*MT);
    std::array<Payload,MT> old_reused{};
    uint64_t epoch=0; int seq=0, groups=1, T=0, host_done=0; bool graph_done=true,copy_done=true,poison=false;
    static Payload reference(uint64_t w,int l,int t) {
        Payload p{};
        for(int i=0;i<N;++i)p.x[i]=(float)(w*1024+l*19+t*3+i);
        for(int k=0;k<K;++k){p.ids[k]=(int32_t)((w+l*11+t*7+k)%512);p.weights[k]=(float)(l+t+k+1)/32;}
        return p;
    }
    bool begin(int t,bool split) {
        if(poison||!graph_done||!copy_done||host_done!=seq)return false;
        ++epoch;seq=host_done=0;T=t;groups=(split&&t>1)?2:1;graph_done=copy_done=false;return true;
    }
    void publish(int l,int tb,int te) {
        for(int t=tb;t<te;++t)snapshots[row(l,0,MT,t)]=old_reused[(size_t)t]=reference(epoch,l,t);
        ++seq; // system-fenced doorbell comes after all payload writes
    }
    bool serve(uint64_t expected,int l,int tb,int te) {
        if(expected!=epoch||poison||seq<host_done+1)return false;
        for(int t=tb;t<te;++t){auto& p=snapshots[row(l,0,MT,t)];auto ref=reference(epoch,l,t);
            assert(p.x==ref.x&&p.ids==ref.ids&&p.weights==ref.weights);}
        ++host_done;return true;
    }
};
int main(){int cases=0;
 // Exact archived lag shapes: host layer29 while GPU seq33; layer31 while GPU seq47.
 {for(auto pair:{std::pair{29,33},std::pair{31,47}}){Window w;assert(w.begin(1,false));
  for(int l=0;l<pair.second;++l)w.publish(l,0,1);
  assert(w.old_reused[0].x!=Window::reference(w.epoch,pair.first,0).x);
  for(int l=0;l<=pair.first;++l)assert(w.serve(w.epoch,l,0,1));
  assert(!w.begin(4,true));}++cases;}
 // Device skips let the graph advance all layers. Deliberately consume after graph finishes.
 {Window w;for(int n=0;n<300;++n){int T=std::array{1,4,6}[(size_t)n%3];bool mtp=n%2;
  assert(w.begin(T,mtp));const int split=w.groups==2?T/2:T;
  for(int l=0;l<Window::L;++l){w.publish(l,0,split);if(w.groups==2)w.publish(l,split,T);}
  w.graph_done=true;assert(!w.begin(T,mtp));
  for(int l=0;l<Window::L;++l){assert(w.serve(w.epoch,l,0,split));if(w.groups==2)assert(w.serve(w.epoch,l,split,T));}
  assert(!w.begin(T,mtp));w.copy_done=true;
 }++cases;}
 // A fallback blocks GPU advancement but a later device-plan skip can produce harmless host lag.
 {Window w;assert(w.begin(4,false));w.publish(0,0,4);assert(w.serve(w.epoch,0,0,4));
  for(int l=1;l<48;++l){w.publish(l,0,4);}
  for(int l=1;l<48;++l){assert(w.serve(w.epoch,l,0,4));}++cases;}
 // Payload identity belongs to this window: no old-window host callback may use newly overwritten rows.
 {Window w;assert(w.begin(1,false));for(int l=0;l<48;++l){w.publish(l,0,1);assert(w.serve(w.epoch,l,0,1));}
  auto old=w.epoch;w.graph_done=w.copy_done=true;assert(w.begin(6,true));w.publish(0,0,3);
  assert(!w.serve(old,0,0,3));assert(w.serve(w.epoch,0,0,3));++cases;}
 // No freeing/reuse on active timeout, including copy queues and host callbacks.
 {Window w;assert(w.begin(6,true));w.publish(0,0,3);w.poison=true;assert(!w.begin(1,false));
  int tick=0;auto d=strata::failed_work::drain(2,[&](size_t i){return i==0&&tick>=1;},[](size_t){},[&]{return tick>=3;},[&]{++tick;});
  assert(!d.safe()&&!w.serve(w.epoch,0,0,3));++cases;}
 // Split stages and groups: exact offsets, no adjacent-layer overwrite, stride always max_t (not T).
 {for(int lb:{0,24,46})for(int T:{1,4,6}){
  assert(row(lb,lb,6,0)==0&&row(lb+1,lb,6,0)==6);
  for(int t=0;t<T;++t)assert(row(lb+1,lb,6,t)==(size_t)(6+t));
 }++cases;}
 std::cout<<"PASS: "<<cases<<" host payload delay/generation/failure cases; 300 windows T=1/4/6 MTP on/off\n";
}
