from pathlib import Path
s=Path('sycl/src/core/verify.cpp').read_text().split('bool Verifier::run(',1)[1]
assert s.index('gather_batch(')<s.index('ext_oneapi_graph(')<s.index('const bool no_host')
assert 'if (!ss.ple.table->gather_batch' in s
assert s.index('wait_and_throw()')<s.index('expert readiness device wait expired')
m=Path('sycl/src/core/mtp.cpp').read_text().split('bool MtpDrafter::draft(',1)[1].split('bool MtpDrafter::draft_first',1)[0]
assert m.count('wait_and_throw()')==2
assert m.index('wait_and_throw()')<m.index('drafts[0] =')
assert m.rindex('wait_and_throw()')<m.index('drafts[j] =')
assert 'ext_oneapi_empty() ? 0 : 1' in s
print('PASS: actual legacy PLE-before-graph, failure propagation, existing per-draft wait ordering and Boolean queue completion')

v=Path('sycl/src/core/verify.cpp').read_text().split('bool Verifier::run(',1)[1]
assert v.index('copy_->wait_and_throw()') < v.index('expert readiness device wait expired') < v.index('out[t] =')
print('PASS: timeout rejection follows copy-queue drain and precedes token consumption')
