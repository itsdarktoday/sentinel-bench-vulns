// Benchmark: tx.origin authorization (Slither tx-origin)
pragma solidity ^0.8.0;

contract Wallet {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // VULN: authorization via tx.origin (phishable)
    function transferTo(address to, uint256 amount) external {
        require(tx.origin == owner, "not owner");
        payable(to).transfer(amount);
    }
}
