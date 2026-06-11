-- =============================================================================
-- CAMADA SILVER — limpeza e tipagem dos dados brutos Open-Meteo
-- Materialização: view
-- Fonte: bronze.raw_openmeteo (dados horários ERA5/ICON)
-- Grão: 1 linha por hora para o ponto geográfico configurado
-- =============================================================================
{{ config(materialized='view') }}

with source as (

    select * from {{ source('bronze', 'raw_openmeteo') }}

),

cleaned as (

    select
        -- Rastreabilidade
        _loaded_at,
        _source,

        -- Localização do ponto geográfico
        latitude::numeric(10, 6)                        as latitude,
        longitude::numeric(10, 6)                       as longitude,
        elevation::numeric(8, 1)                        as elevacao_m,
        timezone                                        as fuso_horario,
        case
            when abs(latitude - (-2.42)) < 0.05 and abs(longitude - (-48.15)) < 0.05 then 'Tomé-Açu'
            when abs(latitude - (-2.93)) < 0.05 and abs(longitude - (-48.95)) < 0.05 then 'Tailândia'
            when abs(latitude - (-1.96)) < 0.05 and abs(longitude - (-48.20)) < 0.05 then 'Acará'
            when abs(latitude - (-1.88)) < 0.05 and abs(longitude - (-48.77)) < 0.05 then 'Moju'
            else 'Desconhecido'
        end                                             as nome_localidade,

        -- Dimensão temporal
        "time"::timestamp                               as medido_em,
        "time"::timestamp::date                         as data_medicao,
        extract(hour from "time"::timestamp)::int       as hora,

        -- Temperatura (°C)
        temperature_2m::numeric(6, 1)                   as temperatura_c,
        apparent_temperature::numeric(6, 1)             as temperatura_sensacao_c,

        -- Precipitação (mm/h)
        precipitation::numeric(8, 2)                    as chuva_mm,

        -- Umidade relativa (%)
        relativehumidity_2m::numeric(5, 1)              as umidade_pct,

        -- Ponto de orvalho (°C)
        dewpoint_2m::numeric(6, 1)                      as orvalho_c,

        -- Vento (m/s e graus)
        windspeed_10m::numeric(6, 1)                    as vento_velocidade_ms,
        windgusts_10m::numeric(6, 1)                    as vento_rajada_ms,
        winddirection_10m::numeric(5, 1)                as vento_direcao_graus,

        -- Pressão atmosférica (hPa = mbar)
        pressure_msl::numeric(8, 2)                     as pressao_mb,

        -- Radiação solar de ondas curtas (W/m²)
        shortwave_radiation::numeric(8, 2)              as radiacao_wm2

    from source
    where "time" is not null

)

select * from cleaned
