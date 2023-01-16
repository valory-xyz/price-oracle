# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Tests for valory/price_estimation_abci skill."""
import logging
from pathlib import Path
from typing import Any, Generator

import docker
import pytest
from aea_test_autonomy.docker.base import launch_image
from aea_test_autonomy.helpers.contracts import get_register_contract

from packages.valory.contracts.offchain_aggregator.tests.test_contract import (
    PACKAGE_DIR as OFFCHAIN_AGGREGATOR_PACKAGE,
)
from packages.valory.skills.abstract_round_abci.test_tools.integration import (
    HardHatHelperIntegration,
)
from packages.valory.skills.price_estimation_abci.tests.helpers.docker import (
    DEFAULT_JSON_SERVER_ADDR,
    DEFAULT_JSON_SERVER_PORT,
    MockApis,
)
from packages.valory.skills.transaction_settlement_abci.test_tools.integration import (
    _TxHelperIntegration,
)


class GnosisIntegrationBaseCase(  # pylint: disable=too-many-ancestors
    _TxHelperIntegration, HardHatHelperIntegration
):
    """Base test class for integration tests in a Hardhat environment, with Gnosis deployed."""

    # TODO change this class to use the `HardHatGnosisBaseTest` instead of `HardHatAMMBaseTest`.

    path_to_skill = PACKAGES_DIR = Path(__file__).parents[2]

    @classmethod
    def setup_class(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup_class()

        # register offchain aggregator contract
        _ = get_register_contract(OFFCHAIN_AGGREGATOR_PACKAGE)


@pytest.fixture(scope="module")
def start_mock_apis(
    timeout: int = 3,
    max_attempts: int = 200,
) -> Generator:
    """Start a mocked APIs instance."""
    client = docker.from_env()
    logging.info(f"Launching the mocked APIs on port {DEFAULT_JSON_SERVER_PORT}")
    image = MockApis(
        client,
        addr=DEFAULT_JSON_SERVER_ADDR,
        port=DEFAULT_JSON_SERVER_PORT,
    )
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)
