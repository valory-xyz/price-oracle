The Price Oracle service provides an estimation
of the Bitcoin price (USD) based on observations coming from different data sources,
e.g., CoinMarketCap, CoinGecko, Binance and Coinbase.
Each agent collects an observation from one of the data sources above and
shares it with the rest of the agents through the consensus gadget.
Once all the observations are settled, each agent
computes locally a deterministic function that aggregates the observations made by all the
agents, and obtains an estimate of the Bitcoin price. The service currently considers the
average of the observed values, but other functions can be applied (e.g., median).
The local estimates made by all the agents are shared, and
a consensus is reached when one estimate
reaches $\lceil(2n + 1) / 3\rceil$ of the total voting power committed
on the consensus gadget.
Once the consensus on an estimate has been reached, a multi-signature transaction
with $\lceil(2n + 1) / 3\rceil$ of the participants' signatures is settled on the
Ethereum chain.


##Run the code

!!! info
	This section will be added soon.


##Build your own

!!! info
	This section will be added soon.
