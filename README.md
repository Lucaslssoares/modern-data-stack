# Modern Data Stack — Pipeline ETL Template

[![GitHub](https://img.shields.io/badge/GitHub-Lucaslssoares-181717?style=flat&logo=github)](https://github.com/Lucaslssoares)
[![Gmail](https://img.shields.io/badge/Gmail-solareslucas@gmail.com-D14836?style=flat&logo=gmail)](mailto:solareslucas@gmail.com)

> Template de pipeline ETL modular e reutilizável construído sobre Apache Airflow, dbt, PostgreSQL e Docker. Projetado para ser adaptado a qualquer fonte de dados ou domínio de negócio.

---

## Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Arquitetura](#arquitetura)
- [Stack Tecnológica](#stack-tecnológica)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
- [Como Executar](#como-executar)
- [Usando o dbt](#usando-o-dbt)
- [pgAdmin](#pgadmin)
- [Como Adaptar para seu Tema](#como-adaptar-para-seu-tema)
- [Testes](#testes)
- [Troubleshooting](#troubleshooting)

---

## Sobre o Projeto

Este repositório implementa um **Modern Data Stack** completo e containerizado, servindo como base para pipelines ETL de qualquer domínio.

O template já entrega pronto:

- Orquestração com **Apache Airflow** (DAG genérica configurável)
- Camada de transformação SQL com **dbt** (staging + marts)
- Armazenamento em **PostgreSQL 16**
- Interface visual com **pgAdmin 4**
- Conexão com **Airbyte Cloud** via porta 5432 exposta
- Testes unitários com **pytest**
- Logging centralizado e configuração via variáveis de ambiente

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                     ORQUESTRAÇÃO                        │
│                  Apache Airflow :8080                   │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ EXTRACT  │ │TRANSFORM │ │   LOAD   │
    │ API REST │ │  Pandas  │ │ SQLAlch. │
    │  → JSON  │ │ → Parquet│ │→Postgres │
    └──────────┘ └──────────┘ └──────────┘
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
              ┌──────────────┐         ┌──────────────────┐
              │   dbt :exec  │         │  pgAdmin  :5050  │
              │  staging SQL │         │  Interface visual │
              │  marts  SQL  │         └──────────────────┘
              └──────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  PostgreSQL :5432│ ← Airbyte Cloud
              └──────────────────┘
```

**Fluxo de dados:**
1. **Extract** — requisição HTTP GET para API configurada, salva `raw_data.json`
2. **Transform** — normalização, renomeação e tipagem via Pandas, salva `temp_data.parquet`
3. **Load** — inserção no PostgreSQL (modo append, acumula histórico)
4. **dbt** — transforma os dados raw em camadas staging (views) e marts (tables)

---

## Stack Tecnológica

| Camada | Tecnologia | Versão |
|---|---|---|
| Orquestração | Apache Airflow | 2.9.2 |
| Transformação Python | Pandas + PyArrow | 3.x |
| Transformação SQL | dbt-postgres | 1.9.0 |
| Banco de dados | PostgreSQL | 16 |
| Interface DB | pgAdmin 4 | latest |
| Containerização | Docker + Compose | v2 |
| Linguagem | Python | 3.12+ |
| Testes | pytest | 8.x |

---

## Estrutura do Projeto

```
modern-data-stack/
│
├── config/                          # Configurações centralizadas
│   ├── pipeline_config.py           # ← PREENCHA AQUI ao definir o tema
│   ├── .env                         # Credenciais (não versionado)
│   ├── dbt/
│   │   └── profiles.yml             # Conexão dbt → PostgreSQL (via env vars)
│   └── pgadmin/
│       └── servers.json             # Conexão pgAdmin (automática)
│
├── dags/
│   └── etl_dag.py                   # DAG Airflow genérica
│
├── src/
│   ├── common/
│   │   ├── logger.py                # get_logger() centralizado
│   │   └── database.py              # get_engine() SQLAlchemy
│   ├── extract_data.py              # Etapa Extract
│   ├── transform_data.py            # Etapa Transform
│   └── load_data.py                 # Etapa Load
│
├── dbt/
│   ├── dbt_project.yml
│   └── models/
│       ├── schema.yml
│       ├── staging/
│       │   ├── sources.yml          # Declara tabela raw como fonte
│       │   └── stg_template.sql     # Template de staging layer
│       └── marts/
│           └── mart_template.sql    # Template de mart layer
│
├── tests/
│   └── unit/
│       ├── test_extract.py          # Testes da etapa Extract
│       └── test_transform.py        # Testes da etapa Transform
│
├── notebooks/
│   └── analysis_data.ipynb          # Análise exploratória
│
├── docker-compose.yaml              # Todos os serviços
├── main.py                          # Execução local (sem Docker)
├── pyproject.toml                   # Dependências e configuração pytest
└── .env.example                     # Template de variáveis de ambiente
```

---

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução
- Conta na API que será consumida (definida ao escolher o tema)
- Git

---

## Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/Lucaslssoares/modern-data-stack.git
cd modern-data-stack
```

### 2. Crie o arquivo de credenciais

```bash
# Windows
copy .env.example config\.env

# Linux/Mac
cp .env.example config/.env
```

Edite `config/.env`:

```env
API_KEY=sua_chave_api_aqui

DB_HOST=postgres
DB_PORT=5432
DB_USER=airflow
DB_PASSWORD=airflow
DB_NAME=airflow

LOG_LEVEL=INFO
```

### 3. Crie as pastas de runtime

```bash
# Windows
mkdir data logs

# Linux/Mac
mkdir -p data logs
```

### 4. Suba os containers

```bash
docker compose up
```

Na primeira execução o Airflow inicializa o banco automaticamente (~2 min).

---

## Como Executar

### Airflow — http://localhost:8080

Recupere a senha gerada automaticamente:

```bash
docker exec airflow-weather-pipeline-airflow-1 cat /opt/airflow/standalone_admin_password.txt
```

- **Usuário:** `admin`
- **Senha:** _(valor retornado acima)_

Na UI localize a DAG configurada em `pipeline_config.DAG_ID` e clique em **▶ Trigger DAG**.

### Verificar dados no banco

```bash
docker exec -it airflow-weather-pipeline-postgres-1 psql -U airflow -d airflow
```

```sql
SELECT COUNT(*) FROM minha_tabela;
SELECT * FROM minha_tabela ORDER BY 1 DESC LIMIT 5;
```

---

## Usando o dbt

O container dbt fica sempre ativo para execução sob demanda.

```bash
# Testar conexão com o banco
docker exec airflow-weather-pipeline-dbt-1 dbt debug

# Rodar todos os models
docker exec airflow-weather-pipeline-dbt-1 dbt run

# Rodar apenas staging
docker exec airflow-weather-pipeline-dbt-1 dbt run --select staging

# Rodar testes de qualidade de dados
docker exec airflow-weather-pipeline-dbt-1 dbt test

# Entrar no container interativamente
docker exec -it airflow-weather-pipeline-dbt-1 bash
```

Os models ficam em `dbt/models/`:

| Camada | Pasta | Materialização | Finalidade |
|---|---|---|---|
| Staging | `models/staging/` | view | Limpa e padroniza os dados raw |
| Marts | `models/marts/` | table | Agrega e entrega métricas para análise |

---

## pgAdmin

Acesse em **http://localhost:5050**

- **Email:** `admin@admin.com`
- **Senha:** `admin`

O servidor **ETL - PostgreSQL** já aparece pré-configurado na barra lateral. Ao conectar pela primeira vez, informe a senha `airflow`.

---

## Como Adaptar para seu Tema

Toda a configuração do pipeline está centralizada em **`config/pipeline_config.py`**. Ao definir o tema, preencha:

```python
# 1. Identifique a DAG
DAG_ID          = "nome_do_seu_pipeline"
DAG_SCHEDULE    = "0 */1 * * *"          # frequência de execução

# 2. Aponte para a API
API_BASE_URL = "https://api.exemplo.com/dados?appid={api_key}"

# 3. Nomeie a tabela de destino
TABLE_NAME = "nome_da_tabela"

# 4. Configure o mapeamento de colunas
COLUMNS_TO_DROP   = ["coluna_desnecessaria"]
COLUMNS_TO_RENAME = {"nome_api": "nome_padronizado"}
DATETIME_COLUMNS  = ["datetime"]
```

Em seguida ajuste:

- **`src/transform_data.py`** — funções marcadas com `# AJUSTE AQUI`
- **`dbt/models/staging/stg_template.sql`** — renomeie e implemente a limpeza SQL
- **`dbt/models/marts/mart_template.sql`** — implemente as agregações do domínio
- **`dbt/models/staging/sources.yml`** — atualize o nome da tabela raw

---

## Testes

```bash
# Instale dependências de dev
pip install -e ".[dev]"

# Rode todos os testes
pytest

# Com cobertura
pytest --cov=src --cov-report=term-missing
```

Testes disponíveis em `tests/unit/`:

- `test_extract.py` — testa HTTP 200, erros e resposta vazia
- `test_transform.py` — testa criação de DataFrame, drop, rename e conversão de datetime

---

## Troubleshooting

### Verificar .env dentro do Airflow

```bash
docker exec airflow-weather-pipeline-airflow-1 cat /opt/airflow/config/.env
```

### dbt não encontra o banco

```bash
docker exec airflow-weather-pipeline-dbt-1 dbt debug
```

Verifique se `DB_PASSWORD` está definido no `config/.env`.

### Resetar volumes e reiniciar do zero

```bash
docker compose down -v
docker compose up
```

### Ver logs de um container específico

```bash
docker logs airflow-weather-pipeline-airflow-1 --tail 50
docker logs airflow-weather-pipeline-dbt-1 --tail 50
```

### Airflow não carrega a DAG

```bash
docker exec airflow-weather-pipeline-airflow-1 airflow dags list
docker exec airflow-weather-pipeline-airflow-1 airflow dags test meu_pipeline_etl
```

---

## Contato

**Lucas Soares**

[![GitHub](https://img.shields.io/badge/GitHub-Lucaslssoares-181717?style=flat&logo=github)](https://github.com/Lucaslssoares)
[![Gmail](https://img.shields.io/badge/Gmail-solareslucas@gmail.com-D14836?style=flat&logo=gmail)](mailto:solareslucas@gmail.com)
