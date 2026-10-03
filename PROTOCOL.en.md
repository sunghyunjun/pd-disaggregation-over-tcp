> This is an English translation, made after the study, of `PROTOCOL.md`, the Korean protocol v1.7 that was committed before the first measurement round (private commit 7e4ce5b; see the technical report, Appendix D). The Korean file is the pre-registered document; where the two differ, the Korean file governs. Internal round codes (A, B, D, E1–E9, P) are those used in the data folders and the appendices of the report.

<!-- PROTOCOL.md: pre-registration. Generated from docs/protocol.html (v1.7, 2026-09-24). The HTML is canonical for layout; this file is the git-tracked text. -->

PD Disaggregation Experiment Protocol

- 

- 

- 

research/pd-without-rdma Experiment protocol v1.7 2026-09-21 Companion to the plan document (v1.1)

# PD Disaggregation Experiment Protocol

The plan document says "what we do and when"; this document says "which claim we prove with which comparison." Each claim of the final article gets an experiment, a control group, a treatment group, a pass criterion, and a figure. Publication is a Zenodo DOI and a technical blog; arXiv is not a target.

 What the article must answer

For a team that finds it hard to buy or rent H- or B-class hardware for long, if they run PD disaggregation on the g5, g6, and g7 instances that are already easy to use on demand and accept the slow network, does goodput per dollar rise over serving without PD? If it rises, how far does it fall short of an H100 NVLink cluster? How does that answer change with the workload and with the model's KV size?
 For teams that can't buy or reliably rent H/B-class clusters: does PD disaggregation on readily available g5/g6/g7 instances, over slow TCP, raise goodput per dollar over colocated serving, and how far does it fall short of an H100 NVLink reference?

↑ Contents 01 Claims

## One headline claim and seven supporting claims

C0 is the article's first number, and C1 to C7 explain why that number comes out as it does. The article is structured to prove these sentences in order. If an experimental result contradicts a sentence, we fix the sentence, not the experiment. The interpretation of an opposite result is written in advance in the last line of each experiment in §03.

C0
On an on-demand g5/g6/g7 fleet, PD disaggregation [raises / does not raise] goodput per dollar relative to the baseline without PD, and reaches only [x]% of the H100 NVLink reference point. Supported load ÷ hourly price. B2 and P1 per generation, R0 and R1 as reference points. Measurement fills the brackets. → E0, F0

C1
The cost of mixed serving is in the tail, not in the average. On a single chunked-prefill instance, as load rises, TBT p99 breaks much earlier and much harder than mean TPOT. The larger the chunk, the worse. → E1, F1

C2
At the same GPU count, PD over a slow network does not beat the baseline on a chat workload, or beats it only narrowly. Two replicas versus 1P+1D, ShareGPT, 5 Gbps single flow. → E2, F2

C3
The break-even is a function of input length, and output length pushes that boundary to the right. PD wins only when the input fits within the transfer budget (TTFT SLO × bandwidth) and the output is long enough. → E3, F3

C4
As bandwidth rises the boundary moves proportionally, but the single-flow cap arrives before the instance spec does. N0 → N1 and the tc sweep. A "50 Gbps instance" actually moves KV at 5 Gbps. → E4, F4

C5
Slow transfer blocks the prefill GPU on memory first. Blocks waiting for transfer occupy prefill KV, so the prefill GPU cannot accept new requests even though it has compute left. This is the mechanism by which PD loses. → E5, F5

C6
The faster the GPU, the narrower PD's window. On Blackwell, prefill gets shorter and transfer takes a larger share. → E6, F6

C7
The smaller a model's KV bytes/token, the further right the break-even of slow-network PD moves. Model choice partly substitutes for a network upgrade. At the same input length, transferred bytes differ by more than 2× across models. GQA head count, layer count, hybrid attention, KV fp8. → E7, F7

↑ Contents 02 Factors

## Seven factors we move, nine conditions we fix

| Factor | Levels | Moved in which experiment | Elsewhere | 

| Serving configuration | B1 · B2 · P1 · (B3 · 1P2D · 2P1D) | All | — | 

| Request rate | 6 to 8 steps, Poisson | All (sweep axis) | — | 

| Input length | 1K · 4K · 16K · 32K | E3, E4, E6 | ShareGPT distribution as is | 

| Output length | 128 · 512 | E3, E6 | ShareGPT distribution as is | 

| Network | Effective bandwidth (measured with iperf). tc sweep {1, 2.5, 5} Gbps + 10 in a placement group. ENA Express is not supported on the target types (9/24) | E4 | N0, measured value recorded. Equalized across generations with tc | 

| GPU generation | RTX PRO 4500 (g7, 32 GB) · RTX PRO 6000 (g7e, 96 GB) · optional: L40S (g6e) · A10G (g5, lower reference) | E6·E7 | g7 | 

| Model · KV | Gemma 4 31B (320 KB/tok) · Qwen3-8B (144) · Gemma 4 26B-A4B (80) · Qwen3.8-27B (64) · Qwen3.6-35B-A3B (20) · KV fp8 (÷2) | E7 | Main model Gemma 4 26B-A4B NVFP4, anchor Qwen3-8B BF16 | 

| Precision | BF16 · FP8 · NVFP4 (same model on the same GPU is possible only on g7e) | E7 | g7e BF16 / g7 NVFP4 | 

| Interconnect reference | Same-node PCIe (R0) · same-node NVLink H100 (R1) | E0 | Inter-node TCP | 

| Chunk size | 2048 · 8192 | E1 | 2048 | 

### Fixed conditions

- Same AZ (us-east-1b), same subnet, same AMI, same vLLM commit and flags. A snapshot in every result file.

- The main model is Gemma 4 26B-A4B NVFP4, the anchor is Qwen3-8B BF16. The model and precision matrix is in the plan document §06b.

- prefix caching: off for synthetic sweeps, on for traces. Identical in both configurations.

- Proxy: both configurations go through the same proxy process. B2 is round-robin, P1 is P→D.

- Same KV block size, max-model-len (32K), gpu-memory-utilization (0.90).

- Same max-num-seqs on the decode side. That the P1 decoder can accept more concurrent requests than a B2 replica is a legitimate gain of PD, so it is not artificially matched, but the value is reported.

- Measurement starts after a warm-up of 30 requests. 3 minutes per point. Sweeps go from the lowest request rate upward.

- On-demand only. If there is a spot interruption log, that point is discarded.

- If the iperf3 single-flow and 4-flow values right before measurement deviate more than 20% from the expected bandwidth of that setting, re-measure.

- The client (bench serve) and the proxy run on a separate CPU instance (c6i.2xlarge) in every round. g7e.2xlarge has 8 vCPUs, so running them on the GPU node would change the client condition per generation. Client CPU utilization is recorded.

- Network is reported as the effective value (iperf single-flow and 4-flow), not the nominal bandwidth. Each family's bandwidth scales with vCPUs, so the nominal value at the one-GPU size differs as 10/20/50 Gbps, but if the single-flow cap (5/10/25) is the real bottleneck the condition is the same. If it differs, equalize with tc.

↑ Contents 03 Experiments

## One headline experiment, two reference experiments, eight main experiments. Control in blue, treatment in orange

E0
### Goodput-per-dollar ladder (headline)
C0 · F0 · No separate run; computed from E2, E3, E6, R0, R1

Control
Serving without PD: B2-g5, B2-g7.2xlarge (2 GPUs each), and B2-H100 from R1.

Treatment
P1-g5 (N0, N1), P1-g7.2xlarge (N0, N1), P1-same-node from R0, P1-NVLink from R1.

Metric
Output tokens/s that meet the SLO ÷ on-demand price per hour = tokens per dollar. Its reciprocal is dollars per 1M output tokens. Each of the two SLOs. Two workloads, ShareGPT and synthetic 4K/512.

Prices
us-east-1 on-demand, stated as of the measurement date. R1 uses that cloud's price. The AWS p5 price is listed alongside in the table (with whether it could be launched).

Pass criterion
Passes whichever way the result goes. What is reported is the order of the ladder, what percentage each P1 is of the same-generation B2, and what percentage it is of the H100 reference point.

Side record
On the experiment day, attempt one on-demand launch of AWS p5.48xlarge and record the result (success / insufficient capacity / quota). This is the evidence for "hard to rent."

Expectation: per dollar, g7e-B2 is highest, g5-P1 is similar to or below g5-B2, and H100-NVLink-P1 has overwhelming absolute goodput but the same order of magnitude per dollar as g7e. If the opposite comes out (g5-P1 is highest per dollar): PD with several cheap GPUs really is the cost-effective answer, and C0 is confirmed positive.

R0
### Reference: same GPU, no network
Reference point for E0 · Round B · one g5.12xlarge

Control
B2: 2 independent instances on 2 A10Gs in the same node.

Treatment
P1: 2 A10Gs in the same node, NixlConnector local transfer (cuda_ipc or PCIe). Not inter-node TCP.

Fixed
Only 2 GPUs used on one g5.12xlarge (A10G ×4, PCIe, no NVLink). Qwen3-8B, chunk 2048, ShareGPT + synthetic 4K/16K/32K × 512.

Measurement
Same metrics as E2 and E3. Transfer time (over PCIe) and the P1/B2 ratio.

What this isolates
The difference between P1 in round B (inter-node TCP) and P1 in R0 (same node) is the network penalty itself. If P1/B2 in R0 does not exceed 1, the problem is not the network but the PD mechanism or the GPU size.

Cost
$5.67/h × 1.5h ≈ $9. Right after round B on the same Saturday, or separately on a weekday evening.

Expectation: P1 in R0 transfers in under 1 second even at 32K, so the break-even moves far to the right. The gap to round B is the "value of the slow network."

R1
### Reference: H100 ×2, NVLink
Upper bound for E0 · After round D · Another cloud or the literature

Control
B2: 2 independent instances on 2 H100s.

Treatment
P1: 2 H100s, NixlConnector over NVLink (same node).

Fixed
Same vLLM commit, same workload and SLO definitions (the TBT multiple re-fixed on the H100 single step). Qwen3-8B BF16. ShareGPT + synthetic 4K/16K/32K × 512.

Where
AWS p5.48xlarge is unrealistic because of the P-family quota of 192 vCPUs and capacity problems (the attempt is recorded). 2h on a cloud that sells 2×H100 NVLink by the hour (about $3/GPU/h, price to be confirmed). If even that is hard, cite H100 numbers from DistServe, Splitwise, and the vLLM/Dynamo blog, marked "literature" in the ladder.

Caution
Intra-node NVLink is faster than inter-node RDMA. So R1 is not "an RDMA cluster" but its upper bound. The article says so.

Cost
About $12 to $20.

Report: both absolute goodput and goodput per dollar. "H100 is N times faster than g7e but M times per dollar" is the second clause of C0.

E1
### Tail interference in mixed serving
C1 · F1 · Round A

Control
B1, chunk 2048, request-rate sweep. The baseline curve.

Treatment
B1, chunk 8192, same sweep. Expectation: the larger the chunk, the more prefill tokens intrude into decode steps, and the longer the TBT tail.

Fixed
One g7.2xlarge, Gemma 4 26B-A4B NVFP4 (main) + Qwen3-8B BF16 (anchor), ShareGPT, prefix caching on.

Measurement
Per request rate: TTFT p90, TBT p99, mean TPOT, within-request TBT max/median ratio. SLO attainment.

Pass criterion
The request rate at which TBT p99 breaks the SLO is lower than the request rate at which mean TPOT rises by the same multiple. That point for chunk 8192 is lower than for 2048.

Repeats
Each point once; only the 2 knee points of the curve are repeated twice and the median taken.

If the opposite comes out: if TBT p99 and TPOT break together, vLLM's chunk scheduler already hides the interference well, and that is a strong result that PD's gain itself is small. C1 is lowered to about "interference is sensitive to chunk size."

E2
### Head to head at the same GPU count
C2 · F2 · Round B

Control
B2. Independent instances on 2 nodes, round-robin proxy.

Treatment
P1. Node A prefill, node B decode, NixlConnector UCX/TCP, N0.

Fixed
2 g7.2xlarge + c6i client, Gemma 4 26B-A4B NVFP4 (main) + Qwen3-8B BF16 (anchor), chunk 2048, ShareGPT + Azure-conv, prefix caching on. Same proxy process.

Measurement
Per request rate: goodput (chat, document), supported load (attainment 90%), TTFT p90, TBT p99. For P1, add KV bytes per request and transfer time.

Pass criterion
Passes whichever way the result goes. The numbers to report are the supported-load ratio P1/B2, and how much TBT p99 improved against how much TTFT p90 worsened.

Pre-check
On B2, throughput difference with and without the proxy within 5%. If it exceeds that, change the proxy and redo.

Expectation: on ShareGPT (short inputs), P1's TBT is stable and TTFT grows by the transfer time, so chat supported load is 0.7 to 1.1 times B2. If the opposite comes out (P1 wins by a large margin): one decoder holds a larger batch stably than two replicas. Report the decoder's concurrent request count and KV occupancy together, and reverse C2.

E3
### Break-even grid
C3 · F3 · Rounds B and C

Control
B2, synthetic requests with fixed (input L, output O), request-rate sweep.

Treatment
P1, same grid. L ∈ {1K, 4K, 16K, 32K}, O ∈ {128, 512}.

Fixed
2 g7.2xlarge, Gemma 4 26B-A4B NVFP4, N0, prefix caching off, ignore_eos.

Measurement
Per grid cell, the supported-load ratio P1/B2 (both SLOs). Predicted transfer time (KV bytes / iperf bandwidth) compared with the measurement.

Pass criterion
The boundary between cells where the ratio exceeds 1 and cells where it does not is monotone along the L axis. The boundary L is larger at O=512 than at O=128.

Repeats
8 cells × 4 request-rate points = 32 runs. The 2 cells straddling the boundary are run twice.

Expectation: under the chat SLO the boundary is near 4K, under the document SLO near 16K. At 32K, P1 loses under both SLOs (transfer 6 to 7 seconds). If the opposite comes out (no boundary, loses everywhere): even on A10G, transfer is always longer than prefill, and C3 changes to "on A10G + 5 Gbps no break-even exists." That too is a valid result.

E4
### Bandwidth axis
C4 · F4 · Round C

Control
P1 at N0 (reusing E3's results).

Treatment
P1 with the bandwidth fixed by sender-side tc at 4 points: {1, 2.5, 5} Gbps (N0), 10 (inside an N1 placement group). Only L ∈ {4K, 16K, 32K}, O=512 from the E3 grid. The N1 value without tc is a validation point. There is no 25 Gbps point because ENA Express is not supported.

Fixed
Same two instance types, same software. At each point, record iperf3 single-flow and 4-flow first to confirm that tc actually took effect. The axis is measured Gbps, not nominal.

Measurement
Measured transfer time per setting, supported-load ratio, shift of the boundary L.

Pass criterion
Transfer time is inversely proportional to iperf bandwidth. The boundary L shifts approximately in proportion to the bandwidth ratio.

Auxiliary measurement
Confirm whether UCX TCP is a single connection from the difference between 4-flow iperf and the measured transfer. If a multi-stream option exists, add one point.

Expectation: measured near N0 5 → N1 10 Gbps, and the boundary L moves from about 4K to about 8K. If the opposite comes out (still 5 Gbps at N1): UCX is tied to a single flow and the placement group cannot raise the per-flow cap. That in itself is one vLLM/NIXL issue, and C4 changes to "the cap is the transfer library's flow count, not the instance spec."

E5
### Transfer-wait occupancy of the prefill GPU
C5 · F5 · Rounds B and C (collected in the same runs as E2 and E3)

Control
KV occupancy and queue time series from one B2 instance. Same request rate.

Treatment
On the P1 prefill node: KV occupancy, number of blocks waiting for transfer (connector metric or log), queue length, GPU utilization time series.

Fixed
No separate run. Uses the Prometheus scrape (1 second) and dmon from E2 and E3 as they are.

Measurement
The request rate at which "low GPU utilization + high KV occupancy + growing queue" appear together on the prefill node. The relation between that request rate and P1's supported-load ceiling.

Pass criterion
At the request rate where P1 starts breaking the SLO, prefill GPU utilization is below 50% and KV occupancy is 90% or above.

Caution
If vLLM does not expose the number of blocks waiting for transfer directly, compute "time from request completion to block release" from the logs. If that is unavailable, it is a candidate for a metrics PR.

If the opposite comes out (prefill GPU is compute-saturated): the bottleneck is compute, not memory, and in that case P1's limit is simply the throughput of one prefill node. Delete C5 and use it as the motivation for E8 (2P1D).

E6
### GPU generation axis
C6 · F6 · Round D

Control
The g7 (RTX PRO 4500) results from E2 and E3.

Treatment
E2 + the E3 grid with the same models (26B-A4B NVFP4, Qwen3-8B BF16) on 2 g7e.2xlarge (96 GB). Optional: g6e (L40S), g5 (A10G, lower reference).

Fixed
Same models and precision, chunk 2048, same proxy and flags, same client instance. The network is equalized with tc so the measured effective value matches the g7 pair (the nominal 40/50 Gbps is not used). The TBT multiple of the SLO is re-fixed in ms by re-measuring the single-step time on each GPU.

Measurement
Per generation: prefill time (32K), transfer time, boundary L. Transfer/prefill ratio.

Pass criterion
At the same effective bandwidth, the faster the GPU (4500 → 6000), the smaller the boundary L. Partial recovery at N1.

Report
The F3 grids of the two generations side by side. The key point is that absolute goodput is higher on g7e but the ratio P1/B2 is lower.

If the opposite comes out (the window widens on g7e): either the 50 Gbps baseline survives to some degree even on a single flow, or the Blackwell decoder's batching gain is large. Separate the two with the iperf value and the decoder's concurrent request count, and report.

E7
### Quantization axis and KV size axis (Gemma first)
C7 · F7 · Round C (g7e ×2)

Control
g7e · Gemma 4 26B-A4B BF16 · N0 (the unquantized baseline on the same GPU).

Treatment
(a) Quantization axis: 26B-A4B NVFP4 / FP8, 31B BF16 / NVFP4 / FP8, same GPU, same model. (b) KV size axis: Gemma 4 31B 320 KB/tok, Qwen3-8B 144, Gemma 4 26B-A4B 80, Qwen3.8-27B 64, Qwen3.6-35B-A3B 20. (c) KV fp8 on/off halves both (a) and (b).

Fixed
2 g7e.2xlarge (96 GB, so 31B and 35B-A3B fit in BF16), N0, L ∈ {4K, 16K, 32K}, O=512. The numbers are computed from config.json and verified against bytes per block in the vLLM log at startup. Matrix in the plan document §06b.

Measurement
KV bytes per request, transfer time, boundary L. Quality is out of scope (not measured, stated explicitly).

Pass criterion
Transfer time is proportional to KV bytes/token × L, and the boundary L shifts inversely with bytes/token. Compute-speed differences between models (MoE active parameters) are reported separately as prefill time.

Caution
First confirm whether NixlConnector moves Gemma 4's sliding-layer KV and the recurrent state of Qwen3.5+ linear attention (Gated DeltaNet). Models where it does not are left as issues and excluded. Workload-side differences in KV size (multi-turn prefix repetition) are handled by the Mooncake trace.

If the opposite comes out (time does not fall when bytes fall): transfer is bound by round-trip and handshake latency, not bandwidth. Separating out the fixed cost per request and reporting it makes this an even more useful result.

E8
### P:D ratio (optional)
Auxiliary · F8 · Round C, if 3 nodes are approved

Control
B3. 3 replicas, round-robin.

Treatment
1P2D and 2P1D. The proxy must support multiple decoders.

Fixed
3 g5.4xlarge, Qwen3-8B, N0. Workloads ShareGPT (decode-heavy) and LongBench (prefill-heavy).

Measurement
Supported-load ratio against B3. Prefill node KV occupancy (linked to E5).

Pass criterion
1P2D on ShareGPT and 2P1D on LongBench each beat the 1P1D ratio. If 2P1D is more favorable than expected on the slow network, that is evidence that the E5 mechanism also acts on the ratio.

Cost
$4.87 per hour, about $20 for 4h. Quota 48 vCPUs.

If the opposite comes out: if the ratio does not change the result, this experiment is moved to an appendix and the body says "1:1 was enough" in one line.

↑ Contents 04 Measurement Protocol

## The order for measuring one point. Every run follows the same order

- Environment snapshot: instance ID, type, AZ, AMI, vLLM commit and flags, NIXL and UCX versions, network setting code (N0/N1, tc value), iperf3 single-flow and 4-flow (both directions), single-step time. As the env block of the results JSON.

- Start-up check: one request through the proxy completes end to end. For P1, confirm the KV transfer completion string in the log.

- Warm-up: 30 requests of the same workload, results discarded.

- Main measurement: bench serve, request rate r, number of requests = max(100, 180·r), Poisson, fixed seed, --save-detailed. At the same time, Prometheus 1-second scrape, dmon 1 second, sar 1 second to files.

- The per-request TBT statistic for the verdict is max (corrected 9/24). A single 350 ms stall inside a 500-token answer is not caught by the request's p99 (0.2%), yet it is exactly the stutter the user sees. The system TBT p99 (all tokens, the Sarathi and Splitwise convention) is listed alongside for comparison, and the fraction of stalled requests (max/median > 5) is also reported.

- Clean-up: before the next request rate, confirm that the queue is empty (Prometheus running and waiting are 0), then rest 30 seconds.

- Discard conditions: spot interruption, client CPU above 90%, iperf deviation above 20%, request failure rate above 1%. Discarded runs keep their files and are marked discarded: true.

### Aggregation is rebuilt with the SLO stated explicitly

`results/all_runs.csv` is built **always with the SLO passed as an argument**. The defaults in `aggregate.py` are chat TBT 100 ms and document 400 ms, but this study's thresholds are 50 ms and 250 ms. A CSV built with the defaults has all its attainment and goodput columns too loose (this actually went wrong once on 2026-09-27).

    python3 harness/aggregate.py results -o results/all_runs.csv \
      --slo chat=ttft:1000,tbt:50 --slo doc=ttft:3000,tbt:250

When the ladder was measured with `vllm bench sweep serve`, convert first.

    python3 harness/sweep_to_runs.py results/sweep/<experiment-name> --stage E5 --config P1tuned --workload sharegpt

### The shape of one results JSON file

{
 "run_id": "2026-10-04_B_P1_N0_sharegpt_r2.0",
 "stage": "B", "config": "P1", "network": "N0",
 "workload": {"name": "sharegpt", "input_len": null, "output_len": null, "prefix_caching": true},
 "load": {"request_rate": 2.0, "num_prompts": 360, "burstiness": 1.0, "seed": 0},
 "env": {"instances": [...], "vllm_commit": "...", "flags": [...], "iperf": {"p1_gbps": 4.9, "p4_gbps": 9.6}, "single_step_ms": 21.3},
 "bench": { ...vllm bench serve output as is... },
 "requests": [{"ttft_ms": ..., "itl_ms": [...], "e2e_ms": ..., "in_tok": ..., "out_tok": ...}, ...],
 "derived": {"tbt_p99_ms": ..., "goodput_chat": ..., "goodput_doc": ..., "attain_chat": 0.93},
 "transfer": {"bytes_per_req_mean": ..., "xfer_ms_p50": ..., "xfer_ms_p90": ...},
 "timeseries": {"prom": "prom_.jsonl", "dmon": "...", "sar": "..."},
 "discarded": false
}

↑ Contents 05 Reporting Rules

## We decide first how to write the numbers

- Latency as p50, p90, and p99 together. The mean only for TPOT, and only as a supplement.

- goodput for each of the two SLOs. "Supported load" is the last request rate at which attainment exceeds 90%, and the uncertainty from the sweep spacing (up to the next request rate) is written alongside.

- The ratio P1/B2 is the ratio of supported loads. Above and below 1.0 in color. 0.9 to 1.1 is read as "equal" and is not written as a win or a loss.

- Confidence intervals by request-level bootstrap (1000 times) on p99 and goodput. No p-values. Repeated runs take the median.

- Transfer time as prediction (bytes / iperf bandwidth) and measurement side by side. The difference is the fixed cost (handshake).

- Cost as dollars per 1M output tokens at the supported load. On-demand price stated, date stated.

- Every figure is regenerated from results/ with one script run. No hand-edited figures.

↑ Contents 06 Figures

## Nine figures and two tables. The skeleton of the article

F0
Goodput-per-dollar ladder. Horizontal bars. SLO tokens per dollar per configuration (B2-g5, P1-g5 N0, P1-g5 N1, R0, B2-g7, P1-g7 N0, P1-g7 N1, B2-H100, P1-H100, literature RDMA). Two SLO panels. Small bars of absolute goodput beside it. The article's first figure. E0.

F1
Interference: request rate versus TBT p99 and mean TPOT, two chunk values. Horizontal axis request rate, vertical axis ms (log). 4 lines. Horizontal SLO line. The figure for C1. E1.

F2
Head to head: request rate versus goodput, B2 and P1, two SLOs. 2 panels (chat, document). Supported load as a vertical dotted line. Bootstrap bands. E2.

F3
Break-even grid: input length × output length → P1/B2 ratio. 4×2 heatmap, numbers in the cells. The two SLOs stacked. The boundary line in bold. The article's representative figure. E3.

F4
Bandwidth axis: transfer time and boundary shift per network setting. Left: iperf bandwidth versus measured transfer time (prediction line overlaid); right: the F3 boundary line per tc value (1/2.5/5/10 Gbps). E4.

F5
Mechanism: prefill node time series. At one request rate, time versus GPU utilization, KV occupancy, queue length. B2 instance and P1 prefill stacked. E5.

F6
Generation axis: F3 for A10G and RTX PRO 6000 side by side. Same color scale. The boundary moving left is visible at a glance. Transfer/prefill ratio bars below. E6.

F7
KV size: bytes per request versus transfer time and boundary L, points for 4 models and per precision. Qwen3-8B, Llama-3.1-8B, Qwen3-30B-A3B, Gemma 4, KV fp8. The intercept of the regression line is the fixed cost. The right panel is bytes/token versus boundary L. E7.

F8
(Optional) Ratio: B3 versus 1P2D versus 2P1D, 2 workloads. 6 bars. E8.

T1
Experiment environment table. Instances, GPUs, network baseline and measured values, vLLM version, models, prices and dates.

T2
Results summary table. Experiment × (expectation, result, pass or fail, figure). The pass criteria of §03 filled in as they are. The article's last section.

↑ Contents 07 Threats to Validity

## Limits the article writes down for itself first

| Threat | How we reduce it | Remaining limit (stated in the article) | 

| Proxy overhead | Both configurations go through the same proxy. Difference with and without it on B2 confirmed within 5% | The toy proxy is not a production router. No routing intelligence (prefix-aware) | 

| Burst credits | Only instances with baseline bandwidth of 10 Gbps or more. iperf before and after measurement | g5.4xlarge is still an "up to" type. Credits may run out in long runs | 

| Nominal bandwidth differences across generations | Reported as the effective value (iperf), equalized with tc | tc is sender-side shaping, so it does not make the latency characteristics identical. Round-trip latency recorded separately (ping) | 

| Single-flow cap | Made an explicit axis with N0/N1 and tc. ENA Express is not supported on the target types | If UCX's flow count cannot be changed, the cap may belong to the library, not AWS | 

| 1:1 ratio only | Partly supplemented by E8 | xP:yD optimization is out of scope. Conclusions limited to the two points 1:1 and 3 nodes | 

| Model size | 8B dense fixed as the main model | At 70B-class TP serving the prefill-to-transfer ratio differs. No generalization claimed | 

| SLO choice | Two sets, literature definition (Sarathi) cited | A different SLO moves the boundary. F3 is drawn once more as a function of the SLO multiple (appendix) | 

| Trace tokenizer | Only token counts are replayed, prompts are generated | Differs from the real text distribution. Prefix repetition reproduced only via Mooncake hash_ids | 

| No RDMA comparison point | Stated as out of scope | "How much better with RDMA" is not answered by this article. Literature numbers cited only | 

| Price changes | On-demand prices on the measurement date fixed in the table, formula published | Per-dollar numbers change when prices change. Also reported as ratios (same-day prices) | 

| Representativeness of the H100 reference point | Intra-node NVLink stated as the "upper bound", inter-node RDMA cited from the literature | Not a real RDMA cluster number. The other cloud's prices differ from AWS | 

| Few repeats | Only boundary cells twice, bootstrap bands | Budget constraint. Reproduction left to the public raw data | 

| Experimenter bias | Hypotheses, pass criteria, and opposite interpretations fixed in this document before measurement | The date of this document serves as pre-registration. It can be uploaded to Zenodo first as v1 | 

↑ Contents 08 Reproduction and Publication

## Zenodo DOI and blog. arXiv is not a target

The canonical text is the Markdown in the public repository, and the blog post is a copy of the same content. Readers are vLLM operators, so Markdown with figures, tables, and reproduction commands reads better than a PDF. A PDF can be built from the same Markdown and attached to a new version when Google Scholar exposure becomes necessary, and ORCID can be created later and linked back to the existing DOI through DataCite search, so it is deferred for now.

#### Repository structure

pd-without-rdma/
 README.md results summary + figures + DOI
 CITATION.cff Sunghyun Jun (ORCID later)
 LICENSE code Apache-2.0, text and figures CC-BY-4.0
 infra/ Terraform, AMI scripts
 harness/ run_bench.sh, convert_*.py, analyze.py
 configs/ vllm serve flags per configuration (B1/B2/P1, N0/N1, tc)
 results/ all run_id.json (including discarded)
 figures/ generation scripts for F1 to F8 and PNG/SVG
 writeup/ article manuscript (md). PDF optional
 PROTOCOL.md the md version of this document

#### Publication order

- Pre-registration: before measurement starts, put PROTOCOL.md into the local repository as its first commit. Publication comes later, but the first commit is kept unsquashed to preserve its date.

- Measurement and analysis: commit results and figures at each round.

- Article: written directly as md in writeup/ (from ARTICLE.md). English body, Korean translation.

- Zenodo: connect the repository to Zenodo, GitHub release v1.0 → automatic archive → DOI. The record description carries a results summary and the blog link. PDF optional.

- Blog: the same article posted to sunghyunjun.github.io, DOI on the first line. Korean edition together.

- Distribution: vLLM Slack, LMCache Slack, GPU MODE Discord, r/LocalLLaMA, HN, LinkedIn. With links to issues and PRs.

- Publication: once code and results are tidy, squash the intermediate commits into logical units and push to GitHub.

- Revision: if additional measurements come, release v1.1 → new version DOI. The concept DOI is kept.

### Zenodo metadata draft

Title
PD Disaggregation Without RDMA: Break-even Measurements on AWS GPU Instances

Type
Software (default with the GitHub integration). When a PDF is attached, a separate Publication / Technical report record

Author
Jun, Sunghyun. Affiliation "Independent". ORCID deferred

Keywords
LLM serving; prefill-decode disaggregation; vLLM; NIXL; KV cache transfer; goodput; AWS EC2

License
CC-BY-4.0 (text and figures), code per the repository license

Related
isSupplementTo: GitHub repository URL. references: DistServe, Splitwise, Sarathi-Serve, Mooncake DOI

↑ Contents 09 Article Skeleton

## Eight sections. Which experiment and figure each section uses

The user writes the sentences. Here there is only the order of the sections and the evidence each section must rest on.

| Section | Question answered | Evidence | Length | 

| 1. Problem | Why PD without RDMA. Who cannot find this answer | The literature's premise (RDMA), the fact of the AWS single-flow cap | Short | 

| 2. Question and claims | C0 in one paragraph, C1 to C7 one sentence each | F0 (E0) | Short | 

| 3. Setup | With what, and how, we measured | T1, §02 factors, §04 protocol summary, repository link | Medium | 

| 4. Interference | Where the cost of mixed serving lies | F1 (E1) | Short | 

| 5. Break-even | Where it wins and where it loses | F2, F3 (E2, E3). The representative figure | Longest | 

| 6. Why it loses | Mechanism | F5, F4 (E5, E4) | Medium | 

| 7. Faster GPUs, smaller KV | How the window moves. Does model choice replace the network | F6, F7 (E6, E7) | Medium | 

| 7.5 Distance to H100 | How far short, and per dollar | F0 again, R0 and R1 | Short | 

| 8. When to use it and when not | Practical decision rules + limits | T2, §07 threats table, list of issues and PRs | Short | 

The one sentence of this article must be "we experimented, and it split this way in this region," not "we will experiment." If one F3 can stand in for that sentence, the article succeeds.

↑ Contents 10 Updates per Round

## The article grows at each round, and is published once

When a round ends, first update the claim status table, then write only the sections of the claims whose status changed. If the status table does not change, that round adds nothing to the article and only that fact is recorded. Opposite results fix the claims along the "if the opposite comes out" lines of §03. Claude prepares the RESULTS tables, figures, and material; the user writes the sentences. No interim publication.

| Round | When | Incoming evidence | What is prepared | Sections the user writes | Claim status | 

| 0 | 9/26 | Protocol finalized | Material organized, status table initialized | Title candidates, one-line claim draft, readers | — | 

| A | 9/27 (g7 ×1) | 3 models started and KV bytes, B1 interference curve, single step, SLO ms, 2 chunk values | RESULTS §A, F1 draft | 4.1 Why this question, the SLO and workload paragraphs of 4.2 | C1 | 

| B | Quota 16 (g7 ×2) | B2 vs P1 (N0) + tc, transfer time, prefill KV time series | RESULTS §B, F2, F3 (partial), F5 drafts, ratio table | First paragraph of 4.3 A10G measurement points, rest of 4.2 | C2, part of C3, C5 | 

| R0 | 10/4 or a weekday | Same-node A10G ×2 | RESULTS §R0, R0 bar in F0 | "If there had been no network" paragraph in 4.3 | Part of C0 | 

| C | Quota 16 (g7e ×2) | Quantization axis, KV size axis, KV fp8 | RESULTS §C, F6, F7, F0 updated | 4.4, 4.5 | C6, C7, C0 updated | 

| D | Quota 16 (PG) | N1 validation point, Azure and Mooncake traces, LongBench and HumanEval, (LMCache) | RESULTS §D, F3 completed, F4, list of issues and PRs | 4.3 completed, 4.6 draft | C3 confirmed, C4 | 

| R1 | Late October | H100 NVLink (measured or literature) | F0 completed, literature number table | "Distance to H100" paragraph | C0 confirmed | 

| Wrap-up | Early November | All raw data, final issues and PRs | T1, T2, final figures, reproduction commands verified, threats table | Summary, conclusion, 4.6 completed, title finalized | Final | 

| Publication | November | — | Repository squash, Zenodo integration, blog build, Korean edition draft | English and Korean proofreading | v1.0 | 

### Checks repeated at every round

- Does RESULTS.md have that round's tables and the list of discarded runs.

- Did any cell change in the claim status table. If not, add nothing to the article and record that fact.

- Is the one-line claim still true. If not, fix it now.

- Did new friction go into the PLAN.md friction log.

- Draft version tag (v0.1 → v1.0) and a one-line change record.

### Claim status table (maintained in ARTICLE.md §9)

| Claim | Evidence | Status | Updated | 

| C0 goodput per dollar, against H100 | E0 | Not measured | — | 

| C1 the cost is in the tail | E1 | Not measured | — | 

| C2 narrow on chat | E2 | Not measured | — | 

| C3 break-even is a function of input length | E3 | Not measured | — | 

| C4 the single-flow cap comes first | E4 | Not measured | — | 

| C5 prefill GPU memory bottleneck | E5 | Not measured | — | 

| C6 the faster the GPU, the narrower the window | E6 | Not measured | — | 

| C7 the smaller the KV size, the more the boundary moves | E7 | Not measured | — | 

The status is one of five: not measured / supported / partly supported / refuted / on hold (insufficient data), and at the end of every round this table and ARTICLE.md §9 are updated together.
