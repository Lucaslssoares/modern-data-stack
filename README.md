# Modern Data Stack — Pipeline ELT

[![GitHub](https://img.shields.io/badge/GitHub-Lucaslssoares-181717?style=flat&logo=github)](https://github.com/Lucaslssoares)
[![Gmail](https://img.shields.io/badge/Gmail-solareslucas@gmail.com-D14836?style=flat&logo=gmail)](mailto:solareslucas@gmail.com)

Projeto de orquestração e transformação de dados com Airflow e dbt, integrado ao Airbyte Cloud e ao PostgreSQL.

---

## Visão Geral

O repositório concentra a camada de orquestração e transformação da pilha:

- **Airflow** para orquestrar os pipelines ELT
- **Airbyte Cloud** para sincronizar dados de origem via API externa
- **dbt** para modelagem, testes e publicação das camadas analíticas (Bronze → Silver → Gold)
- **PostgreSQL** como destino das cargas brutas e das tabelas transformadas
- **pgAdmin** como interface visual para consulta e auditoria do banco

> **Importante:** segredos e credenciais devem ficar apenas em arquivos locais (ex.: `config/.env`), nunca versionados no GitHub.

---

## Domínios Atuais

O projeto está estruturado como template e pronto para receber domínios. Ao definir o tema, cadastre aqui:

```
# Domínios ativos (com DAG dedicada):
# <dominio>_pipeline

# Domínios em preparação (sem DAG dedicada):
# <dominio>/
```

Consulte `config/pipeline_config.py` para configurar cada domínio.

---

## Arquitetura

```
Sistemas de Origem (API REST)
          |
          v
   Python Extract (src/)
          |
          v
 PostgreSQL schema: bronze      ← carga bruta via Airflow (flatten + metadata)
          |
          v
 dbt Silver (schema: silver)    ← limpeza, tipagem, padronização (views)
          |
          v
 dbt Gold (schema: gold)        ← agregações e métricas de negócio (tables)
          |
          v
    Consumo Analítico
  (pgAdmin / Airbyte Cloud / notebooks)
```

**Fluxo dentro de cada DAG:**

```
extract → load_bronze → dbt_silver → dbt_test_silver → dbt_gold → dbt_test_gold
```

---

## Estrutura do Repositório

```
.
├── config/
│   ├── pipeline_config.py       # Configuração central: DAG, API, schemas, tabelas
│   ├── .env                     # Segredos locais (não versionado)
│   ├── dbt/
│   │   └── profiles.yml         # Perfil dbt → PostgreSQL (lê variáveis de ambiente)
│   └── pgadmin/
│       └── servers.json         # Conexão automática do pgAdmin
├── dags/
│   └── etl_dag.py               # DAG genérica: extract → bronze → silver → gold
├── src/
│   ├── common/
│   │   ├── logger.py            # get_logger() centralizado
│   │   └── database.py          # get_engine() SQLAlchemy
│   ├── extract_data.py          # Requisição HTTP → raw_data.json
│   ├── flatten_data.py          # JSON → DataFrame Bronze (+ _loaded_at, _source)
│   └── load_data.py             # DataFrame → PostgreSQL (schema-aware)
├── dbt/
│   ├── dbt_project.yml
│   ├── macros/
│   │   └── generate_schema_name.sql   # Schema exato sem prefixo
│   └── models/
│       ├── bronze/
│       │   └── sources.yml            # Declara tabelas raw como fontes dbt
│       ├── silver/
│       │   ├── stg_template.sql       # Limpeza e tipagem (view)
│       │   └── schema.yml
│       └── gold/
│           ├── fct_template.sql       # Métricas e agregações (table)
│           └── schema.yml
├── tests/
│   └── unit/
│       ├── test_extract.py
│       └── test_flatten.py
├── notebooks/
│   └── analysis_data.ipynb      # Análise exploratória
├── Dockerfile.airflow            # Airflow + dbt-postgres instalado
├── docker-compose.yaml
├── main.py                       # Execução local sem Docker
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Configuração Local Segura

### 1. Pré-requisitos

- Docker Desktop instalado e em execução
- Acesso à API que será consumida (definida em `config/pipeline_config.py`)
- Credenciais e variáveis definidas apenas localmente

### 2. Crie o arquivo local de ambiente

```bash
# Windows
copy .env.example config\.env

# Linux/Mac
cp .env.example config/.env
```

### 3. Preencha os segredos no `.env`

```env
API_KEY=sua_chave_aqui

DB_HOST=postgres
DB_PORT=5432
DB_USER=airflow
DB_PASSWORD=airflow
DB_NAME=airflow

LOG_LEVEL=INFO
```

Use valores reais do seu ambiente. **Não publique esse arquivo.**

### 4. Suba os containers

```bash
docker compose up --build
```

O `--build` é necessário apenas na primeira execução para instalar o dbt na imagem do Airflow.

### 5. Recupere a senha do Airflow

```bash
docker exec airflow-weather-pipeline-airflow-1 cat /opt/airflow/standalone_admin_password.txt
```

Acesse em **http://localhost:8080** com usuário `admin`.

---

## Camada Analítica

O diretório `notebooks/` é usado para consultas exploratórias, validação e auditoria dos dados.

- **Não** substitui os modelos de produção (`models/silver`, `models/gold`)
- **Não** entra no fluxo padrão das DAGs de produção
- Serve como base para validações manuais e análises pontuais

---

## Executar dbt Local (via Docker)

Para execução manual use o container dbt, que compartilha o mesmo diretório `dbt/`:

```bash
# Testar conexão
docker exec airflow-weather-pipeline-dbt-1 dbt debug

# Instalar pacotes
docker exec airflow-weather-pipeline-dbt-1 dbt deps

# Run/test por camada
docker exec airflow-weather-pipeline-dbt-1 dbt run  --select silver
docker exec airflow-weather-pipeline-dbt-1 dbt test --select silver

docker exec airflow-weather-pipeline-dbt-1 dbt run  --select gold
docker exec airflow-weather-pipeline-dbt-1 dbt test --select gold

# Build completo (run + test)
docker exec airflow-weather-pipeline-dbt-1 dbt build --select silver+
```

Exemplo para um domínio específico (após definir o tema):

```bash
docker exec airflow-weather-pipeline-dbt-1 dbt build \
  --select "silver.<dominio>+ gold.<dominio>+"
```

---

## Variáveis Importantes do Airflow

Configure em **Admin → Variables** na UI do Airflow.

**Configuração da DAG:**

| Variável | Descrição |
|---|---|
| `api_key` | Chave de autenticação da API de origem |
| `db_host` | Host do PostgreSQL (`postgres` dentro do Docker) |
| `log_level` | Nível de log (`INFO`, `DEBUG`) |

**Configuração Airbyte Cloud** (quando integrado):

| Variável | Descrição |
|---|---|
| `airbyte_base_url` | URL base da API do Airbyte Cloud |
| `airbyte_api_token` | Token de autenticação |
| `airbyte_connection_ids_<dominio>` | IDs de conexão por domínio |

> As DAGs leem as variáveis de `config/pipeline_config.py`. Variáveis sensíveis devem ficar em `config/.env`, nunca no código.

---

## Alertas por E-mail

Para habilitar notificações de falha nas DAGs, configure em `dags/etl_dag.py`:

```python
default_args={
    "email": ["seu@email.com"],
    "email_on_failure": True,
    "email_on_retry": False,
}
```

E defina as variáveis SMTP no Airflow (**Admin → Connections** → `smtp_default`).

Regras padrão adotadas:

- Envia apenas em `failure`
- Não envia em `retry`
- Não envia em sucesso

---

## Como os Pipelines Funcionam

1. A DAG lê a configuração de `config/pipeline_config.py` (URL da API, schemas, tabela de destino)
2. A task `extract` faz GET na API e salva `data/raw_data.json`
3. A task `load_bronze` achata o JSON com `json_normalize`, adiciona `_loaded_at` e `_source`, e carrega no schema `bronze`
4. O Airflow aciona `dbt run --select silver` — o dbt lê o bronze como source e gera views limpas no schema `silver`
5. O Airflow aciona `dbt test --select silver` — valida qualidade dos dados
6. O Airflow aciona `dbt run --select gold` — agrega e publica tabelas no schema `gold`
7. O Airflow aciona `dbt test --select gold` — valida as métricas finais
8. Os modelos ficam disponíveis nos schemas `bronze`, `silver` e `gold` do PostgreSQL

**Padrão de modelagem adotado:**

- `silver`: pode manter metadados técnicos de carga (`_loaded_at`, `_source`)
- `gold`: deve ficar sem colunas de metadados técnicos — apenas colunas de negócio

O comportamento compartilhado (logger, database engine) fica centralizado em `src/common/`, simplificando a duplicação entre DAGs.

---

## Documentação Complementar

O guia operacional detalhado do dbt está em `dbt/dbt_project.yml` e nos arquivos `schema.yml` de cada camada, incluindo:

- Configuração de schemas por camada (silver = view, gold = table)
- Declaração de fontes Bronze
- Exemplos de testes de qualidade de dados
- Macro `generate_schema_name` para naming exato sem prefixo

---

## Observações

- O arquivo `config/.env` é local e **não deve ser versionado**
- Arquivos de infraestrutura devem ler credenciais por variável de ambiente — sem hardcode no repositório
- O perfil usado pelas tasks dbt do Airflow é `config/dbt/profiles.yml` (lê do `.env` via `env_var()`)
- O arquivo `config/dbt/profiles.yml` serve tanto para o container dbt (desenvolvimento) quanto para o Airflow (produção automatizada)
- Para execução local fora do Docker, use `main.py` — ele resolve os paths automaticamente
- O schema `bronze` é criado pelo Python (`load_data.py`); os schemas `silver` e `gold` são criados automaticamente pelo dbt

---

## Checklist Antes de Fazer Push

```bash
# 1) garantir que não existe segredo real pronto para commit
git status --short

# 2) validar que o arquivo local de segredos não será enviado
git check-ignore -v config/.env

# 3) varredura simples de termos sensíveis em arquivos versionados
git diff --cached | grep -i -E "(password|secret|token|api_key\s*=\s*['\"][^'\"]{8,})"
```

---

## Solução de Problemas Rápida

**DAG não carrega no Airflow**

```bash
docker exec airflow-weather-pipeline-airflow-1 airflow dags list
docker exec airflow-weather-pipeline-airflow-1 airflow dags report
```

**dbt não conecta ao banco**

```bash
docker exec airflow-weather-pipeline-dbt-1 dbt debug
# Verifique se DB_PASSWORD está definido em config/.env
```

**Erro de permissão nos diretórios do dbt**

```bash
# Linux/Mac
chmod -R u+rwX dbt/target dbt/dbt_packages

# Windows — recriar os diretórios
docker exec airflow-weather-pipeline-dbt-1 rm -rf /usr/app/target /usr/app/dbt_packages
```

**Resetar tudo do zero**

```bash
docker compose down -v
docker compose up --build
```

**Ver logs de um container**

```bash
docker logs airflow-weather-pipeline-airflow-1 --tail 50 -f
docker logs airflow-weather-pipeline-dbt-1     --tail 50 -f
```
