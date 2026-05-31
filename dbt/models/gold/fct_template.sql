-- =============================================================================
-- CAMADA GOLD — métricas e agregações prontas para BI e análise
-- Renomear para fct_<tema>.sql ou dim_<tema>.sql ao definir o domínio.
-- Materialização: table (persistida, consultas rápidas para dashboards)
-- =============================================================================
{{ config(materialized='table') }}

with silver as (

    select * from {{ ref('stg_template') }}

),

aggregated as (

    select
        -- AJUSTE: aplique as métricas e agregações do seu domínio.
        --
        -- Fact tables (fct_*): eventos mensuráveis com granularidade baixa
        --   date_trunc('day', criado_em)   as dia,
        --   count(*)                       as total_registros,
        --   sum(valor)                     as receita_total,
        --   avg(valor)                     as ticket_medio,
        --
        -- Dimension tables (dim_*): entidades descritivas (quem, onde, o quê)
        --   distinct id                    as entidade_id,
        --   nome, categoria, regiao

        *

    from silver

)

select * from aggregated
