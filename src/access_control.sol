// Benchmark: missing access control on privileged function
pragma solidity ^0.8.0;

contract AdminMint {
    address public owner;
    mapping(address => uint256) public minted;

    constructor() {
        owner = msg.sender;
    }

    // VULN: no onlyOwner -> anyone can mint
    function mint(address to, uint256 amount) external {
        minted[to] += amount;
    }

    function setOwner(address newOwner) external {
        owner = newOwner;
    }
}
