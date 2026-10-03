# tc 대역폭 등화 / 스윕 (송신 측, GPU 노드 양쪽에 동일하게)

```bash
IF=$(ip -o -4 route show to default | awk '{print $5}')   # 보통 ens5
# 걸기 (예: 5 Gbps). burst는 rate*latency보다 넉넉히
sudo tc qdisc replace dev $IF root tbf rate 5gbit burst 128mb latency 50ms
# 확인
tc -s qdisc show dev $IF
# 해제
sudo tc qdisc del dev $IF root
```
스윕 값: 1gbit, 2500mbit, 5gbit (N0), 10gbit (N1 안에서), 25gbit (N2 안에서).
걸 때마다 iperf3 -P 1 로 실효값을 기록해 env_snapshot에 남긴다. tc는 대역폭만 맞추고 RTT는 못 맞춘다 → ping 기록.
