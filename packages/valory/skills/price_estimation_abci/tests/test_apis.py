# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Test various price apis."""

from typing import Dict, List
from typing import OrderedDict as OrderedDictType
from typing import Tuple, Union
from unittest.mock import MagicMock

import pytest
import requests
from aea.skills.base import Skill, SkillContext
from aea_test_autonomy.docker.base import skip_docker_tests

from packages.valory.skills.price_estimation_abci.models import PriceApi, RandomnessApi
from packages.valory.skills.price_estimation_abci.tests.helpers.docker import (
    DEFAULT_JSON_SERVER_ADDR,
    DEFAULT_JSON_SERVER_PORT,
)


MOCKED_APIS_URL = f"{DEFAULT_JSON_SERVER_ADDR}:{DEFAULT_JSON_SERVER_PORT}"


price_apis = pytest.mark.parametrize(
    "api_specs",
    [
        [
            ("url", f"{MOCKED_APIS_URL}/coingecko"),
            ("api_id", "coingecko"),
            ("headers", []),
            ("parameters", [["ids", "bitcoin"], ["vs_currencies", "usd"]]),
            ("response_key", "bitcoin:usd"),
        ],
        [
            ("url", f"{MOCKED_APIS_URL}/kraken"),
            ("api_id", "kraken"),
            ("response_key", "result:XXBTZUSD:b"),
            ("response_index", 0),
            ("headers", []),
            ("parameters", [["pair", "BTCUSD"]]),
        ],
        [
            ("url", f"{MOCKED_APIS_URL}/coinbase"),
            ("api_id", "coinbase"),
            ("response_key", "data:amount"),
            ("headers", []),
            ("parameters", []),
        ],
        [
            ("url", f"{MOCKED_APIS_URL}/binance"),
            ("api_id", "binance"),
            ("headers", []),
            ("parameters", [["symbol", "BTCUSDT"]]),
            ("response_key", "price"),
        ],
    ],
)

randomness_apis = pytest.mark.parametrize(
    "api_specs",
    [
        [
            ("url", f"{MOCKED_APIS_URL}/cloudflare"),
            ("api_id", "cloudflare"),
            ("headers", []),
            ("parameters", []),
        ],
        [
            ("url", f"{MOCKED_APIS_URL}/protocollabs1"),
            ("api_id", "protocollabs1"),
            ("headers", []),
            ("parameters", []),
        ],
        [
            ("url", f"{MOCKED_APIS_URL}/protocollabs2"),
            ("api_id", "protocollabs2"),
            ("headers", []),
            ("parameters", []),
        ],
        [
            ("url", f"{MOCKED_APIS_URL}/protocollabs3"),
            ("api_id", "protocollabs3"),
            ("headers", []),
            ("parameters", []),
        ],
    ],
)


class DummyMessage:  # pylint: disable=too-few-public-methods
    """Dummy api specs class."""

    body: bytes

    def __init__(self, body: bytes) -> None:
        """Initializes DummyMessage"""
        self.body = body


def make_request(api_specs: Dict) -> requests.Response:
    """Make request using api specs."""

    if api_specs["method"] == "GET":
        if api_specs["parameters"]:
            api_specs["url"] = api_specs["url"] + "?"
            for key, val in api_specs["parameters"]:
                api_specs["url"] += f"{key}={val}&"
            api_specs["url"] = api_specs["url"][:-1]
        return requests.get(url=api_specs["url"], headers=dict(api_specs["headers"]))

    raise ValueError(f"Unknown method {api_specs['method']}")


@pytest.mark.usefixtures("start_mock_apis")
@skip_docker_tests
class TestApis:
    """Tests for the APIs."""

    @staticmethod
    @price_apis
    def test_price_api(
        api_specs: List[Tuple[str, Union[str, List[OrderedDictType[str, str]]]]]
    ) -> None:
        """Test various price api specs."""

        api = PriceApi(
            name="price_api",
            skill_context=SkillContext(MagicMock(), Skill(MagicMock())),
            currency_id="BTC",
            convert_id="USD",
            method="GET",
            response_type="float",
            retries=5,
            **dict(api_specs),
        )

        response = make_request(api.get_spec())
        observation = api.process_response(DummyMessage(response.content))  # type: ignore
        assert isinstance(observation, float)
        assert observation > 0

    @staticmethod
    @randomness_apis
    def test_randomness_api(api_specs: List[Tuple[str, Union[str, List]]]) -> None:
        """Test various price api specs."""

        api = RandomnessApi(
            name="randomness_api",
            skill_context=SkillContext(MagicMock(), Skill(MagicMock())),
            method="GET",
            response_type="dict",
            retries=5,
            **dict(api_specs),
        )

        response = make_request(api.get_spec())
        value = api.process_response(DummyMessage(response.content))  # type: ignore
        assert isinstance(value, dict)
        assert all([key in value for key in ["randomness", "round"]])
