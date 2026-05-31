-- =============================================================================
-- CAMADA SILVER — limpeza, padronização e tipagem dos dados Bronze
-- Renomear para stg_<tema>.sql ao definir o domínio.
-- Materialização: view (recalculada a cada run, sem custo de storage)
-- =============================================================================
{{ config(materialized='view') }}

with source as (

    select * from {{ source('bronze', 'raw_source') }}

),

cleaned as (

    select
        -- Metadados de rastreabilidade
        _loaded_at,
        _source,

        -- AJUSTE: renomeie, tipe e limpe cada coluna vinda do Bronze.
        -- Boas práticas:
        --   - snake_case para todos os nomes
        --   - tipos explícitos (::integer, ::numeric, ::timestamp)
        --   - nulos tratados: nullif(trim(col), '') → converte '' em NULL
        --   - sem lógica de negócio aqui — apenas limpeza estrutural
        --
        -- Exemplos:
        --   id::integer                             as registro_id,
        --   trim(nome)::text                        as nome,
        --   valor::numeric(12, 2)                   as valor,
        --   to_timestamp(ts)::timestamp with time zone as criado_em,
        --   nullif(trim(status), '')                as status

        *

    from source
    where _loaded_at is not null

)

select * from cleaned
