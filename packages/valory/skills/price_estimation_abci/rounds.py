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

from collections import Counter
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppException,
    ABCIAppInternalError,
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    BaseTxPayload,
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
    TransactionHashSamePayload,
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
    def participant_to_signatures(self) -> Dict[str, Optional[str]]:
        """Get the `participant_to_signatures`."""
        participant_to_payload = cast(
            Mapping[str, TransactionHashPayload],
            self._get_deserialized("participant_to_signatures"),
        )
        return {
            agent_address: payload.signature
            for agent_address, payload in participant_to_payload.items()
        }

    @property
    def signature(self) -> str:
        """Get the current agent's signature."""
        return str(self.db.get("signature", {}))

    @property
    def data_json(self) -> str:
        """Get the data json."""
        return str(self.db.get("data_json", ""))


class CollectObservationRound(CollectDifferentUntilThresholdRound):
    """A round in which agents collect observations"""

    payload_class = ObservationPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_observations)


class EstimateConsensusRound(CollectSameUntilThresholdRound):
    """A round in which agents reach consensus on an estimate"""

    payload_class = EstimatePayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_estimate)
    selection_key = get_name(SynchronizedData.most_voted_estimate)


class TxHashRound(CollectSameUntilThresholdRound):
    """
    A round in which agents compute the transaction hash.

    This is a special kind of round. It is a mix of collect same and collect different.
    In essence, it collects the same values for the tx hash and different values for the signatures and the data.
    """

    payload_class = TransactionHashPayload
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_signatures)
    selection_key = (
        get_name(SynchronizedData.signature),
        get_name(SynchronizedData.data_json),
        get_name(SynchronizedData.most_voted_tx_hash),
    )

    @property
    def payload_values_count(self) -> Counter:
        """Get count of payload values."""
        return Counter(map(lambda p: (p.values[2],), self.payloads))

    @property
    def most_voted_payload_values(
        self,
    ) -> Tuple[Any, ...]:
        """Get the most voted payload values."""
        _, max_votes = self.payload_values_count.most_common()[0]
        if max_votes < self.synchronized_data.consensus_threshold:
            raise ABCIAppInternalError("not enough votes")

        all_payload_values_count = Counter(map(lambda p: p.values, self.payloads))
        most_voted_payload_values, _ = all_payload_values_count.most_common()[0]
        return most_voted_payload_values

    def check_majority_possible(
        self,
        votes_by_participant: Dict[str, BaseTxPayload],
        nb_participants: int,
        exception_cls: Type[ABCIAppException] = ABCIAppException,
    ) -> None:
        """
        Overrides the check to only account for the tx hash which should be the same.

        The rest attributes have to be different.

        :param votes_by_participant: a mapping from a participant to its vote
        :param nb_participants: the total number of participants
        :param exception_cls: the class of the exception to raise in case the check fails
        """
        votes_by_participant = {
            participant: TransactionHashSamePayload(
                payload.sender, cast(TransactionHashSamePayload, payload).tx_hash
            )
            for participant, payload in votes_by_participant.items()
        }
        super().check_majority_possible(
            votes_by_participant, nb_participants, exception_cls
        )


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
