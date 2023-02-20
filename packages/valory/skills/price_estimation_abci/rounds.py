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

"""This module contains the data classes for the price estimation ABCI application."""

from enum import Enum
from typing import Dict, List, Mapping, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectDifferentUntilThresholdRound,
    CollectSameUntilThresholdRound,
    CollectionRound,
    DegenerateRound,
    DeserializedCollection,
    get_name,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    EstimatePayload,
    ObservationPayload,
    TransactionHashPayload,
)


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    NONE = "none"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"


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
    def oracle_contract_address(self) -> str:
        """Get the oracle contract address."""
        return cast(str, self.db.get_strict("oracle_contract_address"))

    @property
    def observations(self) -> List[float]:
        """Get the observations."""
        return [
            value.observation for value in self.participant_to_observations.values()
        ]

    @property
    def most_voted_estimate(self) -> float:
        """Get the most_voted_estimate."""
        return cast(float, self.db.get_strict("most_voted_estimate"))

    @property
    def most_voted_tx_hash(self) -> float:
        """Get the most_voted_tx_hash."""
        return cast(float, self.db.get_strict("most_voted_tx_hash"))

    def _get_deserialized(self, key: str) -> DeserializedCollection:
        """Strictly get a collection and return it deserialized."""
        serialized = self.db.get_strict(key)
        deserialized = CollectionRound.deserialize_collection(serialized)
        return cast(DeserializedCollection, deserialized)

    @property
    def participant_to_observations(self) -> Mapping[str, ObservationPayload]:
        """Get the participant_to_observations."""
        return cast(
            Mapping[str, ObservationPayload],
            self._get_deserialized("participant_to_observations"),
        )

    @property
    def participant_to_estimate(self) -> DeserializedCollection:
        """Get the participant_to_estimate."""
        return self._get_deserialized("participant_to_estimate")

    @property
    def participant_to_tx_hash(self) -> DeserializedCollection:
        """Get the participant_to_tx_hash."""
        return self._get_deserialized("participant_to_tx_hash")


class CollectObservationRound(CollectDifferentUntilThresholdRound):
    """A round in which agents collect observations"""

    payload_class = ObservationPayload
    payload_attribute = "observation"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_observations)


class EstimateConsensusRound(CollectSameUntilThresholdRound):
    """A round in which agents reach consensus on an estimate"""

    payload_class = EstimatePayload
    payload_attribute = "estimate"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_estimate)
    selection_key = get_name(SynchronizedData.most_voted_estimate)


class TxHashRound(CollectSameUntilThresholdRound):
    """A round in which agents compute the transaction hash"""

    payload_class = TransactionHashPayload
    payload_attribute = "tx_hash"
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_tx_hash)
    selection_key = get_name(SynchronizedData.most_voted_tx_hash)


class FinishedPriceAggregationRound(DegenerateRound):
    """A round that represents price aggregation has finished"""


class PriceAggregationAbciApp(AbciApp[Event]):
    """PriceAggregationAbciApp

    Initial round: CollectObservationRound

    Initial states: {CollectObservationRound}

    Transition states:
        0. CollectObservationRound
            - done: 1.
            - round timeout: 0.
            - no majority: 0.
        1. EstimateConsensusRound
            - done: 2.
            - none: 0.
            - round timeout: 0.
            - no majority: 0.
        2. TxHashRound
            - done: 3.
            - none: 0.
            - round timeout: 0.
            - no majority: 0.
        3. FinishedPriceAggregationRound

    Final states: {FinishedPriceAggregationRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = CollectObservationRound
    transition_function: AbciAppTransitionFunction = {
        CollectObservationRound: {
            Event.DONE: EstimateConsensusRound,
            Event.ROUND_TIMEOUT: CollectObservationRound,
            Event.NO_MAJORITY: CollectObservationRound,
        },
        EstimateConsensusRound: {
            Event.DONE: TxHashRound,
            Event.NONE: CollectObservationRound,
            Event.ROUND_TIMEOUT: CollectObservationRound,
            Event.NO_MAJORITY: CollectObservationRound,
        },
        TxHashRound: {
            Event.DONE: FinishedPriceAggregationRound,
            Event.NONE: CollectObservationRound,
            Event.ROUND_TIMEOUT: CollectObservationRound,
            Event.NO_MAJORITY: CollectObservationRound,
        },
        FinishedPriceAggregationRound: {},
    }
    final_states: Set[AppState] = {FinishedPriceAggregationRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    db_pre_conditions: Dict[AppState, Set[str]] = {
        CollectObservationRound: {
            get_name(SynchronizedData.participants),
            get_name(SynchronizedData.oracle_contract_address),
        }
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedPriceAggregationRound: {get_name(SynchronizedData.most_voted_tx_hash)}
    }
