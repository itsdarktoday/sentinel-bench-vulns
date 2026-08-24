// Benchmark: oracle price read from attacker-controllable source
pragma solidity ^0.8.0;

interface IAggregator {
    function latestAnswer() external view returns (int256);
}

contract LendingPool {
    IAggregator public priceFeed;
    mapping(address => uint256) public collateral;

    // VULN: priceFeed address is settable by anyone (no access control)
    function setPriceFeed(address feed) external {
        priceFeed = IAggregator(feed);
    }

    function liquidate(address user) external {
        int256 price = priceFeed.latestAnswer();   // depends on attacker feed
        require(collateral[user] * uint256(price) > 0, "safe");
    }
}
