with source as (
    select * from {{ iceberg_relation('solana', 'tokens') }}
),

renamed as (
    select
        block_slot,
        block_hash,
        block_timestamp,
        tx_signature,
        retrieval_timestamp,
        is_nft,
        mint,
        update_authority,
        name,
        symbol,
        uri,
        seller_fee_basis_points,
        primary_sale_happened,
        is_mutable,
        _ingested_at
    from source
    where mint is not null
)

select * from renamed
