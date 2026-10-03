# infra

Terraform and two wrapper scripts that created the AWS EC2 nodes for each measurement round and destroyed them afterwards. Nothing here runs continuously; the project's standing AWS cost is zero once `down.sh` has run.

## What it provisions

`terraform/` (provider `hashicorp/aws ~> 5.0`, Terraform >= 1.5, region `us-east-1`):

| Resource | File | Notes |
|---|---|---|
| GPU nodes (`aws_instance.gpu`, count = `gpu_count`) | `instances.tf` | On-demand. AMI = latest Amazon "Deep Learning OSS Nvidia Driver AMI GPU PyTorch (Ubuntu 22.04)". Root volume gp3, `volume_size_gb` (default 400 GB), 500 MB/s, 6000 IOPS, encrypted. Instance type from `gpu_profile`; the second node can take a different type via `gpu_profile_b` (intended for a head-to-head such as L40S vs RTX PRO 6000). |
| Client node (`aws_instance.client`, 0 or 1) | `instances.tf` | Created with `client = true`. Canonical Ubuntu 22.04 AMI, type `client_type` (default `c6i.xlarge`), 50 GB root volume. Runs the load generator and the proxies. |
| Cluster placement group (`aws_placement_group.cluster`) | `network.tf` | Created with `placement_group = true`; both GPU nodes and the client join it. |
| Security group (`aws_security_group.nodes`) | `network.tf` | SSH (22/tcp) from `allowed_ssh_cidr` only; all traffic among members of the group (vLLM 8000/8100/8200, NIXL side channel 5600, UCX ephemeral ports, iperf3 5201); all egress. |
| Key pair (`aws_key_pair.key`) | `network.tf` | Public key from `ssh_public_key_path` (default `~/.ssh/id_ed25519.pub`). |
| Subnet (data source) | `network.tf` | The default subnet of `availability_zone` (default `us-east-1b`). All nodes share one AZ because a cluster placement group requires it. `vpc_id` is read from the subnet because the deploying IAM user lacks `ec2:DescribeVpcAttribute`. |
| Outputs | `outputs.tf` | `gpu_public_ips`, `gpu_private_ips`, `gpu_instance_ids`, `client_public_ip`, `client_private_ip`, `gpu_type`, `placement_group`, and `ssh` (ready-made `ssh ubuntu@<ip>` lines). |

User data (`terraform/scripts/*.tftpl`):

- GPU nodes install `iperf3 jq sysstat at git python3-pip`, start an iperf3 server, install the proxy dependencies (`aiohttp fastapi uvicorn httpx`) for the ubuntu user, pull the pinned vLLM image (`vllm_image`, default `vllm/vllm-openai:v0.30.0`), optionally sync weights from `s3_weights_uri`, and schedule `shutdown -h` after `auto_shutdown_hours`.
- The client node installs the same tools plus `python3-venv`, creates `~/venv` with `vllm[bench]==0.30.0` and `aiohttp`, and schedules the same auto-shutdown.
- Both write `/var/log/user-data.log` when done; the round scripts poll that file.

Resource names carry a `-<workspace>` suffix outside the `default` Terraform workspace, so a second deployment (for example the GPU pair while the client is already up) can live in its own workspace without name collisions.

## Variables

Defined in `terraform/variables.tf`.

| Variable | Default | Meaning |
|---|---|---|
| `allowed_ssh_cidr` | none, must be set | CIDR allowed to reach SSH, e.g. your own IP as `203.0.113.4/32`. `up.sh` reads it from the `ALLOWED_SSH_CIDR` environment variable and refuses to run without it. |
| `aws_profile` | `default` | AWS CLI profile used by the provider. |
| `aws_region` | `us-east-1` | Region. |
| `availability_zone` | `us-east-1b` | g7e.2xlarge was offered only in us-east-1b and us-east-1d when checked (2026-09-24). |
| `ssh_public_key_path` | `~/.ssh/id_ed25519.pub` | Public key uploaded as the key pair. |
| `gpu_profile` | `g7_2x` | One of `g5_xl g5_2x g5_4x g5_8x g5_12x g6e_2x g6e_4x g7_2x g7_4x g7e_2x`; mapped to an instance type in `locals.profiles`. |
| `gpu_profile_b` | `""` | Profile for the second GPU node when it differs from the first. |
| `gpu_count` | 1 | Number of GPU nodes. |
| `client` | false | Whether to create the client node. |
| `client_type` | `c6i.xlarge` | Client instance type. |
| `placement_group` | false | Whether to create and use a cluster placement group. |
| `auto_shutdown_hours` | 3 | Hours until each node shuts itself down. |
| `volume_size_gb` | 400 | GPU node root volume. Three models filled 194 GB in round A′, and 31B BF16 alone is 62 GB. |
| `vllm_image` | `vllm/vllm-openai:v0.30.0` | Pinned 2026-09-24 (release 2026-09-22). |
| `s3_weights_uri` | `""` | Optional `s3://bucket/prefix` to sync into `/models`; empty skips the sync. |
| `gpu_ami_filter`, `client_ami_filter` | DLAMI / Ubuntu Jammy name filters | AMI selection. |

## up.sh and down.sh

```
ALLOWED_SSH_CIDR=<your ip>/32 infra/up.sh PROFILE GPU_COUNT [--client] [--pg] [--hours N] [--profile-b PROFILE] [--ws NAME]
infra/down.sh [--ws NAME]
```

`up.sh`:

- `PROFILE` is a `gpu_profile` key, `GPU_COUNT` the number of GPU nodes (0 is allowed, e.g. to create only the client).
- `--client` adds the client node, `--pg` puts everything in a cluster placement group, `--hours N` sets the auto-shutdown (default 3), `--profile-b` sets `gpu_profile_b`, `--ws NAME` selects or creates a Terraform workspace.
- The environment variable `CLIENT_TYPE` overrides `client_type` (round E8 used `c6i.2xlarge`).
- It runs `terraform init`, `terraform apply -auto-approve`, writes all outputs to `infra/last-outputs.json` (or `last-outputs-<ws>.json`), and prints the `ssh` output.

`down.sh` runs `terraform destroy -auto-approve -refresh=false` in the given workspace (or the current one). When two workspaces are up, run it once per workspace, e.g. `infra/down.sh --ws e8` and then `infra/down.sh --ws default`. Note that after `up.sh --ws e8` the current workspace is `e8`, so a bare `down.sh` destroys that one, not `default`.

Examples from the rounds:

```
infra/up.sh g5_xl 2 --hours 2                                   # round P
infra/up.sh g7e_2x 1 --hours 2                                  # round A′
infra/up.sh g7_2x 1 --hours 3                                   # round A
CLIENT_TYPE=c6i.2xlarge infra/up.sh g7e_2x 0 --client --hours 8 # round E8 client, default workspace
infra/up.sh g7e_2x 2 --pg --hours 8 --ws e8                     # round E8 GPU pair, workspace e8
```

Instance types used in the study: `g5.xlarge` (A10G, plumbing only), `g7.2xlarge` (RTX PRO 4500 32 GB), `g7e.2xlarge` (RTX PRO 6000 96 GB), `g6e.2xlarge` (L40S 48 GB), and `c6i.xlarge` / `c6i.2xlarge` for the client. The bandwidth figures in `locals.profiles` are nominal; the harness records the measured iperf3 values per round.

## Cost warning

GPU instances bill by the hour from the moment they start, whether or not anything runs on them. A g7e.2xlarge pair with a client costs several dollars per hour. Always finish a round with `infra/down.sh` (once per workspace), and then confirm in the AWS console or with the CLI that no instance is left:

```
aws ec2 describe-instances --filters Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,Tags[?Key==`Name`].Value|[0]]' --output table
```

The user-data auto-shutdown (`--hours`) is a safety net, not the shutdown path: a stopped on-demand instance no longer bills for compute, but its EBS volume does until the instance is terminated by `down.sh`.

## ena-express.sh

```
infra/ena-express.sh on|off i-aaa i-bbb ...
```

Toggles ENA Express (SRD) on the primary network interface of the given instance IDs, for both TCP and UDP. This was the planned "N2" network setting of the protocol. It needs `ec2:DescribeNetworkInterfaces` and `ec2:ModifyNetworkInterfaceAttribute`, and the instance type must support ENA Express.

## Files not in git

`terraform/.terraform/`, `terraform/*.tfstate*`, `terraform/.terraform.lock.hcl`, and `last-outputs.json` are ignored (`infra/.gitignore`). State lives only on the machine that ran `up.sh`.
