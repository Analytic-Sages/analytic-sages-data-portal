{% macro iceberg_relation(schema, identifier, catalog='iceberg') -%}
    {# spark_catalog IS the same Hadoop warehouse (set at submit level),
       so two-level names resolve to the same tables and the metadata
       lives in GCS, not in the batch's throwaway Derby. #}
    {{ schema }}.{{ identifier }}
{%- endmacro %}
