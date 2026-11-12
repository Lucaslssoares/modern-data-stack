# DevOps na Prática — clima-api

Camada de DevOps adicionada sobre o pipeline ELT (Airflow + dbt + PostgreSQL).
A aplicação entregue é a **clima-api** (FastAPI), que publica os dados da camada Gold
(`gold.fct_clima_diario` e `gold.fct_clima_mensal`) via HTTP.

```
Open-Meteo ─► Airflow (extract/bronze) ─► dbt (silver/gold) ─► PostgreSQL (../infra)
                                                                   │
                         GitHub Actions: test ─► build ─► push GHCR ─► helm deploy (Kind)
                                                                   │
                                                  clima-api (FastAPI) ─► stdout JSON
                                                                   │
                                          Filebeat ─► Elasticsearch ─► Kibana (dashboard)
```

| Etapa | Onde está |
|---|---|
| 2 — CI | [.github/workflows/main.yml](../.github/workflows/main.yml), testes em [tests/unit/](../tests/unit/), [api/Dockerfile](../api/Dockerfile) |
| 3 — CD + Helm | [helm/clima-api/](../helm/clima-api/), [helm/kind-config.yaml](../helm/kind-config.yaml), job `deploy` do workflow |
| 4 — Logs/Métricas | [observability/](../observability/), middleware de log em [api/clima_api/main.py](../api/clima_api/main.py) |

---

## Como executar

### Pré-requisitos
Docker Desktop, `kubectl` (já vem no Docker Desktop), `helm` e `kind`:
```powershell
winget install Helm.Helm Kubernetes.kind
```

A infra compartilhada (PostgreSQL com as tabelas gold e a rede Docker `projetos_shared`) fica em
`../infra/` e precisa estar de pé antes da API, local ou no Kind:
```bash
cd ../infra && docker compose up -d postgres pgadmin && cd -
```
O CI no GitHub **não** depende dela: os testes simulam o banco e o smoke test do deploy usa só `/health`.

### Etapa 2 — CI (GitHub Actions)
Basta dar `git push` na branch `main`. O workflow executa:
1. **test** — `uv sync --extra dev` + `pytest` (pipeline e API);
2. **build** — `docker build` da pasta `api/` e push para `ghcr.io/lucaslssoares/clima-api:<sha>` e `:latest`
   (autenticação com o `GITHUB_TOKEN`, sem segredo extra);
3. **deploy** — ver Etapa 3.

Em pull request só o job `test` roda. Print para a entrega: aba **Actions** do repositório.

### Etapa 3 — CD + Kubernetes + Helm
**No pipeline (automático):** o job `deploy` cria um cluster Kind no runner, carrega a imagem
recém-publicada, executa `helm upgrade --install` com a tag do commit e faz um smoke test em
`http://localhost:30080/health`, verificando que a versão servida é o SHA do commit.

**Local (para o print / apresentação):**
```bash
kind create cluster --name devops --config helm/kind-config.yaml
helm upgrade --install clima-api helm/clima-api --set image.tag=latest
kubectl get pods,svc -l app=clima-api     # print do serviço rodando
curl http://localhost:30080/health
```
> Se o pacote no GHCR estiver privado, torne-o público em *GitHub → Packages → clima-api →
> Package settings*, ou carregue a imagem local: `docker build -t ghcr.io/lucaslssoares/clima-api:latest api && kind load docker-image ghcr.io/lucaslssoares/clima-api:latest --name devops`.

O chart cria um **Deployment** (2 réplicas, probes em `/health`), um **Service NodePort 30080**
e um **Secret** com a senha do banco. O banco padrão é o Postgres de `../infra/`, que publica a
porta 5432 no host; os pods o alcançam via `host.docker.internal`.

### Etapa 4 — Filebeat + Elasticsearch + Kibana
```bash
docker compose -f observability/docker-compose.yml up -d --build
bash observability/gerar_trafego.sh                 # gera 200/404/500/503
```
Kibana: http://localhost:5601 (≈1 min para subir).

**Como o Beat coleta os dados:**
1. A API escreve **uma linha JSON por requisição** no stdout (método, rota, status, duração em ms).
2. O Docker grava o stdout em `/var/lib/docker/containers/<id>/<id>-json.log`.
3. O **Filebeat** usa *autodiscover* (escuta o `docker.sock`): quando aparece um container com
   `clima-api` no nome, abre um input `filestream` naquele arquivo.
4. O parser `container` remove o envelope do Docker e o `ndjson` transforma o JSON da API em
   campos (`http.response.status_code`, `http.response.duration_ms`, `url.path`, `log.level`).
5. `add_docker_metadata` acrescenta nome/imagem do container e o evento vai para o
   Elasticsearch (data stream `filebeat-8.17.0`).

**Dashboard como código.** Com o Kibana de pé:
```bash
python observability/dashboard.py        # cria data view, busca e painéis; exporta dashboard.ndjson
```
Abra http://localhost:5601/app/dashboards#/view/clima-api-dashboard (últimos 15 min, refresh 5s):

| Painel | O que mostra |
|---|---|
| Erros 5xx | contador de respostas com `http.response.status_code >= 500` |
| Requisições por status code | barras empilhadas por intervalo (200 / 404 / 500 / 503) |
| Tempo de resposta (ms) | p50 e p95 de `http.response.duration_ms` |
| Requisições e latência por rota | tabela por `url.path` com contagem e latência média |
| Logs em tempo real | busca salva com nível, status, rota, duração e mensagem |

Em outro Kibana, dá para importar só o arquivo: *Stack Management → Saved Objects → Import →
`observability/dashboard.ndjson`*.

---

## Relatório

### Etapa 1 — Conceitos

**DevOps e Ágil.** O Ágil encurtou o ciclo de *desenvolver*: entregas pequenas, frequentes e com
feedback do usuário. Só que de nada adianta terminar uma funcionalidade por sprint se o deploy
acontece uma vez por trimestre e depende de outra equipe. DevOps estende a agilidade até a
operação: a mesma equipe é responsável por construir, entregar e operar, com automação
(pipelines), infraestrutura como código e monitoramento. *Analogia:* o Ágil é a cozinha que passou
a preparar pratos em pequenos lotes; DevOps é o restaurante inteiro (cozinha, garçom e
caixa) funcionando como uma linha só, medindo o que volta no prato.

**CI × Continuous Delivery × Continuous Deployment.**
- **CI (Integração Contínua):** a cada push o código é integrado e verificado automaticamente
  (testes, build). *Neste projeto:* job `test`, que roda os 14 testes do pipeline e da API.
- **Continuous Delivery:** todo commit aprovado gera um artefato **pronto** para produção, mas a
  publicação depende de um clique humano. *Neste projeto:* a imagem versionada no GHCR.
- **Continuous Deployment:** não há o clique; o que passa no pipeline vai para o ambiente
  sozinho. *Neste projeto:* job `deploy`, que aplica o `helm upgrade` com a tag do commit.

*Analogia:* CI é o controle de qualidade de cada peça; Delivery é a peça embalada na doca;
Deployment é o caminhão que sai sozinho assim que a peça é aprovada.

**Máquinas virtuais × containers.** A VM virtualiza o *hardware*: cada uma carrega um sistema
operacional completo (GBs, minutos para iniciar). O container virtualiza o *sistema
operacional*: compartilha o kernel do host e empacota só a aplicação e suas dependências (MBs,
segundos). *Analogia:* VM é uma casa (fundação, encanamento e telhado próprios); container é
um apartamento (estrutura compartilhada, cada um com sua chave). Vantagens observadas aqui:
- a mesma imagem `clima-api` roda no notebook, no runner do GitHub e no Kubernetes ("funciona na
  minha máquina" deixa de ser problema);
- subir Elasticsearch, Kibana e Filebeat leva um comando, sem instalar nada no Windows;
- escala horizontal trivial (`replicaCount: 2`) e rollback trocando a tag.

### Etapa 5 — Implementação, desafios e reflexão

**Passo a passo.**
1. Criação da `clima-api` (FastAPI) sobre a camada Gold, com testes usando banco simulado
   (`dependency_overrides`), sem depender de Postgres no CI.
2. `Dockerfile` enxuto (python:3.12-slim, usuário sem privilégio, versão injetada via `APP_VERSION`).
3. Workflow GitHub Actions com 3 jobs encadeados (`test → build → deploy`).
4. Chart Helm com Deployment, Service NodePort e Secret; o pipeline sobrescreve `image.tag` com o SHA.
5. Logs estruturados em JSON + Filebeat com autodiscover + Elasticsearch + Kibana.

**Desafios enfrentados.**
- *Aplicação sem HTTP:* o projeto original é um pipeline batch e não tinha requisições para medir;
  a solução foi expor a camada Gold numa API.
- *Testes quebrados:* os testes de `flatten_data` ainda usavam o formato JSON antigo, anterior à
  migração para Open-Meteo; foram atualizados para o formato colunar real antes de ligar o CI.
- *CD para cluster local:* o runner do GitHub não alcança um Kind na máquina do aluno; o deploy
  automático roda em um Kind efêmero dentro do próprio runner, com smoke test que confirma a
  versão publicada.
- *Logs multilinha:* tracebacks do Python quebravam um erro em várias linhas no Filebeat; o
  middleware passou a registrar exceções numa única linha JSON.
- *Dashboard via API:* o `_import` do Kibana trata objetos sem versão como antigos e falha ao
  migrá-los; o script cria via `_bulk_create` e exporta o `.ndjson` oficial, que reimporta sem erro.
- *Recursos:* Elasticsearch limitado a 512 MB de heap para caber no Docker Desktop junto do resto.

**Reflexão — como DevOps agrega valor.** Antes, colocar uma alteração no ar dependia de
passos manuais e de "lembrar de rodar os testes". Com o pipeline, cada commit é testado,
empacotado e implantado em minutos, sempre do mesmo jeito; um erro aparece no job `test`, não em
produção. A imagem versionada pelo SHA dá rastreabilidade (qual commit está rodando?) e rollback
imediato. O monitoramento fecha o ciclo: o dashboard mostra taxa de erro e latência **depois**
do deploy, e essa informação volta para o planejamento, que é o "loop infinito" do DevOps
(plan → code → build → test → release → deploy → operate → monitor).

### Roteiro da apresentação (10 min)
1. (1 min) Contexto: pipeline de clima e a API.
2. (3 min) Commit ao vivo → Actions rodando `test → build → deploy`; imagem no GHCR.
3. (2 min) `kubectl get pods,svc` + `curl localhost:30080/health` mostrando a versão nova.
4. (3 min) `gerar_trafego.sh` → Kibana: logs em tempo real, status codes, latência p95.
5. (1 min) Reflexão e desafios.
