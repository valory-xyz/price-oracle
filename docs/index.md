![OracleKit](images/oraclekit.svg){ align=left }
The OracleKit is aimed at building services providing data streams onto the blockchain. For example, The Price Oracle is an {{agent_service_link}} that provides an estimation of the Bitcoin price (USD) based on observations coming from different data sources. In the live demo, the service is using observations from [Kraken](https://www.kraken.com/), [CoinGecko](https://www.coingecko.com/), [Coinbase](https://www.coinbase.com/), and [Binance](https://www.binance.com/).

Each agent collects an observation from one of the data sources above and
shares it with the rest of the agents through the consensus gadget.

Once all the observations are collected, each agent
computes locally a deterministic function that aggregates the observations shared by all the
agents, and obtains an estimate of the current Bitcoin price. The live demo is currently using the
average of the observed values, but other functions, such as the median, can also be considered.
The estimates made by all the agents are shared, and a consensus is reached when one of them
obtains at least $\lceil(2N + 1) / 3\rceil$ votes, where $N$ is the number of agents in the service.

Once the consensus on an estimate has been reached, it is settled in the Polygon chain.
Note that the service is secured through a multisig contract. This means that, in order to settle the
Bitcoin estimate in Polygon, the agents execute a multi-signature transaction that requires at least $\lceil(2N + 1) / 3\rceil$ agents signatures to be accepted.

Finally, a random agent (keeper) is voted among the agents in the service to submit the transaction, and the service starts its cycle again.

## Demo

Once you have {{set_up_system}} to work with the Open Autonomy framework, you can run a local demo of the Price Oracle with a Hardhat node as follows:

1. Fetch the Price Oracle service (Hardhat flavour).

	```bash
	autonomy fetch valory/oracle_hardhat:0.1.0:bafybeiedzmt64oi3ghoeodjscku5ol5ctpqbwn4ie2md5gnz5tfudd637i --service
	```

2. Build the Docker image of the service agents

	```bash
	cd oracle_hardhat
	autonomy build-image
	```

3. Prepare the `keys.json` file containing the wallet address and the private key for each of the agents.

    ??? example "Example of a `keys.json` file"

        <span style="color:red">**WARNING: Use this file for testing purposes only. Never use the keys or addresses provided in this example in a production environment or for personal use.**</span>

        ```json
        [
          {
              "address": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
              "private_key": "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"
          },
          {
              "address": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
              "private_key": "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
          },
          {
              "address": "0x976EA74026E726554dB657fA54763abd0C3a0aa9",
              "private_key": "0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e"
          },
          {
              "address": "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955",
              "private_key": "0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356"
          }
        ]
        ```

4. Build the service deployment.

    ```bash
    autonomy deploy build keys.json --aev
    ```

5. Run the service.

      1. In a separate terminal, run a Hardhat node. We provide a pre-configured Docker image for testing.

		```bash
		docker run -p 8545:8545 -it valory/open-autonomy-hardhat:0.1.0
		```

      2. Once the Hardhat node is up and running, run the service deployment.

		```bash
		cd abci_build
		autonomy deploy run
		```

		You can cancel the local execution at any time by pressing ++ctrl+c++.

## Build

1. Fork the [OracleKit repository](https://github.com/valory-xyz/price-oracle).
2. Make the necessary adjustments to tailor the service to your needs. This could include:
    * Adjust configuration parameters (e.g., in the `service.yaml` file).
    * Expand the service finite-state machine with your custom states.
3. Run your service as detailed above.

!!! tip "Looking for help building your own?"

    Refer to the [Autonolas Discord community](https://discord.com/invite/z2PT65jKqQ), or consider ecosystem services like [Valory Propel](https://propel.valory.xyz) for the fastest way to get your first autonomous service in production.