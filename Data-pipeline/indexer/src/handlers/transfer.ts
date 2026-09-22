import { indexer } from "envio";

// General Solana transfer indexer — per-transfer rows, only TOKEN_TRANSFERS_SCHEMA columns

const fields = {
  instruction: ["accounts", "args", "path"] as const,
  transaction: ["signature", "transactionIndex"] as const,
  accountActivity: ["token.mint", "token.decimals"] as const,
  block: ["time", "hash"] as const,
} as const;

function makeId(instruction: any): string {
  return `${instruction.block.slot}-${instruction.transaction.transactionIndex}-${instruction.path.join(".")}`;
}

async function handlePlain({ instruction, context }: any) {
  const mint: string | undefined =
    (instruction.accounts.source as any)?.activity?.token?.mint ??
    (instruction.accounts.destination as any)?.activity?.token?.mint;
  if (!mint) return;
  const amount: bigint = instruction.args.amount as bigint;
  const decimals: number =
    (instruction.accounts.source as any)?.activity?.token?.decimals ??
    (instruction.accounts.destination as any)?.activity?.token?.decimals ??
    6;
  const srcAcc: any = instruction.accounts.source;
  const dstAcc: any = instruction.accounts.destination;
  const authAcc: any = instruction.accounts.authority;
  context.Transfer.set({
    id: makeId(instruction),
    block_slot: BigInt(instruction.block.slot),
    block_hash: (instruction.block as any)?.hash ?? null,
    block_timestamp: BigInt(Number((instruction.block as any)?.time ?? 0)),
    tx_signature: instruction.transaction.signature as string,
    source: srcAcc.address as string,
    destination: dstAcc.address as string,
    authority: authAcc?.address ?? null,
    value: amount,
    decimals,
    mint,
    mint_authority: null,
    fee: null,
    fee_decimals: null,
    memo: null,
    transfer_type: "transfer",
  });
}

async function handleChecked({ instruction, context }: any) {
  const mint: string = instruction.accounts.mint.address as string;
  const amount: bigint = instruction.args.amount as bigint;
  const decimals: number = instruction.args.decimals as number;
  const srcAcc: any = instruction.accounts.source;
  const dstAcc: any = instruction.accounts.destination;
  const authAcc: any = instruction.accounts.authority;
  context.Transfer.set({
    id: makeId(instruction),
    block_slot: BigInt(instruction.block.slot),
    block_hash: (instruction.block as any)?.hash ?? null,
    block_timestamp: BigInt(Number((instruction.block as any)?.time ?? 0)),
    tx_signature: instruction.transaction.signature as string,
    source: srcAcc.address as string,
    destination: dstAcc.address as string,
    authority: authAcc?.address ?? null,
    value: amount,
    decimals,
    mint,
    mint_authority: null,
    fee: null,
    fee_decimals: null,
    memo: null,
    transfer_type: "transferChecked",
  });
}

async function handleCheckedWithFee({ instruction, context }: any) {
  const mint: string = instruction.accounts.mint.address as string;
  const amount: bigint = instruction.args.amount as bigint;
  const decimals: number = instruction.args.decimals as number;
  const fee: bigint = instruction.args.fee as bigint;
  const srcAcc: any = instruction.accounts.source;
  const dstAcc: any = instruction.accounts.destination;
  const authAcc: any = instruction.accounts.authority;
  context.Transfer.set({
    id: makeId(instruction),
    block_slot: BigInt(instruction.block.slot),
    block_hash: (instruction.block as any)?.hash ?? null,
    block_timestamp: BigInt(Number((instruction.block as any)?.time ?? 0)),
    tx_signature: instruction.transaction.signature as string,
    source: srcAcc.address as string,
    destination: dstAcc.address as string,
    authority: authAcc?.address ?? null,
    value: amount,
    decimals,
    mint,
    mint_authority: null,
    fee,
    fee_decimals: null,
    memo: null,
    transfer_type: "transferCheckedWithFee",
  });
}

indexer.onInstruction({ program: "SplToken", instruction: "transfer", fields }, handlePlain);
indexer.onInstruction({ program: "SplToken", instruction: "transferChecked", fields }, handleChecked);
indexer.onInstruction({ program: "Token2022", instruction: "transfer", fields }, handlePlain);
indexer.onInstruction({ program: "Token2022", instruction: "transferChecked", fields }, handleChecked);
indexer.onInstruction({ program: "Token2022", instruction: "transferCheckedWithFee", fields }, handleCheckedWithFee);
