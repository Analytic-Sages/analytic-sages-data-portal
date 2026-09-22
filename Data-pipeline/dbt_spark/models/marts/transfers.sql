{{ 
    config(
        materialized='incremental', 
        file_format='iceberg',
        incremental_strategy='merge',
        unique_key=['block_slot', 'tx_signature', 'source', 'destination', 'mint'],
        partition_by=['block_date'],
        on_schema_change='sync_all_columns'
    ) 
}}

with transfers as (
    select * from {{ ref('stg_token_transfers') }}
    {% if is_incremental() %}
    -- only new blocks since last max, avoids re-querying entire lake.solana.transfers
    where block_slot > (select coalesce(max(block_slot), 0) from {{ this }})
    {% endif %}
),
token as (
    select * from {{ ref('stg_tokens') }}
),

add_metadata as (
    select 
    t.*,
    t2.name,
    t2.symbol
    from transfers t
    left join token t2 ON t.mint = t2.mint
)

{% if is_incremental() %}
-- late token update: re-emit existing transfers where symbol was null but token now has it
-- must select NEW symbol/name from token, not old null t.*
, needs_update as (
    select
        t.block_slot, t.block_hash, t.block_timestamp, t.block_date, t.tx_signature,
        t.source, t.destination, t.authority, t.value, t.decimals, t.value_normalized, t.mint,
        t.mint_authority, t.fee, t.fee_decimals, t.memo, t.transfer_type, t._ingested_at,
        tok.name, tok.symbol
    from {{ this }} t
    join token tok on t.mint = tok.mint
    where t.symbol is null and tok.symbol is not null
)
select * from add_metadata
union all
select * from needs_update
{% else %}
select * from add_metadata
{% endif %}