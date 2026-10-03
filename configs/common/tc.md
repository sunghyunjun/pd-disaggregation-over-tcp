*English translation of `tc.md`; the Korean file is the original.*

# tc bandwidth equalization / sweep (sender side, identical on both GPU nodes)

```bash
IF=$(ip -o -4 route show to default | awk '{print $5}')   # usually ens5
# apply (example: 5 Gbps). burst should be comfortably larger than rate*latency
sudo tc qdisc replace dev $IF root tbf rate 5gbit burst 128mb latency 50ms
# check
tc -s qdisc show dev $IF
# remove
sudo tc qdisc del dev $IF root
```
Sweep values: 1gbit, 2500mbit, 5gbit (N0), 10gbit (within N1), 25gbit (within N2).
Each time a cap is applied, record the effective value with iperf3 -P 1 and keep it in env_snapshot. tc matches only bandwidth, not RTT → record ping.
