
with source as (
    select * from {{ iceberg_relation('solana', 'transfers') }}
),

renamed as (
    select
        block_slot,
        block_hash,
        block_timestamp,
        cast(block_timestamp as date) as block_date,
        tx_signature,
        source,
        destination,
        authority,
        value,
        decimals,
        value / power(10, decimals) as value_normalized,
        mint,
        mint_authority,
        fee,
        fee_decimals,
        memo,
        transfer_type,
        _ingested_at
    from source
    where block_slot is not null
      and tx_signature is not null
      and source is not null
      and destination is not null
      and mint is not null
)

select * from renamed
