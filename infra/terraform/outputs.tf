output "gpu_public_ips" {
  value = aws_instance.gpu[*].public_ip
}
output "gpu_private_ips" {
  value = aws_instance.gpu[*].private_ip
}
output "gpu_instance_ids" {
  value = aws_instance.gpu[*].id
}
output "client_public_ip" {
  value = try(aws_instance.client[0].public_ip, null)
}
output "client_private_ip" {
  value = try(aws_instance.client[0].private_ip, null)
}
output "gpu_type" {
  value = local.gpu_type
}
output "placement_group" {
  value = try(aws_placement_group.cluster[0].name, null)
}
output "ssh" {
  value = concat([for ip in aws_instance.gpu[*].public_ip : "ssh ubuntu@${ip}"], [for ip in aws_instance.client[*].public_ip : "ssh ubuntu@${ip}"])
}
