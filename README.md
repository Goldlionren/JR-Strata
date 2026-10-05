<h1 align="center">JR-Strata</h1>

<p align="center">
<b>Heterogeneous LLM runtime research based on Strata</b><br>
Intel Arc · SYCL / Level Zero · VRAM + pinned RAM expert tiering · Vulkan next
</p>

<p align="center">
Current milestone: <b>Intel Arc Pro B60 running Swift 1.5 IQ3_XXS with 128K context configuration</b>
</p>

> [!IMPORTANT]
> JR-Strata is an independent experimental derivative of [Niko1221/Strata](https://github.com/Niko1221/Strata).
> The original Strata copyright and MIT License are retained.
> JR-Strata focuses on Intel GPU execution, heterogeneous memory, and future Vulkan backend development.

---

## Intel Arc milestone

The first JR-Strata milestone establishes a practical Intel Arc inference path on Linux using the existing Strata MoE runtime architecture.

### Validated system

| Component | Configuration |
| --- | --- |
| OS | Ubuntu 24.04 LTS |
| GPU | Intel Arc Pro B60 24 GB |
| GPU architecture | Battlemage / Xe2 / `bmg-g21` |
| Connection | PCIe 4.0 x4 via OCuLink |
| Measured H2D bandwidth | ~6.8 GB/s |
| System RAM | 64 GB |
| Compiler / runtime | Intel oneAPI DPC++ 2026.1 / Level Zero |
| Backend | SYCL |
| Model | Swift 1.5 / Qwen3.8-Flash-Next |
| Quantization | IQ3_XXS |
| Context configuration | 131072 tokens |
| KV cache | INT8 |
| Resident KV window | 32768 |
| Speculative decoding | MTP, `--spec 4` |

---

## Expert placement achieved

On the validated B60 system:

| Tier | Experts | Memory |
| --- | ---: | ---: |
| Arc Pro B60 VRAM | 10,617 | ~17.22 GiB |
| Pinned system RAM | 13,959 / 13,959 | ~22.75 GiB |
| Expert SSD fallback | **0** | **0** |

All experts that do not fit in VRAM remain resident in pinned system memory and are accessible to the GPU over PCIe.

PLE remains on NVMe by design.

The resulting execution hierarchy is:

```text
Swift IQ3_XXS
      |
      +---- hot experts ----------> Arc B60 VRAM
      |                              ~17.22 GiB
      |
      +---- remaining experts ----> pinned system RAM
                                     ~22.75 GiB
                                          |
                                      PCIe 4.0 x4

PLE / n-gram table --------------> NVMe
```

The goal is therefore:

```text
VRAM -> pinned RAM -> SSD only for PLE/storage
```

rather than using SSD as an active expert execution tier.

---

## Observed performance

Representative development observations on the validated B60 system:

- Decode: up to approximately **33.5 tok/s**
- Prefill: approximately **311 tok/s** in the observed workload
- VRAM expert hit rate: approximately **94%**
- PCIe host-to-device probe: approximately **6.8 GB/s**

These are development observations, not yet a controlled benchmark suite.

A fixed-prompt benchmark, `pcie_frac` sweep, CPU worker tuning, and real 120K–125K prompt test are planned before declaring a final SYCL performance baseline.

---

## JR-Strata changes

JR-Strata currently builds on upstream Strata v0.1.39 and adds/fixes the following areas.

### 1. Intel Arc Pro B60 support

Correct detection of the Arc Pro B60 PCI ID:

```text
8086:e211
```

The validated AOT target is:

```text
bmg-g21
```

### 2. SYCL API synchronization

The Intel/SYCL path was updated to match interface changes in the current Strata tree, including:

- thread-affinity handling
- native dense layer-range loading
- Intel setup/run-script argument synchronization

### 3. SYCL ring-wait correctness fix

JR-Strata includes the queue-state correction corresponding to the work discussed in upstream PR #866.

This fixes failures such as:

```text
verify: layer N never rang (graph finished)
```

where the translated SYCL queue state was previously not evaluated correctly.

### 4. Arc B60 uncached doorbell reads

JR-Strata includes the uncached L1/L3 read-hint approach corresponding to the work discussed in upstream PR #889.

On the tested B60 host-mirror path this was a major performance fix because the device could otherwise repeatedly observe a cached synchronization value while the CPU had already updated the host-side doorbell.

### 5. Chunked pinned-host expert mirror

The original host expert mirror attempted one very large allocation similar to:

```cpp
sycl::malloc_host(total_bytes)
```

For IQ3_XXS, the required host mirror can exceed 20 GiB after filling VRAM.

Even with sufficient total system RAM, a single extremely large Intel USM host allocation can fail.

JR-Strata replaces this with multiple pinned host blocks.

Conceptually:

```text
24+ GiB host expert complement

+---------+
| 4 GiB   |
+---------+
| 4 GiB   |
+---------+
| 4 GiB   |
+---------+
| 4 GiB   |
+---------+
| 4 GiB   |
+---------+
| ...     |
+---------+
```

Each expert retains its own device-readable host pointer.

This allows the complete non-VRAM IQ3_XXS expert set to remain resident in system RAM and eliminates expert SSD fallback when enough RAM is available.

---

## Current milestone commits

Upstream base:

```text
Strata v0.1.39
6f32ec0
```

JR-Strata milestone commits:

```text
0bac541  jr: establish Arc B60 SYCL IQ3_XXS baseline
18f7c3e  jr: chunk Intel SYCL host expert mirror
```

Milestone tag:

```text
jr-b60-sycl-iq3xxs-128k-20261006
```

---

## Intel Arc build

JR-Strata's current Intel path targets Linux.

Validated toolchain:

```text
Ubuntu 24.04 LTS
Intel oneAPI 2026.1
Intel Level Zero
CMake
Ninja
Docker
```

### Select the Intel GPU

Example for a system where the B60 is `level_zero:0`:

```bash
source /opt/intel/oneapi/setvars.sh

export ONEAPI_DEVICE_SELECTOR=level_zero:0
export SYCL_CACHE_PERSISTENT=0
```

Always verify your own device ordering:

```bash
sycl-ls --ignore-device-selectors
```

Do not assume that SYCL device indices are identical across machines.

### Build the B60 AOT binary

```bash
cmake \
  -S sycl \
  -B build-sycl-aot \
  -G Ninja \
  -DCMAKE_C_COMPILER=icx \
  -DCMAKE_CXX_COMPILER=icpx \
  -DCMAKE_BUILD_TYPE=Release \
  -DSTRATA_SYCL_AOT=bmg-g21 \
  -DSTRATA_SYCL_PARITY=ON

cmake --build build-sycl-aot \
  --target strata \
  -j"$(nproc)"
```

---

## Model setup

The validated model is:

```text
Swift 1.5
Qwen3.8-Flash-Next
IQ3_XXS
```

Example setup using already-downloaded GGUF shards:

```bash
./setup.sh \
  --backend sycl \
  --family swift \
  --model IQ3_XXS \
  --context 131072 \
  --kv int8 \
  --gpu 0 \
  --vision none \
  --data-dir /data/strata-lab/data \
  --models-dir /data/strata-lab/data/models \
  --gguf-dir /data/strata-lab/data/models/swift-IQ3_XXS \
  --yes \
  --no-start
```

Adjust paths for your own system.

The validated runtime uses settings equivalent to:

```text
--max-context 131072
--kv int8
--kv-resident 32768
--stream-experts
--spec 4
--spec-min-p 0.5
--prefill 4096
```

Current machine-specific tuning reached:

```text
--vram-reserve-mib 768
--pcie-frac 0.25
```

These two values are **not universal defaults**. They depend on GPU VRAM, CPU performance, PCIe bandwidth, and the model.

---

## Current status

### Working

- Intel Arc Pro B60
- SYCL / Level Zero
- Battlemage AOT build
- Swift 1.5 IQ3_XXS
- 128K configured context
- INT8 KV streaming
- MTP speculative decoding
- OpenAI-compatible serving path
- VRAM expert cache
- complete pinned-RAM expert complement
- PCIe access to host-resident experts
- zero expert SSD fallback on the validated 64 GB system

### Next

1. Controlled fixed-prompt `pcie_frac` benchmark.
2. CPU expert-pool worker tuning.
3. Real 120K–125K prompt benchmark.
4. Freeze the final Intel SYCL baseline.
5. Begin Vulkan backend development.
6. Later investigate heterogeneous Intel multi-GPU execution.

---

## Vulkan roadmap

The next major JR-Strata development line is Vulkan.

The goal is **not** to turn JR-Strata into a wrapper around another inference engine.

The target remains a Strata-style heterogeneous MoE runtime:

```text
model / router / MTP / KV / PLE
              |
        backend interface
         /           \
      SYCL          Vulkan
```

The Vulkan work will initially focus on:

- device discovery
- device/local buffer allocation
- host-visible or imported host memory
- asynchronous transfer and synchronization
- compute dispatch
- quantized GEMV / GEMM
- expert dispatch
- host expert execution over PCIe
- validation against the working SYCL implementation

Once a single-B60 Vulkan backend is stable, multi-GPU research can follow.

---

## Repository relationship

```text
Niko1221/Strata
      |
      | upstream base
      v
JR-Strata
      |
      +-- Intel SYCL stable line
      |
      +-- heterogeneous VRAM / RAM execution
      |
      `-- Vulkan backend research
```

JR-Strata is independently maintained and is not an official upstream Strata release.

Original project:

https://github.com/Niko1221/Strata

JR-Strata:

https://github.com/Goldlionren/JR-Strata

---

## Credits

JR-Strata is based on the work of:

- Niko1221 / Strata
- Strata contributors
- Intel Arc / SYCL community contributors

The Intel B60 work also incorporates ideas and fixes discussed in upstream Strata issues and pull requests, including the synchronization work associated with #866 and #889.

---

## License

MIT License.

The original Strata copyright notice and MIT License are retained in `LICENSE`.

Copyright (c) 2026 Niko1221 and the Strata contributors.
