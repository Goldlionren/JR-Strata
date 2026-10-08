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

f=Path('sycl/src/core/verify.cpp').read_text()
run=f.split('bool Verifier::run(',1)[1].split('void Verifier::set_plan_slot',1)[0]
assert run.index('FailureGuard failed_window') < run.index('ext_oneapi_graph(')
assert run.index('out[t] =') < run.index('failed_window.accepted = true')
assert 'FlagSet' not in f and 'host_task([publication]' in f
release=f.split('bool Verifier::release_gpu_waits',1)[1].split('void Verifier::trace_ev',1)[0]
assert 'UINT32_MAX' not in release and 'wait_and_throw()' in release
commit=f.split('bool Verifier::commit_finish',1)[1].split('bool Verifier::wait_commit',1)[0]
assert commit.index('wait_and_throw()') < commit.index('pending_commit_ = 0') < commit.index('ss_->ple_prev')
g=Path('sycl/src/program/generate.cpp').read_text()
assert 'if (test_no_draft) { T = 1; from_sfx = false; }' in g
assert 'const bool drafted = test_no_draft ||' in g
print('PASS: failure guards, immutable DMA publication, no fabricated readiness, completed commit history, explicit T=1 control')
