from pathlib import Path
s=Path('sycl/src/core/verify.cpp').read_text()
assert 'payload_rows = T * (uint64_t)(le_ - lb_)' in s
for member, width in [('h_x_', 'N'), ('h_ids_', 'K'), ('h_w_', 'K')]:
    assert f'mapped(payload_rows * {width} * 4, (void**) &{member}' in s
assert s.count('strata::verify_payload::row(l, lb_, max_t_, tb)')==2
assert 'h_x_ + payload_row * g.n_embd, h_ids_ + payload_row * ss.k' in s
assert 'm_x_ + tb * N' not in s and 'h_ids_ + (size_t) tb * ss.k' not in s
run=s.split('bool Verifier::run(',1)[1].split('void Verifier::set_plan_slot',1)[0]
assert run.index('copy_->wait_and_throw()') < run.index('failed_window.accepted = true')
assert 'released_.load()' in run and 'released_.store(true)' in run
assert run.index('pool(user, h_x_ + payload_row') < run.index('failed_window.accepted = true')
print('PASS: actual graph/host offsets match; graph/copy/host completion gates snapshot reuse')
