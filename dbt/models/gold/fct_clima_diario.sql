-- =============================================================================
-- CAMADA GOLD — agregações diárias de clima
-- Materialização: table
-- Grão: 1 linha por dia para o ponto geográfico
-- Base para fct_clima_mensal
-- =============================================================================
{{ config(materialized='table') }}

with silver as (

    select * from {{ ref('stg_openmeteo') }}

),

diario as (

    select
        nome_localidade,
        latitude,
        longitude,
        elevacao_m,
        fuso_horario,
        data_medicao,

        -- Temperatura (°C)
        round(avg(temperatura_c),          1)       as temperatura_media_c,
        max(temperatura_c)                          as temperatura_max_c,
        min(temperatura_c)                          as temperatura_min_c,
        round(avg(temperatura_sensacao_c), 1)       as temperatura_sensacao_media_c,

        -- Precipitação — soma acumulada diária (mm)
        round(sum(chuva_mm),               2)       as chuva_total_mm,
        count(case when chuva_mm > 0
                   then 1 end)                      as horas_com_chuva,

        -- Umidade relativa (%)
        round(avg(umidade_pct),            1)       as umidade_media_pct,
        max(umidade_pct)                            as umidade_max_pct,
        min(umidade_pct)                            as umidade_min_pct,

        -- Ponto de orvalho (°C)
        round(avg(orvalho_c),              1)       as orvalho_medio_c,

        -- Vento
        round(avg(vento_velocidade_ms),    1)       as vento_velocidade_media_ms,
        max(vento_rajada_ms)                        as vento_rajada_max_ms,

        -- Pressão (hPa = mbar)
        round(avg(pressao_mb),             1)       as pressao_media_mb,

        -- Radiação solar — total diário e média horária (W/m²)
        round(sum(radiacao_wm2),           0)       as radiacao_total_wm2,
        round(avg(radiacao_wm2),           1)       as radiacao_media_wm2,

        -- Qualidade
        count(*)                                    as horas_com_dados   -- máx 24

    from silver
    group by
        nome_localidade,
        latitude,
        longitude,
        elevacao_m,
        fuso_horario,
        data_medicao

)

select * from diario
order by data_medicao desc
