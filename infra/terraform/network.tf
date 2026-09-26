# The default subnet of the chosen AZ. All nodes share it (cluster placement group requires one AZ).
# (No aws_vpc data source: it needs ec2:DescribeVpcAttribute, which terraform-admin lacks. vpc_id comes from the subnet.)
data "aws_subnet" "chosen" {
  availability_zone = var.availability_zone
  default_for_az    = true
}

resource "aws_security_group" "nodes" {
  name        = "pd-without-rdma-sg${local.ws_suffix}"
  description = "SSH from allowed CIDR; all traffic among experiment nodes"
  vpc_id      = data.aws_subnet.chosen.vpc_id
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }
  # vLLM 8000/8100/8200, NIXL side channel 5600+, UCX ephemeral, iperf3 5201
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_key_pair" "key" {
  key_name   = "pd-without-rdma-key${local.ws_suffix}"
  public_key = file(pathexpand(var.ssh_public_key_path))
}

resource "aws_placement_group" "cluster" {
  count    = var.placement_group ? 1 : 0
  name     = "pd-without-rdma-pg${local.ws_suffix}"
  strategy = "cluster"
}
