#include <initializer_list>
#include "strata/core/fastfix_output.hpp"
#include <cassert>
#include <limits>
#include <cstdio>
int main() {
 using strata::core::valid_draft_result;
 assert(valid_draft_result(0,0,100)); assert(valid_draft_result(99,1,100));
 assert(!valid_draft_result(-1,.5,100)); assert(!valid_draft_result(100,.5,100));
 for(float p : {-1.f,1.001f,std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::infinity()}) assert(!valid_draft_result(1,p,100));
 puts("PASS: MTP completed-output bounds and nonfinite rejection (CPU; not GPU synchronization proof)");
}
