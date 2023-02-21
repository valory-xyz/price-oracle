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

"""Integration tests for the valory/oracle_abci skill."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Tuple

import pytest

# pylint: skip-file
import requests
from aea.configurations.data_types import PublicId
from aea_test_autonomy.base_test_classes.agents import (
    BaseTestEnd2EndExecution,
    RoundChecks,
)
from aea_test_autonomy.configurations import KEY_PAIRS
from aea_test_autonomy.docker.registries import SERVICE_MULTISIG_1, SERVICE_MULTISIG_2
from aea_test_autonomy.fixture_helpers import abci_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import flask_tendermint  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_addr  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_configuration  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_scope_class  # noqa: F401
from aea_test_autonomy.fixture_helpers import ganache_scope_function  # noqa: F401
from aea_test_autonomy.fixture_helpers import hardhat_addr  # noqa: F401
from aea_test_autonomy.fixture_helpers import hardhat_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import key_pairs  # noqa: F401
from aea_test_autonomy.fixture_helpers import tendermint  # noqa: F401
from aea_test_autonomy.fixture_helpers import tendermint_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    UseACNNode,
    UseGnosisSafeHardHatNet,
    UseRegistries,
    abci_host,
    acn_config,
    acn_node,
    gnosis_safe_hardhat_scope_class,
    gnosis_safe_hardhat_scope_function,
    ipfs_daemon,
    ipfs_domain,
    registries_scope_class,
)

from packages.valory.skills.oracle_deployment_abci.rounds import (
    DeployOracleRound,
    RandomnessOracleRound,
    SelectKeeperOracleRound,
    ValidateOracleRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    EstimateConsensusRound,
    TxHashRound,
)
from packages.valory.skills.registration_abci.rounds import RegistrationStartupRound
from packages.valory.skills.reset_pause_abci.rounds import ResetAndPauseRound
from packages.valory.skills.transaction_settlement_abci.rounds import (
    CollectSignatureRound,
    FinalizationRound,
    RandomnessTransactionSubmissionRound,
    SelectKeeperTransactionSubmissionRoundA,
    ValidateTransactionRound,
)


HAPPY_PATH: Tuple[RoundChecks, ...] = (
    RoundChecks(RegistrationStartupRound.auto_round_id()),
    RoundChecks(RandomnessOracleRound.auto_round_id()),
    RoundChecks(SelectKeeperOracleRound.auto_round_id()),
    RoundChecks(DeployOracleRound.auto_round_id()),
    RoundChecks(ValidateOracleRound.auto_round_id()),
    RoundChecks(EstimateConsensusRound.auto_round_id(), n_periods=2),
    RoundChecks(TxHashRound.auto_round_id(), n_periods=2),
    RoundChecks(RandomnessTransactionSubmissionRound.auto_round_id(), n_periods=2),
    RoundChecks(SelectKeeperTransactionSubmissionRoundA.auto_round_id(), n_periods=2),
    RoundChecks(CollectSignatureRound.auto_round_id(), n_periods=2),
    RoundChecks(FinalizationRound.auto_round_id(), n_periods=2),
    RoundChecks(ValidateTransactionRound.auto_round_id(), n_periods=2),
    RoundChecks(ResetAndPauseRound.auto_round_id(), n_periods=2),
    RoundChecks(CollectObservationRound.auto_round_id(), n_periods=3),
)


def _generate_reset_happy_path(
    n_resets_to_perform: int, reset_tendermint_every: int
) -> Tuple[RoundChecks, ...]:
    """Generate the happy path for checking the oracle combined with the Tendermint reset functionality."""
    happy_path = deepcopy(HAPPY_PATH)
    for round_checks in happy_path:
        if round_checks.name in (
            EstimateConsensusRound.auto_round_id(),
            TxHashRound.auto_round_id(),
            RandomnessTransactionSubmissionRound.auto_round_id(),
            SelectKeeperTransactionSubmissionRoundA.auto_round_id(),
            CollectSignatureRound.auto_round_id(),
            FinalizationRound.auto_round_id(),
            ValidateTransactionRound.auto_round_id(),
            ResetAndPauseRound.auto_round_id(),
            CollectObservationRound.auto_round_id(),
        ):
            round_checks.n_periods = n_resets_to_perform * reset_tendermint_every

    return happy_path


# strict check log messages of the happy path
STRICT_CHECK_STRINGS = (
    "Finalized with transaction hash",
    "Signature:",
    "Data signature:",
    "Got estimate of BTC price in USD:",
    "Got observation of BTC price in USD",
    "Period end",
)
PACKAGES_DIR = Path(__file__).parent.parent.parent.parent.parent


class ABCIPriceEstimationTest(
    BaseTestEnd2EndExecution,
    UseRegistries,
    UseACNNode,
):
    """Test the ABCI oracle skill with only one agent."""

    agent_package = "valory/oracle:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 180
    strict_check_strings = STRICT_CHECK_STRINGS
    happy_path = HAPPY_PATH
    package_registry_src_rel = PACKAGES_DIR
    multisig = SERVICE_MULTISIG_1
    key_pairs_override = KEY_PAIRS[:4]
    _skill_name = PublicId.from_str(skill_package).name
    
    BASE_PORT = 18000

    @classmethod
    def setup_class(cls) -> None:
        """Set the class up."""
        super().setup_class()
        cls.extra_configs = [
            {
                "dotted_path": f"vendor.valory.skills.{cls._skill_name}.models.params.args.setup.safe_contract_address",
                "value": json.dumps([cls.multisig]),
                "type_": "list",
            },
        ]

    def prepare_and_launch(self, nb_nodes: int) -> None:
        """Prepare and launch the agents."""
        # we need to set the correct key pairs, since the 5th agent is registered for the service with 1 agent instance.
        self.key_pairs = self.key_pairs_override
        super().prepare_and_launch(nb_nodes)
    
    def prepare(self, nb_nodes: int) -> None:
        super().prepare(nb_nodes)
        
        for i in range(nb_nodes):
            agent_name = self._get_agent_name(i)
            self.set_agent_context(agent_name)
            port = self.BASE_PORT + i
            self.set_config(dotted_path="vendor.fetchai.connections.http_server.config.port", value=port, type_="int")


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (1,))
class TestABCIPriceEstimationSingleAgent(ABCIPriceEstimationTest):
    """Test the ABCI oracle skill with only one agent."""

    multisig = SERVICE_MULTISIG_2
    key_pairs_override = [KEY_PAIRS[4]]


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (2,))
@pytest.mark.skip(
    "Enable and set the correct multisig and key pairs "
    "when registries image gets updated to include a service with 2 agent instances"
)
class TestABCIPriceEstimationTwoAgents(ABCIPriceEstimationTest):
    """Test the ABCI oracle skill with two agents."""


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (4,))
class TestABCIPriceEstimationFourAgents(ABCIPriceEstimationTest):
    """Test the ABCI oracle skill with four agents."""


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (4,))
class TestAgentCatchup(ABCIPriceEstimationTest):
    """Test that an agent that is launched later can synchronize with the rest of the network"""

    agent_package = "valory/oracle:0.1.0"
    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 200
    restart_after = 45
    strict_check_strings = ()
    happy_path = HAPPY_PATH
    stop_string = f"'{RegistrationStartupRound.auto_round_id()}' round is done with event: Event.DONE"
    n_terminal = 1


@pytest.mark.e2e
@pytest.mark.skip
class TestTendermintReset(TestABCIPriceEstimationFourAgents):
    """Test the ABCI oracle skill with four agents when resetting Tendermint."""

    skill_package = "valory/oracle_abci:0.1.0"
    wait_to_finish = 360
    # run for 4 periods instead of 2
    __n_resets_to_perform = 2
    __reset_tendermint_every = 2
    happy_path = _generate_reset_happy_path(
        __n_resets_to_perform, __reset_tendermint_every
    )
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    # reset every two rounds
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.reset_tendermint_after",
            "value": __reset_tendermint_every,
        },
        {
            "dotted_path": f"{__args_prefix}.observation_interval",
            "value": 15,
        },
    ]


@pytest.mark.e2e
@pytest.mark.skip
class TestTendermintResetInterrupt(TestAgentCatchup):
    """Test the ABCI oracle skill with four agents when an agent gets temporarily interrupted on Tendermint reset."""

    skill_package = "valory/oracle_abci:0.1.0"
    cli_log_options = ["-v", "INFO"]
    wait_before_stop = 100
    wait_to_finish = 300
    restart_after = 1
    __n_resets_to_perform = 3
    __reset_tendermint_every = 2

    # stop for restart_after seconds when resetting Tendermint for the first time (using -1 because count starts from 0)
    stop_string = f"Entered in the '{ResetAndPauseRound.auto_round_id()}' round for period {__reset_tendermint_every - 1}"
    happy_path = _generate_reset_happy_path(
        __n_resets_to_perform, __reset_tendermint_every
    )
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    # reset every `__reset_tendermint_every` rounds
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.reset_tendermint_after",
            "value": __reset_tendermint_every,
        },
        {
            "dotted_path": f"{__args_prefix}.observation_interval",
            "value": 15,
        },
    ]


@pytest.mark.e2e
@pytest.mark.skip
class TestTendermintResetInterruptNoRejoin(TestTendermintResetInterrupt):
    """
    Test a Tendermint reset case for the ABCI oracle skill.

    Test the ABCI oracle skill with four agents when an agent gets temporarily interrupted
    on Tendermint reset and never rejoins.
    """

    wait_to_finish = 300
    # set the restart to a value so that the agent never rejoins, in order to test the impact to the rest of the agents
    restart_after = wait_to_finish
    # check if we manage to reset with Tendermint `__n_resets_to_perform` times with the rest of the agents
    exclude_from_checks = [3]



@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (1,))
class TestABCIPriceEstimationSingleAgentHTTPServer(ABCIPriceEstimationTest):
    """Test the ABCI oracle skill with only one agent with data share over http server connection."""

    multisig = SERVICE_MULTISIG_2
    key_pairs_override = [KEY_PAIRS[4]]
    
    def check_aea_messages(self) -> None:
        """
        Check that *each* AEA prints these messages.

        First failing check will cause assertion error and test tear down.
        """
        super().check_aea_messages()
        self.check_data_exposed()
        
    def check_data_exposed(self):
        """Check http data."""
        resp = requests.get(f"http://127.0.0.1:{self.BASE_PORT}")
        assert resp.json().get("payload")
        assert isinstance(resp.json().get("signatures"), dict)
        assert resp.json().get("signatures")
        assert self.key_pairs_override[0][0] in resp.json().get("signatures")