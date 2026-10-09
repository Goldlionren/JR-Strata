#!/usr/bin/env python3
"""Offline replay of immutable startup ranking and archived ownership publications."""
import collections
import hashlib
import json
import pathlib
import re
import struct
import sys

base = pathlib.Path(sys.argv[1])
evidence = base / 'logs/fastfix/mirror-repair-window-02'
profile = pathlib.Path('/data/strata-lab/Strata/data/expert-profile.bin')
raw = profile.read_bytes()
assert raw[:4] == b'STRP'
version, nl, ne, slots, count = struct.unpack_from('<5I', raw, 4)
assert (version, nl, ne, slots, count) == (1, 48, 512, 24576, 24576)
pairs = list(struct.iter_unpack('<HH', raw[24:24 + count * 4]))
assert len(set(pairs)) == count
nresident = 10831
res = [-1] * (nl * ne)
for slot, (layer, expert) in enumerate(pairs[:nresident]):
    res[layer * ne + expert] = slot
mirrored = {i for i, r in enumerate(res) if r < 0}
addresses = {}
owners = {}
log = (evidence / 'engine.log').read_text()
generation = 0
last_mirror = 0
last_upload = 0
batch_slots = set()
batch_experts = set()
swap_counts = collections.Counter()
layer_counts = collections.Counter()
evicted_initial_gpu_only = set()
initial_gpu_only = {i for i, r in enumerate(res) if r >= 0}
for line in log.splitlines():
    if line.startswith('APLAN_EXCHANGE '):
        m = re.fullmatch(r'APLAN_EXCHANGE generation=(\d+) phase=cpu_committed copies=complete layer=(\d+) in=(\d+) out=(\d+) slot=(\d+) host=(0x[0-9a-f]+)', line)
        assert m, line
        g, l, incoming, outgoing, slot = map(int, m.groups()[:5])
        address = int(m.group(6), 16)
        assert 0 <= l < nl and 0 <= incoming < ne and 0 <= outgoing < ne
        assert incoming != outgoing and 0 <= slot < nresident and address
        if g != generation:
            assert g == generation + 1 and last_upload == generation
            generation = g
            batch_slots.clear()
            batch_experts.clear()
        a, b = l * ne + incoming, l * ne + outgoing
        assert slot not in batch_slots and a not in batch_experts and b not in batch_experts
        batch_slots.add(slot)
        batch_experts.update((a, b))
        assert res[a] == -1 and a in mirrored and res[b] == slot and b not in mirrored
        if a in addresses:
            assert addresses[a] == address and owners[address] == a
        else:
            assert address not in owners, 'physical host pointer already has another known owner'
            addresses[a] = address
            owners[address] = a
        assert b not in addresses
        del addresses[a]
        addresses[b] = address
        owners[address] = b
        mirrored.remove(a)
        mirrored.add(b)
        res[a], res[b] = slot, -1
        swap_counts[g] += 1
        layer_counts[l] += 1
        if b in initial_gpu_only:
            evicted_initial_gpu_only.add(b)
    elif line.startswith('APLAN_MIRROR '):
        m = re.fullmatch(r'APLAN_MIRROR generation=(\d+) phase=mirror_uploaded entries=(\d+)', line)
        assert m and int(m.group(2)) == len(res)
        assert int(m.group(1)) == generation
        last_mirror = generation
    elif line.startswith('APLAN_RESIDENCY '):
        m = re.fullmatch(r'APLAN_RESIDENCY upload=(\d+) generation=(\d+) adapt_every=4 adapt_swaps=96 holes=0 first_layer=-1 first_expert=-1 hash=(\d+)', line)
        assert m, line
        upload, g, recorded_hash = map(int, m.groups())
        assert upload == last_upload + 1 and g == generation == last_mirror
        assert len(mirrored) == len(res) - nresident
        assert all((r < 0) == (i in mirrored) for i, r in enumerate(res))
        gpu_slots = [r for r in res if r >= 0]
        assert len(gpu_slots) == nresident and set(gpu_slots) == set(range(nresident))
        value = 2166136261
        for r in res:
            value = ((value ^ (r & 0xffffffff)) * 16777619) & 0xffffffff
        assert value == recorded_hash, (g, value, recorded_hash)
        assert all(i in mirrored and owners[a] == i for i, a in addresses.items())
        assert swap_counts[g] <= 96
        last_upload = upload
assert generation == last_upload == last_mirror == 251
assert sum(swap_counts.values()) == 14066
aplan = [line for line in log.splitlines() if line.startswith('APLAN_WINDOW ')]
# Successful-window diagnostics deliberately print only the first window; later failures would print.
assert not re.search(r'readiness timeout|device wait expired|UNSAFE|root!!!!!|!{5,}', log, re.I)
result = {
    'status': 'PASS', 'profile_sha256': hashlib.sha256(raw).hexdigest(),
    'initial_gpu_experts': nresident, 'mirrored_experts': len(mirrored),
    'pair_exchanges': sum(swap_counts.values()), 'committed_generations': generation,
    'max_pairs_in_generation': max(swap_counts.values()),
    'initial_gpu_only_experts_evicted': len(evicted_initial_gpu_only),
    'distinct_physical_host_addresses_observed': len(owners),
    'full_residency_hash_matches': last_upload,
    'publication_order': 'completed exchange -> mirror upload -> residency hash for each generation',
    'layer_exchange_counts': dict(sorted(layer_counts.items())),
    'limitations': [
        'Initial host addresses are learned on first logged exchange, not a readback of all 13745 aliases.',
        'CPU replay checks log consistency, not GPU byte integrity; the separate actual-source probe checks independent full-blob hashes on layers 0/32/46.',
        'Success diagnostics do not dump every verifier window; later progress is demonstrated by completed inference and metadata generations.'
    ]
}
responses = {}
for name in ['long-response', 'english', 'chinese', 'math']:
    row = json.loads((evidence / (name + '.json')).read_text())
    assert row['error'] is None
    assert not re.search(r'!{5,}|\ufffd', row['content'])
    responses[name] = {
        'prompt_tokens': row['usage']['prompt_tokens'],
        'generated_tokens': row['usage']['completion_tokens'],
        'finish_reason': row['finish_reason'], 'timings': row['timings'],
        'ttft_s': row['ttft_s'], 'elapsed_s': row['elapsed_s'],
        'sha256_utf8_content': hashlib.sha256(row['content'].encode()).hexdigest()
    }
long = json.loads((evidence / 'long-response.json').read_text())
assert long['usage']['completion_tokens'] == 2048 and long['finish_reason'] == 'length'
before, after = long['before'], long['after']
tail = next(s for s in long['samples'] if s['epoch'] >= before['epoch'] + long['ttft_s'] + 1)
samples = [before] + long['samples'] + [after]
all_samples = []
for name in responses:
    row = json.loads((evidence / (name + '.json')).read_text())
    all_samples.extend([row['before']] + row['samples'] + [row['after']])
def deltas(a, b):
    return {**{k: b['io'][k] - a['io'][k] for k in ['read_bytes', 'rchar', 'syscr']},
            **{k: b[k] - a[k] for k in ['majflt', 'pswpin', 'pswpout']},
            'duration_s': b['epoch'] - a['epoch']}
result['responses'] = responses
result['memory_io'] = {
    'long_request': deltas(before, after), 'post_prefill_conservative_tail': deltas(tail, after),
    'tail_start_epoch': tail['epoch'],
    'long_peak_vram_kib': max(s['vram_kib'] for s in samples),
    'long_peak_gtt_kib': max(s['gtt_kib'] for s in samples),
    'long_peak_rss_kib': max(s['VmRSS_kib'] for s in samples),
    'long_min_available_kib': min(s['host_available_kib'] for s in samples),
    'all_requests_peak_vram_kib': max(s['vram_kib'] for s in all_samples),
    'all_requests_peak_gtt_kib': max(s['gtt_kib'] for s in all_samples),
    'all_requests_peak_rss_kib': max(s['VmRSS_kib'] for s in all_samples),
    'all_requests_min_available_kib': min(s['host_available_kib'] for s in all_samples),
    'engine_max_swap_kib': max(s['VmSwap_kib'] for s in all_samples),
    'caveat': 'Process IO includes PLE/other reads; global swap is not attributable to the engine. DRM GTT and RSS overlap and must not be summed.'
}
out = evidence / 'offline-analysis.json'
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
