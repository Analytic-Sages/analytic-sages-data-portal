{{ config(materialized='table', file_format='iceberg', partition_by=['block_date']) }}

with transfers as (
    select * from {{ ref('stg_token_transfers') }}
),

daily as (
    select
        block_date,
        mint,
        count(*) as transfer_count,
        sum(value_normalized) as total_volume,
        count(distinct source) as unique_senders,
        count(distinct destination) as unique_receivers
    from transfers
    group by 1, 2
)

select * from daily
