# Lead author-side verification notes (checked by the lead, not by reviewers)

1. EFA / ENA Express (fetched AWS docs: ec2/latest/instancetypes/ac.html and AWSEC2/latest/UserGuide/efa.html, 2026-09-30)
   - g6e.2xlarge: 5.0/20.0 Gbps baseline/burst, EFA No, ENA Express No, max 4 ENIs, 1x L40S
   - g6e.8xlarge: 25 Gbps, EFA Yes (Nitro v4, RDMA read/write, no GDR), 1x L40S
   - g7.2xlarge: 40/60 Gbps, EFA No; g7.8xlarge: 100 Gbps, EFA Yes (with GDR), 1x RTX PRO 4500
   - g7e.2xlarge: 50 Gbps, EFA No, max 4 ENIs; g7e.8xlarge: 100 Gbps, EFA Yes (RDMA read/write, no GDR), 1x RTX PRO 6000
   - ENA Express: No on all six sizes above.
   => Reviewer 3 is right: single-GPU nodes with EFA exist (8xlarge). The paper's premise must be "the cheapest single-GPU sizes (2xlarge) have no EFA", not "single GPU => no RDMA". Price of 8xlarge not yet looked up.

2. Global-stall events in disaggregated runs (reran reviewer 2's scratch script r2_global.py): reproduced exactly.
   26_2P1D 4K @9 0.769 -> 0.996 without 5 events; 31_1P1D chat @8 0.863-0.944 -> 0.973-0.978. Replica runs show zero such events (B2/B3 at 4K and chat). The next 1-2 gaps after a stall are <2 ms (burst delivery) => delivery-path cause more likely than GPU compute.
   Router asymmetry confirmed in harness/serve_pair.sh: replicas/single use harness/rr_proxy.py (aiohttp); PD uses vLLM's tests/v1/kv_connector/nixl_integration/toy_proxy_server.py. PROTOCOL.md line 213 had promised "같은 프록시 프로세스". If the toy proxy causes the global stalls, the asymmetry penalizes disaggregation, not replicas (i.e., PD limits are conservative).

3. Absolute vs relative ITL threshold: RESULTS.md line 150 records a deliberate decision: relative 5x-step thresholds make faster models stricter (e.g., 26B BF16 5x = 38 ms) and distort cross-model comparison; "보고서에는 상대 SLO(모델별)와 절대 SLO(채팅 50 ms / 문서 250 ms 공통) 둘 다 제시". So the switch to absolute 50 ms was intentional and justified in the notebook, but the paper neither discloses the pre-registered relative rule nor reports relative results.

4. KV transfer volume is affine, not linear (RESULTS.md lines 310/326/343): 26B NVFP4 4K 140 MB, 16K 260 MB, 32K 412 MB (vLLM "MB" is likely MiB). Section 4.3's 16K example is wrong.

5. NIXL splitting (RESULTS.md 453-454, 483-490): in v0.30.0 num_threads default 4 (adjustable via kv_connector_extra_config), split_batch_size 1024 descriptors minimum per chunk, UCX TCP one socket per endpoint pair (dev_num_paths=1). So a 26B 4K request (2,240 descriptors) is split into 3 chunks (1024/1024/192) over up to 3 thread endpoints; 31B (4,480) into 4. Direction consistent with m>1, but never verified with socket counts (ss). Treat as source-reading inference.

6. Chunk size: every safe run uses --max-num-batched-tokens 2560. RESULTS.md line 77 only says "청크 2048은 mm 검사로 거부(마찰 #4)" (multimodal budget check of Gemma 4). harness/serve.sh now always passes --limit-mm-per-prompt '{"image":0}'; whether a chunk below 2560 starts with that flag is untested. A replica chunk sweep would need new cloud runs (user approval + cost).

7. Context for the chair: the author intends to publish this as an independent preprint (Zenodo DOI, possibly arXiv later), aiming to be a citable reference for practitioners — not submitting to a venue right now. Budget so far about $217; E7 cost about $90. Any new experiment needs the author's explicit approval.
