# Solana General Transfer Indexer (HyperIndex)

Per-transfer indexer for **all** SPL Token + Token-2022 transfers on Solana mainnet.

- **Programs:** `SplToken TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA` + `Token2022 TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`
- **Instructions:** `transfer@0x03`, `transferChecked@0x0c`, `transferCheckedWithFee@0x1a01` (Token-2022 only)
- **Mints:** all (no `where` filter). Plain `transfer` resolves `mint` via `accountActivity token.mint`.

## What it stores

`Transfer` per row: `mint`, `sender` (source `token.owner`, may be ""), `receiver` (dest `token.owner`), `source`/`destination` token accounts, `amount` (raw u64), `decimals`, `normalizedAmount`, `fee` (if withFee), `instruction`, `program`, `depth` (0 top-level), `isInner`, `slot`, `txSignature`, `blockTime`.

ID = `slot-txIndex-path` (e.g. `447500001-5-0.1`).

## Setup

```bash
cd Data-pipeline/indexer
pnpm codegen
pnpm exec tsc --noEmit
# token from https://app.envio.dev/api-tokens
echo "ENVIO_API_TOKEN=..." > .env
# if :5433 already used or schema changed:
echo "ENVIO_PG_SCHEMA=solana_transfer_raw" >> .env
pnpm dev # needs Docker
```

- `start_slot` is slot number (head `curl https://solana.hypersync.xyz/height` → ~448M). Before earliest (~403M) it starts at earliest without error.
- Schema changed from aggregates → need new PG schema or reset: `ENVIO_PG_SCHEMA=solana_transfer_raw` or `docker volume rm` if you want to wipe.
