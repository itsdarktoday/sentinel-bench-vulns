// Benchmark: unchecked low-level call return (Slither unchecked-send)
pragma solidity ^0.8.0;

contract Refunder {
    mapping(address => uint256) public pending;

    // VULN: .call{value:} return not checked
    function refund(address payable to) external {
        uint256 amount = pending[to];
        pending[to] = 0;
        to.call{value: amount}("");
    }
}
