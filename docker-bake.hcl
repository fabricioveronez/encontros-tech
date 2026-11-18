variable "DOCKERHUB_USER" {
  default = ""

  validation {
    condition     = DOCKERHUB_USER != ""
    error_message = "Defina DOCKERHUB_USER com o nome da sua conta Docker Hub."
  }
}

variable "TAG" {
  default = ""

  validation {
    condition     = TAG != "" && TAG == regex("^v[1-9][0-9]*$", TAG)
    error_message = "Defina TAG como uma versão sequencial, por exemplo v1 ou v2; latest não é permitido."
  }
}

variable "COMMIT_SHA" {
  default = "unknown"
}

target "app" {
  context    = "."
  dockerfile = "Dockerfile"
  platforms  = ["linux/amd64"]
  tags       = ["docker.io/${DOCKERHUB_USER}/encontros-tech:${TAG}"]

  args = {
    VERSION    = TAG
    COMMIT_SHA = COMMIT_SHA
  }
}