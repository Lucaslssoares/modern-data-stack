# 🌤️ Pipeline ETL - Dados Climáticos de Uiraúna/PB

[![LinkedIn](https://img.shields.io/badge/LinkedIn-luisfernando--eng-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/luisfernando-eng/)
[![Instagram](https://img.shields.io/badge/Instagram-@luis__fernando__jv__eng-E4405F?style=flat&logo=instagram)](https://www.instagram.com/luis_fernando_jv_eng)
[![Gmail](https://img.shields.io/badge/Gmail-luizfer.12321@gmail.com-D14836?style=flat&logo=gmail)](mailto:luizfer.12321@gmail.com)

> Pipeline ETL automatizado para coleta, transformação, armazenamento e análise de dados meteorológicos em tempo real da cidade de Uiraúna - PB.

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Arquitetura do Pipeline](#-arquitetura-do-pipeline)
- [Stack Tecnológica](#-stack-tecnológica)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Como Executar](#-como-executar)
- [Detalhamento das Etapas](#-detalhamento-das-etapas)
- [Análise e Visualização de Dados](#-análise-e-visualização-de-dados)
- [Troubleshooting](#-troubleshooting)
- [Contato](#-contato)

---

## 🎯 Sobre o Projeto

Este projeto tem como objetivo demonstrar a construção de um **pipeline ETL completo** aplicado a dados reais, utilizando boas práticas de Engenharia de Dados.

O pipeline coleta dados meteorológicos da API OpenWeatherMap **a cada hora**, transforma os dados brutos em um formato estruturado e os armazena em um banco de dados PostgreSQL — servindo como base para análises e visualizações exploratórias.

A cidade escolhida foi **Uiraúna - PB**, no sertão paraibano, região com clima semiárido e grande variação de temperatura ao longo do dia.

---

## 🏗️ Arquitetura do Pipeline

### Diagrama Visual

![Diagrama ETL - Pipeline Climático Uiraúna/PB](assets/ETL.jpg)

---

```
OpenWeatherMap API
        │
        ▼
  ┌─────────────┐
  │   EXTRACT   │  → Requisição HTTP → weather_data.json
  └─────────────┘
        │
        ▼
  ┌─────────────┐
  │  TRANSFORM  │  → Normalização, renomeação, conversão de timestamps → temp_data.parquet
  └─────────────┘
        │
        ▼
  ┌─────────────┐
  │    LOAD     │  → Inserção no PostgreSQL (tabela: uirauna_weather)
  └─────────────┘
        │
        ▼
  ┌─────────────┐
  │   ANÁLISE   │  → Jupyter Notebook com visualizações e insights
  └─────────────┘

  Orquestração: Apache Airflow (schedule: a cada 1 hora)
  Infraestrutura: Docker + Docker Compose
```

---

## 🛠️ Stack Tecnológica

### Core

- **Python 3.12+** — Linguagem principal
- **Apache Airflow 2.9.2** — Orquestração do pipeline
- **PostgreSQL 16** — Banco de dados relacional
- **Docker & Docker Compose** — Containerização

### Bibliotecas Python

- **pandas** — Manipulação e transformação de dados
- **requests** — Requisições HTTP para a API
- **SQLAlchemy** — Conexão com o banco de dados
- **psycopg2** — Driver PostgreSQL
- **python-dotenv** — Gerenciamento de variáveis de ambiente
- **pyarrow** — Suporte ao formato Parquet
- **matplotlib / seaborn** — Visualização de dados
- **jupyter** — Análise exploratória interativa

---

## 📁 Estrutura do Projeto

```
pipeline_weather/
├── config/
│   └── .env                  # Variáveis de ambiente (não versionado)
├── dags/
│   └── weather_dag.py        # Definição da DAG no Airflow
├── data/
│   ├── weather_data.json     # Dados brutos extraídos da API
│   └── temp_data.parquet     # Dados transformados (intermediário)
├── logs/                     # Logs do Airflow
├── notebooks/
│   └── analysis_data.ipynb   # Análise e visualização dos dados
├── src/
│   ├── extract_data.py       # Etapa de extração
│   ├── transform_data.py     # Etapa de transformação
│   └── load_data.py          # Etapa de carga
├── docker-compose.yaml       # Definição dos serviços Docker
├── .env.example              # Exemplo de variáveis de ambiente
└── README.md
```

---

## ✅ Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/)
- Conta gratuita na [OpenWeatherMap](https://openweathermap.org/api) para obter a API Key
- Git

---

## 🚀 Instalação e Configuração

### 1️⃣ Clone o Repositório

```bash
git clone https://github.com/seu-usuario/pipeline_weather.git
cd pipeline_weather
```

### 2️⃣ Obtenha sua API Key

1. Acesse [openweathermap.org](https://openweathermap.org/api)
2. Crie uma conta gratuita
3. Gere sua API Key no dashboard

### 3️⃣ Configure as Variáveis de Ambiente

Crie o arquivo `config/.env` baseado no exemplo:

```bash
mkdir -p config
cp .env.example config/.env
```

Edite o arquivo com suas credenciais:

```env
# config/.env

API_KEY=sua_chave_api_aqui

DB_USER=airflow
DB_PASSWORD=airflow
DB_NAME=airflow
DB_HOST=postgres
```

> ⚠️ **IMPORTANTE:** Nunca commite o arquivo `.env` com suas chaves reais no Git!

### 4️⃣ Crie as Pastas e Ajuste Permissões

```bash
mkdir -p logs data
sudo chmod -R 777 logs data
```

### 5️⃣ Inicie os Containers

```bash
docker compose up
```

Aguarde todos os serviços subirem. Na primeira execução, o Airflow inicializa o banco e cria o usuário `admin` automaticamente.

### 6️⃣ Recupere a Senha do Airflow

```bash
docker exec pipeline_weather-airflow-1 cat /opt/airflow/standalone_admin_password.txt
```

---

## 🎮 Como Executar

### 1️⃣ Acesse a Interface do Airflow

Abra: **http://localhost:8080**

**Credenciais:**

- Username: `admin`
- Password: _(gerada automaticamente — veja passo 6 acima)_

### 2️⃣ Ative e Dispare a DAG

1. Localize a DAG **`clima_uirauna_etl`**
2. Clique no botão ▶ **Trigger DAG** para executar manualmente
3. A DAG está configurada para rodar **a cada 1 hora** automaticamente

### 3️⃣ Verifique os Dados no Banco

```bash
docker exec -it pipeline_weather-postgres-1 psql -U airflow -d airflow
```

```sql
SELECT COUNT(*) FROM uirauna_weather;
SELECT * FROM uirauna_weather ORDER BY datetime DESC LIMIT 5;
```

---

## 🔍 Detalhamento das Etapas

### 📥 ETAPA 1: EXTRACT

**Arquivo:** `src/extract_data.py`

- Faz requisição HTTP GET para a API OpenWeatherMap
- Valida o status code da resposta
- Salva os dados brutos em `data/weather_data.json`

**Dados coletados:** temperatura, sensação térmica, umidade, pressão, vento, nebulosidade, coordenadas, horários de nascer e pôr do sol.

---

### 🔄 ETAPA 2: TRANSFORM

**Arquivo:** `src/transform_data.py`

1. **Leitura do JSON** e criação do DataFrame com `pd.json_normalize()`
2. **Normalização da coluna `weather`** — extrai `weather_id`, `weather_main`, `weather_description`
3. **Remoção de colunas** desnecessárias
4. **Renomeação de colunas** para nomes padronizados em inglês
5. **Conversão de timestamps Unix** para datetime no fuso `America/Fortaleza`

**Resultado:** DataFrame limpo salvo em formato Parquet.

---

### 💾 ETAPA 3: LOAD

**Arquivo:** `src/load_data.py`

- Lê o arquivo Parquet intermediário
- Conecta ao PostgreSQL via SQLAlchemy
- Insere os dados na tabela `uirauna_weather` com `if_exists='append'`
- Valida a inserção com `SELECT COUNT(*)`

**Por que Parquet entre as etapas?**
Formato binário eficiente que preserva tipos de dados (datetime, float), evitando problemas de serialização entre as tasks do Airflow.

---

## 📊 Análise e Visualização de Dados

**Arquivo:** `notebooks/analysis_data.ipynb`

Com os dados acumulados no PostgreSQL, o notebook realiza análise exploratória e geração de visualizações sobre o clima de Uiraúna ao longo do tempo.

### O que está sendo analisado:

- 🌡️ **Temperatura** — variação ao longo do dia e tendências horárias
- 💧 **Umidade** — correlação com temperatura e sensação térmica
- 💨 **Vento** — velocidade, direção e rajadas
- ☁️ **Nebulosidade** — frequência de céu aberto vs nublado
- 🌅 **Padrões diários** — análise de médias por hora do dia
- 📈 **Série temporal** — evolução das variáveis meteorológicas

### Como rodar o notebook:

```bash
# Instale as dependências localmente
pip install pandas matplotlib seaborn psycopg2-binary sqlalchemy jupyter python-dotenv

# Inicie o Jupyter
jupyter notebook notebooks/analysis_data.ipynb
```

> O notebook se conecta diretamente ao PostgreSQL do container para buscar os dados acumulados.

---

## 🐛 Troubleshooting

### DAG com erro de importação

```bash
# Verifique se o .env está no lugar certo
docker exec pipeline_weather-airflow-1 cat /opt/airflow/config/.env
```

### Erro de permissão nas pastas

```bash
sudo chmod -R 777 logs data
```

### Banco de dados com schema desatualizado

```bash
docker exec -it pipeline_weather-postgres-1 psql -U airflow -d airflow -c "DROP TABLE IF EXISTS uirauna_weather;"
```

Re-execute a DAG para recriar a tabela com o schema correto.

### Erro `execution_date` ao subir o Airflow

Volume do PostgreSQL com dados de versão antiga. Solução:

```bash
docker compose down -v
docker compose up
```

### Resetar tudo do zero

```bash
docker compose down -v
sudo rm -rf logs/*
docker compose up
```

---

## 📧 Contato

**Luis Fernando**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-luisfernando--eng-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/luisfernando-eng/)
[![Instagram](https://img.shields.io/badge/Instagram-@luis__fernando__jv__eng-E4405F?style=flat&logo=instagram)](https://www.instagram.com/luis_fernando_jv_eng)
[![Gmail](https://img.shields.io/badge/Gmail-luizfer.12321@gmail.com-D14836?style=flat&logo=gmail)](mailto:luizfer.12321@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-seu--usuario-181717?style=flat&logo=github)](https://github.com/seu-usuario)
