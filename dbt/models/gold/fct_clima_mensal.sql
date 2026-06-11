{{ config(materialized='table') }}

with diario as (

    select * from {{ ref('fct_clima_diario') }}

),

mensal as (

    select
        nome_localidade,
        latitude,
        longitude,
        elevacao_m,
        fuso_horario,
        date_trunc('month', data_medicao)::date             as mes,

        round(sum(chuva_total_mm),              1)          as chuva_total_mm,
        round(avg(chuva_total_mm),              1)          as chuva_media_diaria_mm,
        count(case when chuva_total_mm > 0 then 1 end)      as dias_com_chuva,

        round(avg(temperatura_media_c),         1)          as temperatura_media_c,
        max(temperatura_max_c)                              as temperatura_max_c,
        min(temperatura_min_c)                              as temperatura_min_c,

        round(avg(umidade_media_pct),           1)          as umidade_media_pct,

        round(avg(vento_velocidade_media_ms),   1)          as vento_medio_ms,
        max(vento_rajada_max_ms)                            as vento_rajada_max_ms,

        round(sum(radiacao_total_wm2),          0)          as radiacao_total_wm2,

        count(*)                                            as dias_com_dados

    from diario
    group by
        nome_localidade,
        latitude,
        longitude,
        elevacao_m,
        fuso_horario,
        date_trunc('month', data_medicao)::date

),

com_janelas as (

    select
        *,

        round(sum(chuva_total_mm) over (
            partition by nome_localidade
            order by mes
            rows between 2 preceding and current row
        ), 1)                                               as chuva_acum_3m_mm,

        round(sum(chuva_total_mm) over (
            partition by nome_localidade
            order by mes
            rows between 5 preceding and current row
        ), 1)                                               as chuva_acum_6m_mm,

        round(sum(chuva_total_mm) over (
            partition by nome_localidade
            order by mes
            rows between 11 preceding and current row
        ), 1)                                               as chuva_acum_12m_mm,

        round(
            chuva_total_mm
            - lag(chuva_total_mm) over (
                partition by nome_localidade
                order by mes
            ),
        1)                                                  as chuva_delta_mm,

        round(chuva_total_mm - 120, 1)                     as balanco_hidrico_mm,

        round(avg(chuva_total_mm) over (
            partition by nome_localidade
            order by mes
            rows between 11 preceding and current row
        ), 1)                                               as chuva_media_12m_mm,

        case
            when chuva_total_mm < 80  then 'CRÍTICO'
            when chuva_total_mm < 120 then 'ATENÇÃO'
            else 'NORMAL'
        end                                                 as status_hidrico

    from mensal

),

final as (

    select
        *,
        round(
            case
                when chuva_media_12m_mm > 0
                then (chuva_total_mm - chuva_media_12m_mm) / chuva_media_12m_mm * 100
            end,
        1)                                                  as desvio_vs_media_12m_pct
    from com_janelas

)

select * from final
order by nome_localidade, mes desc
