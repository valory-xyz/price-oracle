# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Integration tests for the valory/apy_estimation_abci skill."""

from typing import Tuple, cast

import pytest

from tests.fixture_helpers import UseGnosisSafeHardHatNet
from tests.test_agents.base import BaseTestEnd2EndNormalExecution


# check log messages of the happy path
CHECK_STRINGS_LIST = [
    "Entered in the 'tendermint_healthcheck' behaviour state",
    "'tendermint_healthcheck' behaviour state is done",
]

states_checks_config = {
    "registration": {
        "state_name": "registration",
        "extra_logs": (),
        "only_at_first_period": True,
    },
    "collect_history": {
        "state_name": "collect_history",
        "extra_logs": (
            "Retrieved block: ",
            "Retrieved ETH price for block ",
            "Retrieved pool data for block ",
        ),
        "only_at_first_period": True,
    },
    "transform": {
        "state_name": "transform",
        "extra_logs": ("Data have been transformed:\n",),
        "only_at_first_period": True,
    },
    "preprocess": {
        "state_name": "preprocess",
        "extra_logs": ("Data have been preprocessed.",),
        "only_at_first_period": True,
    },
    "randomness": {
        "state_name": "randomness",
        "extra_logs": (),
        "only_at_first_period": True,
    },
    "optimize": {
        "state_name": "optimize",
        "extra_logs": ("Optimization has finished. Showing the results:\n",),
        "only_at_first_period": True,
    },
    "train": {
        "state_name": "train",
        "extra_logs": ("Training has finished.",),
        "only_at_first_period": True,
    },
    "test": {
        "state_name": "test",
        "extra_logs": ("Testing has finished. Report follows:\n",),
        "only_at_first_period": True,
    },
    "full_train": {
        "state_name": "train",
        "extra_logs": ("Training has finished.",),
        "only_at_first_period": True,
    },
    "estimate": {
        "state_name": "estimate",
        "extra_logs": ("Got estimate of APY for ",),
        "only_at_first_period": False,
    },
    "cycle_reset": {
        "state_name": "cycle_reset",
        "extra_logs": ("Finalized estimate: ",),
        "only_at_first_period": False,
    },
}


def build_check_strings() -> None:
    """Build check strings based on the `states_checks_config`."""
    for period in (0, 1):
        for _, config in states_checks_config.items():
            if period == 0:
                CHECK_STRINGS_LIST.append(
                    f"Entered in the '{config['state_name']}' round for period {period}"
                )

                for log in cast(Tuple[str], config["extra_logs"]):
                    CHECK_STRINGS_LIST.append(log)

                CHECK_STRINGS_LIST.append(f"'{config['state_name']}' round is done")

            elif not config["only_at_first_period"]:
                CHECK_STRINGS_LIST.append(
                    f"Entered in the '{config['state_name']}' round for period {period}"
                )


build_check_strings()
CHECK_STRINGS = tuple(CHECK_STRINGS_LIST)


class BaseTestABCIAPYEstimationSkillNormalExecution(BaseTestEnd2EndNormalExecution):
    """Base class for the APY estimation e2e tests."""

    agent_package = "valory/apy_estimation:0.1.0"
    skill_package = "valory/apy_estimation_abci:0.1.0"
    check_strings = CHECK_STRINGS
    KEEPER_TIMEOUT = 120
    wait_to_finish = 240


class TestABCIAPYEstimationSingleAgent(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test the ABCI apy_estimation_abci skill with only one agent."""

    NB_AGENTS = 1


@pytest.mark.skip
class TestABCIAPYEstimationTwoAgents(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI apy_estimation_abci skill with two agents."""

    NB_AGENTS = 2


@pytest.mark.skip
class TestABCIAPYEstimationFourAgents(
    BaseTestABCIAPYEstimationSkillNormalExecution,
    UseGnosisSafeHardHatNet,
):
    """Test that the ABCI apy_estimation_abci skill with four agents."""

    NB_AGENTS = 4
