output "cluster_id" {
  description = "ID do cluster Kubernetes"
  value       = digitalocean_kubernetes_cluster.main.id
}

output "db_private_uri" {
  description = "URI privada do banco de dados (usar no Secret manual)"
  value       = digitalocean_database_cluster.main.private_uri
  sensitive   = true
}

output "vpc_id" {
  description = "ID da VPC criada"
  value       = digitalocean_vpc.main.id
}
