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

    pipenv install open-autonomy[all]==0.10.0.post2
    autonomy init --remote --ipfs --reset --author=your_name
    ```

2. Fetch the Price Oracle service (Hardhat flavour).

	```bash
	autonomy fetch valory/oracle_hardhat:0.1.0:bafybeig2r7wr3zlgjn5zu7pppr42etmmj7ih6sat6hjkjvfbbhn73koeji --service
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

## Querying the service

Querying autonomous services can become very simple by using the 
[Open Autonomy Client SDK](https://github.com/valory-xyz/open-autonomy-client).
This is a library that helps to query multi-agent systems built with the Open Autonomy framework 
It provides a simplified approach for making requests to a service as if it were a single endpoint.
The SDK queries multiple agents in the background to retrieve information and returns a result that is presumed to be reached by consensus among the agents.

Let's take a look at a simple example, using the SDK. First of all we need to make sure 
that we have the necessary requirements installed:

```bash
pip install open-autonomy-client
pip install aiohttp
```

Having installed the requirements and while running the hardhat demo above, you can use this simple script 
to get a result for which the agents have reached consensus on:

```python
import asyncio
import json
from open_autonomy_client.client import Client


PUB_KEYS_LIST = ['0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266', '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
                 '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC', '0x90F79bf6EB2c4f870365E785982E1f101E93b906']
AGENTS_URLS_LIST = [
    f"http://127.0.0.1:{i}"
    for i in range(8000, 8000 + len(PUB_KEYS_LIST))
]


async def fetch():
    client = Client(urls=AGENTS_URLS_LIST, keys=PUB_KEYS_LIST)
    agents_data = await client.fetch()
    print(json.dumps(agents_data, indent=4))

if __name__ == '__main__':
  asyncio.run(fetch())
```

Let's take a look at this script step by step:

1. We import the `asyncio` library, because the Client SDK queries the agents in an asynchronous way 
   in order to save time. The `json` library is not necessary, but helps us format the data before printing them 
   for this demo. The `open_autonomy_client` is the SDK, and the `Client` is the class that we are going to use 
   to fetch the agents' data.
2. We specify a list with the public keys and the URLs of the agents that we would like to query. 
   These are the only parameters that need to be changed in this script in order to run it for any service.
3. Next, we define an asynchronous function which initializes a client, using the constants above, 
   and calls the `fetch()` method on the instance. Using these two lines of code, we have received the `agents_data`, 
   which we continue to print in a JSON format.
4. We use `asyncio` in order to execute the asynchronous function that we defined.

An example result after running the above script should look like the following:

```json
{
    "estimate": 28079.105,
    "observations": {
        "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC": 28157.41,
        "0x70997970C51812dc3A010C7d01b50e0d17dc79C8": 28000.8,
        "0x90F79bf6EB2c4f870365E785982E1f101E93b906": 27976.56,
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266": 28206.0
    },
    "period_count": 5,
    "prev_tx_hash": "0x7ba926e8de2919552f681de97efde61fb0f89fda64a8d375b2206abebf75dab2",
    "unit": "BTC:USD"
}
```

## Build

1. Fork the [OracleKit repository](https://github.com/valory-xyz/price-oracle).
2. Make the necessary adjustments to tailor the service to your needs. This could include:
    * Adjust configuration parameters (e.g., in the `service.yaml` file).
    * Expand the service finite-state machine with your custom states.
3. Run your service as detailed above.

!!! tip "Looking for help building your own?"

    Refer to the [Autonolas Discord community](https://discord.com/invite/z2PT65jKqQ), or consider ecosystem services like [Valory Propel](https://propel.valory.xyz) for the fastest way to get your first autonomous service in production.