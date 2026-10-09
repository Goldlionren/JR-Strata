#include "strata/adaptive_mirror.hpp"
#include "strata/failed_work.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <functional>
#include <iostream>
#include <numeric>
using namespace strata::adaptive_mirror;
struct Sim {
    static constexpr size_t E=8,L=3,B=31;
    std::vector<int32_t> res, device_res;
    std::vector<uint8_t*> mirror, device_mirror;
    std::array<std::array<uint8_t,B>,L*E/2> gpu{},host{};
    std::array<uint8_t,B> scratch{};
    std::vector<std::function<void()>> dma;
    Batch batch; uint64_t generation=0, published=0; std::string err;
    Sim():res(L*E,-1),mirror(L*E,nullptr) {
        for(size_t i=0;i<L*E;++i) {
            if(i%2==0) {res[i]=(int32_t)(i/2);gpu[i/2]=reference(i);}
            else {mirror[i]=host[i/2].data();host[i/2]=reference(i);}
        }
        publish();
    }
    static std::array<uint8_t,B> reference(size_t i) {
        std::array<uint8_t,B> v{};for(size_t j=0;j<B;++j)v[j]=(uint8_t)((i*73+j*17)^j);return v;
    }
    void check() {
        size_t ng=0,nh=0;std::vector<int> seen(L*E/2,0);
        for(size_t i=0;i<L*E;++i) {
            const uint8_t* p;
            if(res[i]>=0) {assert(!mirror[i]);assert(++seen[(size_t)res[i]]==1);p=gpu[(size_t)res[i]].data();++ng;}
            else {assert(mirror[i]);p=mirror[i];++nh;}
            const auto expected=reference(i);assert(std::memcmp(p,expected.data(),B)==0);
        }
        assert(ng==L*E/2&&nh==L*E/2);
    }
    bool begin(std::vector<Swap> swaps) {
        if(!batch.prepare(swaps,E,res,mirror,generation,err))return false;
        enqueue(batch,scratch.data(),[&](int32_t slot){return gpu[(size_t)slot].data();},
            [](size_t){return B;},[&](uint8_t* dst,const uint8_t* src,size_t n){
                dma.push_back([=]{std::memcpy(dst,src,n);});});
        return true;
    }
    void advance(size_t n) {
        while(n-- && !dma.empty()){auto f=dma.front();dma.erase(dma.begin());f();}
    }
    void finish() {assert(dma.empty());batch.copies_completed();assert(batch.commit(res,mirror,generation,err));}
    void publish() {device_mirror=mirror;device_res=res;published=generation;}
    void read_window(int T,bool mtp) {
        assert(!batch.active()&&generation==published);
        for(int layer=0;layer<(int)L;++layer)for(int row=0;row<T;++row) {
            const size_t id=(size_t)layer*E+(row+(mtp?2:0))%E;
            const auto* p=device_res[id]<0?device_mirror[id]:gpu[(size_t)device_res[id]].data();
            const auto expected=reference(id);assert(p&&std::memcmp(p,expected.data(),B)==0);
        }
    }
};
int main() {int cases=0;
 {Sim x;x.check();for(int T:{1,4,6})for(bool mtp:{false,true})x.read_window(T,mtp);++cases;}
 {Sim x;for(int w=0;w<1000;++w){std::vector<Swap> b;
  for(size_t l=0;l<Sim::L;++l){size_t in=0,out=0;for(size_t e=0;e<Sim::E;++e){size_t i=l*Sim::E+e;if(x.res[i]<0)in=i;else out=i;}b.push_back({in,out,x.res[out]});}
  assert(x.begin(b));x.advance(99);x.finish();x.publish();x.check();for(int T:{1,4,6})for(bool mtp:{false,true})x.read_window(T,mtp);}
  assert(x.generation==1000);++cases;}
 {Sim x;auto* slot=x.mirror[1];assert(x.begin({{1,0,0}}));
  assert(!x.batch.commit(x.res,x.mirror,x.generation,x.err));x.advance(1);
  assert(x.scratch==Sim::reference(0)&&x.host[0]==Sim::reference(1));
  assert(!x.batch.commit(x.res,x.mirror,x.generation,x.err));x.advance(1);
  assert(x.gpu[0]==Sim::reference(1)&&x.host[0]==Sim::reference(1));
  assert(!x.batch.commit(x.res,x.mirror,x.generation,x.err));x.advance(1);x.finish();
  assert(!x.mirror[1]&&x.mirror[0]==slot&&x.host[0]==Sim::reference(0));
  assert(x.published!=x.generation);x.publish();x.check();++cases;}
 {Sim x;assert(x.begin({{1,0,0},{3,2,1}}));x.advance(3);
  assert(x.host[0]==Sim::reference(0));x.advance(3);x.finish();x.publish();x.check();++cases;}
 {Sim x;assert(!x.begin({{1,0,0},{1,2,1}}));assert(!x.batch.active());x.check();++cases;}
 {Sim x;assert(!x.begin({{9,0,0}}));x.check();++cases;}
 {Sim x;x.mirror[1]=nullptr;assert(!x.begin({{1,0,0}}));assert(x.dma.empty());++cases;}
 {Sim x;assert(!x.begin({{1,0,3}}));assert(x.dma.empty());++cases;}
 {Sim x;assert(x.begin({{1,0,0}}));assert(!x.begin({{3,2,1}}));x.advance(3);x.finish();x.publish();x.check();++cases;}
 {Sim x;assert(x.begin({{1,0,0}}));x.advance(3);x.batch.copies_completed();++x.generation;
  assert(!x.batch.commit(x.res,x.mirror,x.generation,x.err)&&x.batch.active());++cases;}
 {Sim x;assert(x.begin({{1,0,0}}));x.advance(3);x.batch.copies_completed();auto* expected=x.mirror[1];x.mirror[1]=x.host[1].data();
  assert(!x.batch.commit(x.res,x.mirror,x.generation,x.err));assert(x.mirror[0]==nullptr&&x.res[0]==0);
  x.mirror[1]=expected;x.finish();x.publish();x.check();++cases;}
 {Sim x;assert(x.begin({{1,0,0}}));assert(!x.batch.commit(x.res,x.mirror,x.generation,x.err));
  int ticks=0;auto d=strata::failed_work::drain(1,[&](size_t){return x.dma.empty();},[](size_t){},[&]{return ticks>=5;},[&]{++ticks;x.advance(1);});
  assert(d.safe()&&x.dma.empty());x.finish();x.publish();x.check();++cases;}
 {Sim x;assert(x.begin({{1,0,0}}));int ticks=0;
  auto d=strata::failed_work::drain(1,[](size_t){return false;},[](size_t){},[&]{return ticks>=2;},[&]{++ticks;});
  assert(!d.safe()&&x.batch.active()&&!x.dma.empty()); // no freeing or reader admission on failed drain
  x.advance(3);x.finish();x.publish();x.check();++cases;}
 {Sim x;assert(x.begin({{1,0,0}}));x.advance(3);bool failed=false;
  auto d=strata::failed_work::drain(1,[](size_t){return true;},[&](size_t){failed=true;throw 1;},[]{return false;},[]{});
  assert(failed&&!d.safe()&&x.batch.active());++cases;}
 {Sim x;assert(x.begin({{1,0,0}}));x.advance(3);x.finish();x.publish();
  assert(!x.begin({{1,0,0}}));assert(x.begin({{0,1,0}}));x.advance(3);x.finish();x.publish();x.check();++cases;}
 {Sim x;std::vector<uint8_t*> m=x.mirror;std::vector<int32_t> r=x.res;Batch b;std::string e;
  assert(!b.prepare({{1,0,0}},0,r,m,0,e));m.pop_back();assert(!b.prepare({{1,0,0}},Sim::E,r,m,0,e));++cases;}
 std::cout<<"PASS: "<<cases<<" adaptive mirror ownership/DMA/failure cases; 1000 exchanges, T=1/4/6, MTP on/off\n";
}
