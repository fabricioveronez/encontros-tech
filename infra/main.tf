# VPC
resource "digitalocean_vpc" "main" {
  name   = "${var.project_name}-vpc"
  region = var.region
}

# Cluster DOKS
resource "digitalocean_kubernetes_cluster" "main" {
  name     = "${var.project_name}-cluster"
  region   = var.region
  version  = var.doks_version
  vpc_uuid = digitalocean_vpc.main.id

  ha           = false
  auto_upgrade = true

  node_pool {
    name       = "${var.project_name}-pool"
    size       = "s-1vcpu-2gb"
    node_count = 2
  }

  destroy_all_associated_resources = true
}

# Banco de Dados
resource "digitalocean_database_cluster" "main" {
  name                 = "${var.project_name}-db"
  engine               = "pg"
  version              = "18"
  size                 = "db-amd-1vcpu-1gb"
  region               = var.region
  node_count           = 1
  private_network_uuid = digitalocean_vpc.main.id
}
