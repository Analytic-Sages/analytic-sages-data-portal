with source as (
    select * from {{ iceberg_relation('solana', 'blocks') }}
),

renamed as (
    select
        block_slot,
        block_hash,
        block_timestamp,
        cast(block_timestamp as date) as block_date,
        previous_block_hash,
        parent_slot,
        _ingested_at
    from source
    where block_slot is not null
)

select * from renamed
