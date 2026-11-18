# Infraestrutura - Encontros Tech

Este diretório contém a infraestrutura necessária para o ambiente de homologação.

## Provisionamento

1. **Terraform**: Provisiona VPC, cluster DOKS e banco de dados gerenciado.
   - Informe o token de API da DigitalOcean na variável `do_token`: copie `terraform.tfvars.example` para `terraform.tfvars` (ignorado pelo Git) e preencha, ou exporte `TF_VAR_do_token`.
   - Execute:
     ```bash
     cd infra
     terraform init
     terraform apply
     ```

2. **Docker Hub**: Constrói e publica a imagem pública da aplicação com uma tag sequencial `vN`.
   - Execute os comandos a seguir na raiz do repositório. Se o passo do Terraform deixou o shell em `infra/`, volte antes com `cd ..`.
   - Crie no Docker Hub um repositório público chamado `encontros-tech` e um API token com permissão **Read & Write**.
   - Defina o nome da conta e faça login. Quando solicitado, informe o token como senha; não o inclua em comandos, arquivos do projeto ou argumentos de build:
     ```bash
     export DOCKERHUB_USER=seu_usuario
     docker login --username "$DOCKERHUB_USER"
     ```
   - Antes de publicar, confirme que a tag escolhida ainda não existe. Para a primeira versão:
     ```bash
     docker buildx imagetools inspect "docker.io/${DOCKERHUB_USER}/encontros-tech:v1"
     ```
     Se o comando exibir um manifesto, escolha a próxima tag (`v2`, `v3` etc.); nunca reutilize uma tag publicada. Um erro de rede ou autenticação não confirma que a tag está livre.
   - Construa e publique a imagem para a arquitetura dos nós DOKS (`linux/amd64`):
     ```bash
     TAG=v1 COMMIT_SHA="$(git rev-parse --short HEAD)" \
       docker buildx bake -f docker-bake.hcl --push app
     ```
     Informe `-f docker-bake.hcl` para não carregar o `compose.yaml` local nem depender das variáveis de banco. O Bake valida o usuário e a tag antes do build. A imagem ficará em `docker.io/${DOCKERHUB_USER}/encontros-tech:v1`.
   - Antes do deploy, atualize `image` em `infra/k8s/deployment.yaml` para a imagem publicada e `SERVICE_VERSION` em `infra/k8s/configmap.yaml` para a mesma tag; não use `latest`.

3. **Kubernetes**: Aplica os manifestos da aplicação.
   - Obtenha o kubeconfig do cluster DOKS via `doctl` ou Console DigitalOcean.
   - Crie o Secret `encontros-tech-secret` manualmente com a `DATABASE_URL` (obtida do output `db_private_uri` do Terraform):
     ```bash
     kubectl create secret generic encontros-tech-secret \
       --namespace encontros-tech \
       --from-literal=DATABASE_URL=postgres://user:password@host:port/dbname?sslmode=require
     ```
   - Aplique os manifestos:
     ```bash
     kubectl apply -f infra/k8s/
     ```

## CI/CD com GitHub Actions

Os workflows em `.github/workflows/` executam testes, lint do Dockerfile e build da imagem em pull requests e em pushes para `main`. Uma publicação é iniciada ao enviar uma tag Git no formato `vN` (por exemplo, `v2`); após validar os manifests, o workflow publica a imagem no Docker Hub e aplica os manifests ao cluster DOKS.

Configure em **Settings → Secrets and variables → Actions**:

| Tipo | Nome | Valor |
| --- | --- | --- |
| Variable | `DOCKERHUB_USERNAME` | Nome da conta Docker Hub que contém o repositório público `encontros-tech`. |
| Variable (opcional) | `DOKS_CLUSTER_NAME` | Nome do cluster DOKS; o padrão é `encontros-tech-cluster`. |
| Secret | `DOCKERHUB_TOKEN` | API token do Docker Hub com permissão **Read & Write**. |
| Secret | `DIGITALOCEAN_ACCESS_TOKEN` | Token de API da DigitalOcean com acesso ao cluster DOKS. |

Antes de criar uma tag de release, atualize `image` em `infra/k8s/deployment.yaml` para `<DOCKERHUB_USERNAME>/encontros-tech:vN` e `SERVICE_VERSION` em `infra/k8s/configmap.yaml` para a mesma versão. Faça commit dessas alterações e então crie e envie a tag correspondente:

```bash
git tag v2
git push origin v2
```

O workflow exige que os dois manifests já indiquem a tag enviada. Tags publicadas anteriormente no Docker Hub nunca são sobrescritas; em uma nova execução da mesma release, o workflow reutiliza a imagem existente e continua com o deploy. O Secret `encontros-tech-secret` com a `DATABASE_URL` deve existir previamente no namespace `encontros-tech`; o workflow verifica sua existência e falha com uma mensagem explícita se estiver ausente. Após a aplicação dos manifests, o workflow aguarda a conclusão do rollout.
