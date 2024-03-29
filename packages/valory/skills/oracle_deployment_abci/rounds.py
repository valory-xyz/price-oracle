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

"""This module contains the data classes for the oracle deployment ABCI application."""

from enum import Enum
from typing import Dict, Optional, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    OnlyKeeperSendsRound,
    VotingRound,
    get_name,
)
from packages.valory.skills.oracle_deployment_abci.payloads import (
    DeployOraclePayload,
    RandomnessPayload,
    SelectKeeperPayload,
    VotingOraclePayload,
)


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    NEGATIVE = "negative"
    NONE = "none"
    FAILED = "failed"
    DEPLOY_TIMEOUT = "deploy_timeout"
    VALIDATE_TIMEOUT = "validate_timeout"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        return cast(str, self.db.get_strict("safe_contract_address"))

    @property
    def oracle_contract_address(self) -> Optional[str]:
        """Get the oracle contract address."""
        return cast(Optional[str], self.db.get("oracle_contract_address", None))


class SetupCheckRound(VotingRound):
    """A round which checks if the oracle address is already provided via the agents' `setup` or not"""

    payload_class = VotingOraclePayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_ffw"


class RandomnessOracleRound(CollectSameUntilThresholdRound):
    """A round for generating randomness"""

    payload_class = RandomnessPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_randomness)
    selection_key = ("ignored", get_name(SynchronizedData.most_voted_randomness))


class SelectKeeperOracleRound(CollectSameUntilThresholdRound):
    """A round in a which keeper is selected"""

    payload_class = SelectKeeperPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_selection)
    selection_key = get_name(SynchronizedData.most_voted_keeper_address)


class DeployOracleRound(OnlyKeeperSendsRound):
    """A round in a which the oracle is deployed"""

    payload_class = DeployOraclePayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    fail_event = Event.FAILED
    payload_key = get_name(SynchronizedData.oracle_contract_address)


class ValidateOracleRound(VotingRound):
    """A round in a which the oracle address is validated"""

    payload_class = VotingOraclePayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_votes)


class FinishedOracleRound(DegenerateRound):
    """A round that represents that the oracle has been deployed"""


class OracleDeploymentAbciApp(AbciApp[Event]):
    """OracleDeploymentAbciApp

    Initial round: SetupCheckRound

    Initial states: {SetupCheckRound}

    Transition states:
        0. SetupCheckRound
            - done: 5.
            - negative: 1.
            - none: 1.
            - round timeout: 0.
            - no majority: 1.
        1. RandomnessOracleRound
            - done: 2.
            - round timeout: 1.
            - no majority: 1.
        2. SelectKeeperOracleRound
            - done: 3.
            - round timeout: 1.
            - no majority: 1.
        3. DeployOracleRound
            - done: 4.
            - deploy timeout: 2.
            - failed: 2.
        4. ValidateOracleRound
            - done: 5.
            - negative: 1.
            - none: 1.
            - validate timeout: 1.
            - no majority: 1.
        5. FinishedOracleRound

    Final states: {FinishedOracleRound}

    Timeouts:
        round timeout: 30.0
        validate timeout: 30.0
        deploy timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = SetupCheckRound
    transition_function: AbciAppTransitionFunction = {
        SetupCheckRound: {
            Event.DONE: FinishedOracleRound,  # we trust the given input and do not transition to `ValidateOracleRound`
            Event.NEGATIVE: RandomnessOracleRound,
            Event.NONE: RandomnessOracleRound,  # NOTE: unreachable
            Event.ROUND_TIMEOUT: SetupCheckRound,
            Event.NO_MAJORITY: RandomnessOracleRound,
        },
        RandomnessOracleRound: {
            Event.DONE: SelectKeeperOracleRound,
            Event.ROUND_TIMEOUT: RandomnessOracleRound,
            Event.NO_MAJORITY: RandomnessOracleRound,
        },
        SelectKeeperOracleRound: {
            Event.DONE: DeployOracleRound,
            Event.ROUND_TIMEOUT: RandomnessOracleRound,
            Event.NO_MAJORITY: RandomnessOracleRound,
        },
        DeployOracleRound: {
            Event.DONE: ValidateOracleRound,
            Event.DEPLOY_TIMEOUT: SelectKeeperOracleRound,
            # NOTE: Consider the case where the keeper does send the tx but doesn't share the hash.
            # We do not need to check for this! A simple round timeout will do here as the agents
            # do not care about this oracle instance.
            Event.FAILED: SelectKeeperOracleRound,
        },
        ValidateOracleRound: {
            Event.DONE: FinishedOracleRound,
            Event.NEGATIVE: RandomnessOracleRound,
            Event.NONE: RandomnessOracleRound,  # NOTE: unreachable
            Event.VALIDATE_TIMEOUT: RandomnessOracleRound,
            Event.NO_MAJORITY: RandomnessOracleRound,
        },
        FinishedOracleRound: {},
    }
    final_states: Set[AppState] = {FinishedOracleRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.DEPLOY_TIMEOUT: 30.0,
    }
    cross_period_persisted_keys = frozenset(
        {
            get_name(SynchronizedData.safe_contract_address),
            get_name(SynchronizedData.oracle_contract_address),
        }
    )
    db_pre_conditions: Dict[AppState, Set[str]] = {SetupCheckRound: set()}
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedOracleRound: {get_name(SynchronizedData.oracle_contract_address)}
    }
