# Day 014: CUDA Occupancy Basics

Date: 2026-07-06

## Topic

CUDA occupancy, SM resource limits, and warp latency hiding.

## Goal

Understand how resident warps, registers, shared memory, and block scheduling affect occupancy and why higher occupancy is useful but not always sufficient for higher performance.

## 10 Concept Questions

### 1. SM and block scheduling

**Question:** In CUDA, what is an SM? After launching a kernel with many blocks, do all blocks run at once, or are they scheduled in batches onto SMs?

**Explanation:** An SM is a Streaming Multiprocessor. A GPU has multiple SMs, and blocks are scheduled onto SMs as execution resources become available.

**Correct Answer:** Blocks are scheduled in batches onto SMs. A block is assigned to one SM, and the SM executes its warps internally.

### 2. Occupancy definition

**Question:** What is CUDA occupancy? Intuitively, what resource usage on an SM does it describe?

**Explanation:** Occupancy describes how many active warps are resident on an SM compared with the architecture's maximum resident warp capacity.

**Correct Answer:** Occupancy is usually:

```text
occupancy = active warps per SM / maximum resident warps per SM
```

It describes how many warps are available on an SM to help hide latency.

### 3. Can a block span multiple SMs?

**Question:** Can one block be split across multiple SMs? For example, can part of a 256-thread block run on SM0 and the rest on SM1?

**Explanation:** A block is the basic unit of SM scheduling and resource allocation.

**Correct Answer:** No. One block is assigned to one SM. Its threads, warps, shared memory, and register allocation belong to that SM. This is what makes block-level synchronization and shared memory possible.

### 4. Warps per block and resident blocks

**Question:** Suppose one SM can have at most 64 resident warps. If a kernel uses 256 threads per block, how many warps does each block have? From the warp limit alone, how many such blocks can one SM hold?

**Explanation:** One warp usually contains 32 threads.

**Correct Answer:**

```text
warps per block = 256 / 32 = 8
max blocks from warp limit = 64 / 8 = 8
```

From the warp limit alone, one SM can hold at most 8 such blocks.

### 5. Resources that limit resident blocks

**Question:** Besides the maximum resident warp count, what resources can limit how many blocks can reside on one SM? Name at least two.

**Explanation:** Occupancy is constrained by several hardware limits at the same time.

**Correct Answer:** Common limits include:

- maximum resident blocks per SM
- maximum resident warps per SM
- registers per SM
- shared memory per SM
- threads per block

### 6. Register usage and occupancy

**Question:** If each thread in a kernel uses many registers, how does that affect occupancy? Why does a per-thread resource affect whether a whole block can reside on an SM?

**Explanation:** Registers are private to each thread, but a block's total register usage is the sum of all its threads' register requirements.

**Correct Answer:**

```text
block register usage = registers per thread * threads per block
```

If each thread uses many registers, each block consumes more of the SM's register file. When the SM cannot fit more blocks because registers are exhausted, resident blocks and active warps decrease, so occupancy can decrease.

### 7. Shared memory usage and occupancy

**Question:** If each block uses a lot of shared memory, how does that affect occupancy? How is this similar to and different from register limits?

**Explanation:** Shared memory is a limited per-SM resource. Each resident block reserves its own shared memory allocation.

**Correct Answer:** More shared memory per block can reduce the number of blocks that fit on an SM.

Registers and shared memory are similar because both are finite SM resources and both can limit resident blocks. They differ because registers are usually allocated per thread and then accumulate into a block-level total, while shared memory is allocated per block and shared by threads in that block.

### 8. Is higher occupancy always better?

**Question:** Is occupancy always better when it is higher? If occupancy increases from 50% to 100%, must performance improve?

**Explanation:** Occupancy is a means to expose enough ready warps, not a direct performance guarantee.

**Correct Answer:** No. Higher occupancy can help when the kernel needs more warps to hide latency, but performance may not improve if the bottleneck is elsewhere. Chasing higher occupancy can also hurt performance if it causes register spilling, smaller shared-memory tiles, worse memory access patterns, or poor block-size choices.

### 9. Occupancy and global memory latency

**Question:** If a kernel is global-memory-latency-bound, why can higher occupancy help? Explain using "warp waiting for memory" and "switching to another warp."

**Explanation:** When one warp waits for a global memory load, the SM can issue instructions from another ready warp instead of idling.

**Correct Answer:** Higher occupancy gives the SM more active warps. When some warps wait for global memory, the SM has a better chance of finding another ready warp to execute. This hides memory latency and can improve utilization.

### 10. Putting the concepts together

**Question:** Summarize the relationship between occupancy, registers, shared memory, and warp latency hiding.

**Explanation:** Occupancy is shaped by resource limits, and its value comes from giving the SM enough runnable warps.

**Correct Answer:** Registers and shared memory limit how many blocks and warps can reside on an SM. Occupancy measures active warps per SM relative to the hardware maximum. More active warps can help the SM switch to other ready warps when some warps wait for memory or instruction results, which hides latency. However, high occupancy does not guarantee high performance.

## Summary

Today covered:

- SMs as the hardware units that receive and execute blocks
- block scheduling onto SMs in batches
- block residency and why one block cannot span multiple SMs
- occupancy as active warps per SM relative to the maximum resident warps per SM
- register usage as a per-thread resource that accumulates into block-level pressure
- shared memory usage as a per-block resource that can limit resident blocks
- why high occupancy helps hide latency
- why maximum occupancy is not always the fastest configuration

## Common Mistakes

- Saying "stream multiprocessors" instead of the more precise "Streaming Multiprocessor."
- Treating the occupancy denominator as the current number of warps on an SM instead of the architecture's maximum resident warps per SM.
- Confusing maximum resident warp count with maximum resident block count.
- Thinking warps do not wait for memory; they can wait, and the SM hides that wait by scheduling other ready warps.
- Assuming higher occupancy always guarantees higher throughput.

## Next Step

Study CUDA block-size selection and occupancy calculator intuition: why block sizes such as 128, 256, and 512 are common, and how register usage, shared memory usage, and warp count shape occupancy.
