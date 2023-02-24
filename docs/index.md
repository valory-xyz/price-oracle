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

In order to run a local demo of the Price Oracle service with a Hardhat node:

1. [Set up your system](https://docs.autonolas.network/open-autonomy/guides/set_up/) to work with the Open Autonomy framework. We recommend that you use these commands:

    ```bash
    mkdir your_workspace && cd your_workspace
    touch Pipfile && pipenv --python 3.10 && pipenv shell

    pipenv install open-autonomy[all]==0.9.1
    autonomy init --remote --ipfs --reset --author=your_name
    ```

2. Fetch the Price Oracle service (Hardhat flavour).

	```bash
<<<<<<< HEAD
<<<<<<< HEAD
	autonomy fetch valory/oracle_hardhat:0.1.0:bafybeih6eqd3324mlumtimugsm7sl5beb6hrpsk5b3x4mpx6ou5eipplhy --service
=======
	autonomy fetch valory/oracle_hardhat:0.1.0:bafybeibo4lwiq3lmvkfzsqaa5uwbcdwtjmv257af33xkgalvlnd2tqnlxi --service
>>>>>>> 754b4ecd9 (http_server_data skill to expose service data over http. rice_estimation_abci updated to store service data on shared_state)
=======
	autonomy fetch valory/oracle_hardhat:0.1.0:bafybeicfrzs3ix352my5uipl6sqn4zzix7mfu4yk5ux22apl77l5j66sqi --service
>>>>>>> e691a693c (some docstring fixes)
	```

3. Build the Docker image of the service agents

	```bash
	cd oracle_hardhat
	autonomy build-image
	```

4. Prepare the `keys.json` file containing the wallet address and the private key for each of the agents.

    ??? example "Generating an example `keys.json` file"

        <span style="color:red">**WARNING: Use this file for testing purposes only. Never use the keys or addresses provided in this example in a production environment or for personal use.**</span>

        ```bash
        cat > keys.json << EOF
        [
          {
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "private_key": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
          },
          {
            "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "private_key": "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
          },
          {
            "address": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
            "private_key": "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"
          },
          {
            "address": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
            "private_key": "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"
          }
        ]
        EOF
        ```

5. Build the service deployment.
   
    The `--use-hardhat` flag below, adds an image with a Hardhat node containing some default smart contracts 
    (e.g., a [Safe](https://safe.global/)) to the service deployment. You can use any image with a Hardhat node, 
    instead of the default `valory/open-autonomy-hardhat`. To achieve that, you need to modify the environment variable 
    `HARDHAT_IMAGE_NAME`.

    The Price Oracle service demo requires the Autonolas Protocol registry contracts in order to run. 
    We conveniently provide the image `valory/autonolas-registries` containing them. 
    Therefore, build the deployment as follows:

    ```bash
    export HARDHAT_IMAGE_NAME=valory/autonolas-registries
    autonomy deploy build keys.json --aev -ltm --use-hardhat
    ```

6. Run the service.

    ```bash
    cd abci_build
    autonomy deploy run
    ```

    You can cancel the local execution at any time by pressing ++ctrl+c++.

To understand the deployment process better, follow the deployment guide [here](https://docs.autonolas.network/open-autonomy/guides/deploy_service/).

## Build

1. Fork the [OracleKit repository](https://github.com/valory-xyz/price-oracle).
2. Make the necessary adjustments to tailor the service to your needs. This could include:
    * Adjust configuration parameters (e.g., in the `service.yaml` file).
    * Expand the service finite-state machine with your custom states.
3. Run your service as detailed above.

!!! tip "Looking for help building your own?"

    Refer to the [Autonolas Discord community](https://discord.com/invite/z2PT65jKqQ), or consider ecosystem services like [Valory Propel](https://propel.valory.xyz) for the fastest way to get your first autonomous service in production.