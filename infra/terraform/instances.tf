data "aws_ami" "gpu" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = [var.gpu_ami_filter]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}
data "aws_ami" "client" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = [var.client_ami_filter]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# On-Demand GPU nodes (quota: Running On-Demand G and VT instances, vCPU-summed)
resource "aws_instance" "gpu" {
  count                       = var.gpu_count
  ami                         = data.aws_ami.gpu.id
  instance_type               = local.gpu_type
  subnet_id                   = data.aws_subnet.chosen.id
  vpc_security_group_ids      = [aws_security_group.nodes.id]
  key_name                    = aws_key_pair.key.key_name
  associate_public_ip_address = true
  placement_group             = var.placement_group ? aws_placement_group.cluster[0].name : null
  root_block_device {
    volume_type = "gp3"
    volume_size = var.volume_size_gb
    throughput  = 500
    iops        = 6000
    encrypted   = true
  }
  user_data = templatefile("${path.module}/scripts/user-data-gpu.sh.tftpl", {
    hours          = var.auto_shutdown_hours
    vllm_image     = var.vllm_image
    s3_weights_uri = var.s3_weights_uri
    role           = "gpu${count.index}"
  })
  tags = {
    Name    = "pd-gpu-${count.index}"
    Role    = "gpu"
    Profile = var.gpu_profile
  }
}

# Client / proxy node (Standard family quota)
resource "aws_instance" "client" {
  count                       = var.client ? 1 : 0
  ami                         = data.aws_ami.client.id
  instance_type               = var.client_type
  subnet_id                   = data.aws_subnet.chosen.id
  vpc_security_group_ids      = [aws_security_group.nodes.id]
  key_name                    = aws_key_pair.key.key_name
  associate_public_ip_address = true
  placement_group             = var.placement_group ? aws_placement_group.cluster[0].name : null
  root_block_device {
    volume_type = "gp3"
    volume_size = 50
    encrypted   = true
  }
  user_data = templatefile("${path.module}/scripts/user-data-client.sh.tftpl", {
    hours = var.auto_shutdown_hours
  })
  tags = {
    Name = "pd-client"
    Role = "client"
  }
}
