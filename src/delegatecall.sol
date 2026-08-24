// Benchmark: untrusted delegatecall to variable address (Slither controlled-delegatecall)
pragma solidity ^0.8.0;

contract Proxy {
    address public implementation;

    // VULN: delegatecall to a mutable/external address
    function execute(bytes calldata data) external {
        (bool ok, ) = implementation.delegatecall(data);
        require(ok, "fail");
    }

    function setImplementation(address impl) external {
        implementation = impl;
    }
}
