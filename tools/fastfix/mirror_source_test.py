from pathlib import Path
s=Path('sycl/src/core/gguf_expert_source.cpp').read_text()
g=Path('sycl/src/program/generate.cpp').read_text()
assert 'adaptive_mirror::enqueue(exchange_' in s
assert s.index('exchange_event_.wait_and_throw()') < s.index('exchange_.copies_completed()') < s.index('exchange_.commit(') < s.index('cache.replace(')
assert 'GGUF mirror read during uncommitted adaptive exchange' in s
alias=s.split('const uint8_t* GgufExpertSource::device_alias',1)[1].split('bool GgufExpertSource::pcie_layer',1)[0]
assert 'layer_first_' not in alias and 'return nullptr' in alias
assert g.count('finish_gguf_exchange(); wait = true;')==2
assert g.count('gguf_src.exchange_async(batch, host_res, xcache, *adapt_stream, why)')==2
assert g.count('apply_pending(true);')>=4
assert 'mirror_table_h; // persistent' in g
assert 'drain_device_or_exit("GGUF mirror destruction")' in s
print('PASS: real serving/CLI exchange guards, exact aliases, completion-before-commit, safe destruction')

assert g.count('strata::drain_device_or_exit("adaptive worker exception")')==2
print('PASS: both adaptive workers propagate exceptions only after proven safe queue completion')
