-- =============================================================================
-- STAGING LAYER — Normalização e limpeza dos dados brutos
-- Renomeie este arquivo para stg_<tema>.sql quando definir o tema.
-- =============================================================================
-- Materialização: view (recalculada sempre, sem custo de storage)
{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'minha_tabela') }}
),

renamed as (
    select
        -- AJUSTE AQUI: renomeie e tipe cada coluna da tabela raw.
        -- Padrão: snake_case, tipos explícitos, nulos tratados.
        --
        -- id::integer                             as registro_id,
        -- nome::text                              as nome,
        -- valor::numeric(10,2)                    as valor,
        -- created_at::timestamp with time zone    as criado_em,
        -- nullif(trim(status), '')                as status,    -- '' → NULL
        *
    from source
)

select * from renamed
