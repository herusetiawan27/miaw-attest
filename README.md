# MiawAttest — Web-Claim Checker on GenLayer

An original Intelligent Contract for [GenLayer](https://genlayer.com) that checks
a claim against a web page: give it a claim and a URL, and a jury of AI validators
reads the page and returns a verdict — **supported**, **refuted**, or **unclear** —
plus the verbatim quote it relied on.

Built for GenLayer Season 2 (Builder track).

## How it works

- `attest(claim, url)` (write) — validators fetch the URL, read the page, and
  judge whether the claim is supported, refuted, or unclear. The verdict and
  quote are stored on-chain.
- `verdict(claim)` (view) — returns the stored verdict for a claim.
- `claims()` (view) — lists all attested claims.

The contract uses GenLayer's non-deterministic execution: the leader fetches the
page and proposes a verdict, then a jury of validators independently re-checks
it (Optimistic Democracy consensus).

## Deployment

- **StudioNet (live, gasless):** `0xAeE918631eDDCa615e675c70c5EDC363fCB0eEa2`
  - Deploy tx: `0xf0ae2be403e76aaff1f331d4080e3a84dce40367a3b6247f98b4b95c8c6adf29`
  - Deployer: `0x8E037d7BAde06A24a2432117C35c31101EFa3081`
- **Bradbury testnet:** pending — the faucet requires holding 0.01 ETH on
  Ethereum mainnet, so the Bradbury deploy is on hold until testnet GEN is
  available. The same contract deploys unchanged.

## Test

```bash
pip install genlayer-test genvm-linter
genlayer-test test_miaw_attest.py
```

Lint + 8/8 direct-mode tests pass.

## License

MIT
