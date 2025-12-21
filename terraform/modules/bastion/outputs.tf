output "bastion_public_ip" {
  description = "Bastion host public IP address"
  value       = aws_eip.bastion.public_ip
}

output "bastion_public_dns" {
  description = "Bastion host public DNS name"
  value       = aws_instance.bastion.public_dns
}

output "bastion_security_group_id" {
  description = "Bastion security group ID"
  value       = aws_security_group.bastion.id
}
