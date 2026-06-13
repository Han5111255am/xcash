"""Tron 运行时常量。"""

# Runtime VaultSlot 合约调用交易的 fee_limit，单位 sun。
# fee_limit 是异常情况下可燃烧 TRX 的硬上限，不是常规预算；广播前仍会先证明
# Energy/Bandwidth 充足。这里统一限制为 5 TRX，不按 collect/deployVaultSlot 分档。
TRON_VAULT_SLOT_FEE_LIMIT = 5_000_000
