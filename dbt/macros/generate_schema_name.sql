-- Garante que dbt use o nome exato do schema configurado
-- sem prefixar com o schema do target (ex: evita "public_silver")
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
