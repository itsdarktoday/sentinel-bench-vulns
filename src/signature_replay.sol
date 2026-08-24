// Benchmark: signature replay (Slither signed-data / missing nonce+chainId)
pragma solidity ^0.8.0;

contract Claimable {
    mapping(address => bool) public claimed;

    // VULN: ecrecover without nonce / chainId / domain separator -> replayable
    function claim(uint256 amount, uint8 v, bytes32 r, bytes32 s) external {
        bytes32 hash = keccak256(abi.encodePacked(msg.sender, amount));
        address signer = ecrecover(hash, v, r, s);
        require(signer == msg.sender, "bad sig");
        require(!claimed[msg.sender], "already");
        claimed[msg.sender] = true;
        payable(msg.sender).transfer(amount);
    }

    receive() external payable {}
}
