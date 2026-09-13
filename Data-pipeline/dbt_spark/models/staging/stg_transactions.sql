with source as (
    select * from {{ iceberg_relation('solana', 'transactions') }}
),

renamed as (
    select
        block_slot,
        block_hash,
        block_timestamp,
        cast(block_timestamp as date) as block_date,
        recent_block_hash,
        signature,
        index,
        fee,
        status,
        err,
        compute_units_consumed,
        accounts,
        log_messages,
        balance_changes,
        pre_token_balances,
        post_token_balances,
        _ingested_at
    from source
    where block_slot is not null
      and index is not null
)

select * from renamed
