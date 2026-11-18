variable "do_token" {
  description = "Token de API da DigitalOcean (definir em terraform.tfvars ou TF_VAR_do_token)"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Nome do projeto para prefixar recursos"
  type        = string
  default     = "encontros-tech"
}

variable "region" {
  description = "Região da DigitalOcean para provisionar os recursos"
  type        = string
  default     = "nyc1"
}

variable "doks_version" {
  description = "Versão do Kubernetes para o cluster DOKS"
  type        = string
  default     = "1.37.2-do.0"
}
