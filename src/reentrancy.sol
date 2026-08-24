// Benchmark: classic reentrancy + missing guard
pragma solidity ^0.8.0;

interface IToken {
    function transfer(address, uint256) external returns (bool);
    function transferFrom(address, address, uint256) external returns (bool);
}

contract ReentrantVault {
    mapping(address => uint256) public balances;
    IToken public token;

    function deposit(uint256 amount) external {
        balances[msg.sender] += amount;
        token.transferFrom(msg.sender, address(this), amount);
    }

    // VULN: external, nonpayable, calls external token.transfer BEFORE state update
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "insufficient");
        token.transfer(msg.sender, amount);   // external call -> reentrancy
        balances[msg.sender] -= amount;        // state update AFTER
    }

    function flashLoan(uint256 amount, address receiver) external {
        token.transfer(receiver, amount);
        // callback omitted for brevity
    }
}
