// Benchmark: weak randomness from block values (Slither weak-prng)
pragma solidity ^0.8.0;

contract Lottery {
    address public winner;
    uint256 public prize;

    // VULN: randomness from block.timestamp / blockhash
    function drawLottery() external {
        uint256 r = uint256(keccak256(abi.encodePacked(block.timestamp, blockhash(block.number - 1)))) % 100;
        if (r == 42) {
            winner = msg.sender;
            payable(msg.sender).transfer(prize);
        }
    }

    receive() external payable {}
}
