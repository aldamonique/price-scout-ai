{% macro bronze_files() -%}
    {%- if target.name == 'cloud' -%}
        s3://{{ env_var('LAKE__BUCKET', 'price-scout-lake') }}/bronze/*.json
    {%- else -%}
        bronze/*.json
    {%- endif -%}
{%- endmacro %}
