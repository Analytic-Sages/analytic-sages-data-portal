{{ config(materialized='table', file_format='iceberg', partition_by=['block_date']) }}

with transfers as (
    select * from {{ ref('stg_token_transfers') }}
),

unified as (
    select block_date, source as wallet, value_normalized, 'sent' as direction
    from transfers
    union all
    select block_date, destination as wallet, value_normalized, 'received' as direction
    from transfers
),

daily as (
    select
        block_date,
        wallet,
        count(*) as transfer_count,
        sum(value_normalized) as total_volume,
        sum(case when direction = 'sent' then value_normalized else 0 end) as sent_volume,
        sum(case when direction = 'received' then value_normalized else 0 end) as received_volume
    from unified
    where wallet is not null
    group by 1, 2
)

select * from daily
