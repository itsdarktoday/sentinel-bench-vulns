# Sentinel Benchmark — Vulnerable Contracts
Three intentionally vulnerable contracts used to benchmark Sentinel's autonomous hunter.
- reentrancy.sol: withdraw() external call before state update (no reentrancy guard)
- access_control.sol: mint()/setOwner() with no onlyOwner
- oracle_manipulation.sol: setPriceFeed() attacker-controllable oracle
