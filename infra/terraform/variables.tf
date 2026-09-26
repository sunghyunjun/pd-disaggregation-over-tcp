variable "aws_region" {
  type    = string
  default = "us-east-1"
}
variable "aws_profile" {
  type    = string
  default = "default"
}
# AZ: g7e.2xlarge is offered only in us-east-1b and us-east-1d (checked 2026-09-24); g5.4xlarge/g5.12xlarge in a,b,c,d,f.
variable "availability_zone" {
  type    = string
  default = "us-east-1b"
}
variable "ssh_public_key_path" {
  type    = string
  default = "~/.ssh/id_ed25519.pub"
}
variable "allowed_ssh_cidr" {
  type    = string
  default = "0.0.0.0/0"
}

# GPU node profile. Bandwidth notes are nominal; the harness records iperf3 effective values.
variable "gpu_profile" {
  type    = string
  default = "g7_2x"
  validation {
    condition     = contains(["g5_xl", "g5_2x", "g5_4x", "g5_8x", "g5_12x", "g6e_2x", "g6e_4x", "g7_2x", "g7_4x", "g7e_2x"], var.gpu_profile)
    error_message = "unknown gpu_profile"
  }
}
# 두 번째 GPU 노드에 다른 타입을 쓸 때만 설정 (예: g6e_2x vs g7e_2x 정면 비교). 빈 값이면 gpu_profile과 같음.
variable "gpu_profile_b" {
  type    = string
  default = ""
}

variable "gpu_count" {
  type    = number
  default = 1
}
variable "client" {
  type    = bool
  default = false
}
variable "client_type" {
  type    = string
  default = "c6i.xlarge"
}
variable "placement_group" {
  type    = bool
  default = false
}
variable "auto_shutdown_hours" {
  type    = number
  default = 3
}
variable "volume_size_gb" {
  type    = number
  default = 400 # A′: 3 models filled 194 GB; 31B BF16 (62 GB) needs more
}
variable "vllm_image" {
  type    = string
  default = "vllm/vllm-openai:v0.30.0" # pinned 2026-09-24 (release 2026-09-22); fallback v0.29.0
}
variable "s3_weights_uri" {
  type    = string
  default = "" # e.g. s3://bucket/models ; empty = skip sync
}
variable "gpu_ami_filter" {
  type    = string
  default = "Deep Learning OSS Nvidia Driver AMI GPU PyTorch * (Ubuntu 22.04)*"
}
variable "client_ami_filter" {
  type    = string
  default = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
}

locals {
  profiles = {
    g5_xl  = { type = "g5.xlarge", note = "A10G 24GB, 4 vCPU, 2.5 Gbps baseline (burst 10) - plumbing only" }
    g5_2x  = { type = "g5.2xlarge", note = "A10G 24GB, 8 vCPU, 5 Gbps baseline (burst 10) - stage A single node" }
    g5_4x  = { type = "g5.4xlarge", note = "A10G 24GB, 16 vCPU, 10 Gbps baseline (burst 25) - stages B/C" }
    g5_8x  = { type = "g5.8xlarge", note = "A10G 24GB, 32 vCPU, 25 Gbps fixed" }
    g5_12x = { type = "g5.12xlarge", note = "A10G x4, 48 vCPU, 40 Gbps - R0 same-node reference" }
    g6e_2x = { type = "g6e.2xlarge", note = "L40S 48GB, 8 vCPU, 5 Gbps baseline (burst 20)" }
    g6e_4x = { type = "g6e.4xlarge", note = "L40S 48GB, 16 vCPU, 20 Gbps fixed" }
    g7_2x  = { type = "g7.2xlarge", note = "RTX PRO 4500 32GB, 8 vCPU, 40 Gbps baseline (peak 60) - stage D main Blackwell point, $2.52/h" }
    g7_4x  = { type = "g7.4xlarge", note = "RTX PRO 4500 32GB, 16 vCPU, 80 Gbps baseline (peak 100)" }
    g7e_2x = { type = "g7e.2xlarge", note = "RTX PRO 6000 96GB, 8 vCPU, 50 Gbps fixed - E7 only (30B MoE / Gemma 4), us-east-1b or 1d" }
  }
  gpu_type   = local.profiles[var.gpu_profile].type
  gpu_type_b = var.gpu_profile_b != "" ? local.profiles[var.gpu_profile_b].type : local.profiles[var.gpu_profile].type
}
