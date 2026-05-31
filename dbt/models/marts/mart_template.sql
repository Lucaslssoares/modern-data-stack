-- =============================================================================
-- MARTS LAYER — Agregações e métricas prontas para BI / análise
-- Renomeie para fct_<tema>.sql ou dim_<tema>.sql quando definir o tema.
-- =============================================================================
-- Materialização: table (resultado persistido, mais rápido para consultas)
{{ config(materialized='table') }}

with staging as (
    select * from {{ ref('stg_template') }}
),

aggregated as (
    select
        -- AJUSTE AQUI: aplique as métricas e agregações do domínio.
        --
        -- date_trunc('day', criado_em)  as dia,
        -- count(*)                      as total_registros,
        -- avg(valor)                    as valor_medio,
        -- max(valor)                    as valor_maximo,
        -- min(valor)                    as valor_minimo
        *
    from staging
)

select * from aggregated
