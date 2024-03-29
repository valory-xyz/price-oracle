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

"""Tests for valory/registration_abci skill's rounds."""

# pylint: skip-file

import logging  # noqa: F401
from typing import Any, Dict, FrozenSet, Mapping, Optional, Type, cast
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import AbciAppDB, AbstractRound
from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData as SynchronizedData,
)
from packages.valory.skills.abstract_round_abci.base import (
    BaseTxPayload,
    CollectSameUntilThresholdRound,
    CollectionRound,
    MAX_INT_256,
    VotingRound,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectSameUntilThresholdRoundTest,
    BaseOnlyKeeperSendsRoundTest,
    BaseVotingRoundTest,
)
from packages.valory.skills.oracle_deployment_abci.payloads import (
    DeployOraclePayload,
    RandomnessPayload,
    SelectKeeperPayload,
    VotingOraclePayload,
)
from packages.valory.skills.oracle_deployment_abci.rounds import DeployOracleRound
from packages.valory.skills.oracle_deployment_abci.rounds import (
    Event as OracleDeploymentEvent,
)
from packages.valory.skills.oracle_deployment_abci.rounds import SelectKeeperOracleRound
from packages.valory.skills.oracle_deployment_abci.rounds import (
    SynchronizedData as OracleDeploymentSynchronizedSata,
)
from packages.valory.skills.oracle_deployment_abci.rounds import ValidateOracleRound


MAX_PARTICIPANTS: int = 4
RANDOMNESS: str = "d1c29dce46f979f9748210d24bce4eae8be91272f5ca1a6aea2832d3dd676f51"


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_randomness(
    participants: FrozenSet[str], round_id: int
) -> Dict[str, RandomnessPayload]:
    """participant_to_randomness"""
    return {
        participant: RandomnessPayload(
            sender=participant,
            round_id=round_id,
            randomness=RANDOMNESS,
        )
        for participant in participants
    }


def get_most_voted_randomness() -> str:
    """most_voted_randomness"""
    return RANDOMNESS


def get_participant_to_selection(
    participants: FrozenSet[str],
    keeper: str = "keeper",
) -> Dict[str, SelectKeeperPayload]:
    """participant_to_selection"""
    return {
        participant: SelectKeeperPayload(sender=participant, keeper=keeper)
        for participant in participants
    }


def get_most_voted_keeper_address() -> str:
    """most_voted_keeper_address"""
    return "keeper"


def get_safe_contract_address() -> str:
    """safe_contract_address"""
    return "0x6f6ab56aca12"


def get_participant_to_votes(
    participants: FrozenSet[str], vote: Optional[bool] = True
) -> Dict[str, VotingOraclePayload]:
    """participant_to_votes"""
    return {
        participant: VotingOraclePayload(sender=participant, vote=vote)
        for participant in participants
    }


class BaseDeployTestClass(BaseOnlyKeeperSendsRoundTest):
    """Test DeploySafeRound."""

    round_class: Type[AbstractRound]
    payload_class: Type[BaseTxPayload]
    update_keyword: str

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        keeper = sorted(list(self.participants))[0]
        self.synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(most_voted_keeper_address=keeper),
        )

        test_round = self.round_class(
            synchronized_data=self.synchronized_data, context=mock.MagicMock()
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,  # type: ignore
                keeper_payloads=self.payload_class(keeper, get_safe_contract_address()),  # type: ignore
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    **{self.update_keyword: get_safe_contract_address()}
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: getattr(
                        _synchronized_data, self.update_keyword
                    )
                ],
                exit_event=self._event_class.DONE,
            )
        )


class TestDeployOracleRound(BaseDeployTestClass):
    """Test DeployOracleRound."""

    round_class = DeployOracleRound
    payload_class = DeployOraclePayload
    update_keyword = "oracle_contract_address"
    _event_class = OracleDeploymentEvent
    _synchronized_data_class = OracleDeploymentSynchronizedSata


class BaseValidateRoundTest(BaseVotingRoundTest):
    """Test BaseValidateRound."""

    test_class: Type[VotingRound]
    test_payload: Type[VotingOraclePayload]

    def test_positive_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        self.synchronized_data.update(tx_hashes_history="t" * 66)

        test_round = self.test_class(
            synchronized_data=self.synchronized_data, context=mock.MagicMock()
        )

        self._complete_run(
            self._test_voting_round_positive(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    participant_to_votes=CollectionRound.serialize_collection(
                        get_participant_to_votes(self.participants)
                    )
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.participant_to_votes.keys()
                ],
                exit_event=self._event_class.DONE,
            )
        )

    def test_negative_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = self.test_class(
            synchronized_data=self.synchronized_data, context=mock.MagicMock()
        )

        self._complete_run(
            self._test_voting_round_negative(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants, vote=False),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    participant_to_votes=CollectionRound.serialize_collection(
                        get_participant_to_votes(self.participants, vote=False)
                    )
                ),
                synchronized_data_attr_checks=[],
                exit_event=self._event_class.NEGATIVE,
            )
        )

    def test_none_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = self.test_class(
            synchronized_data=self.synchronized_data, context=mock.MagicMock()
        )

        self._complete_run(
            self._test_voting_round_none(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants, vote=None),
                synchronized_data_update_fn=lambda _synchronized_data, _: _synchronized_data.update(
                    participant_to_votes=CollectionRound.serialize_collection(
                        get_participant_to_votes(self.participants, vote=None)
                    )
                ),
                synchronized_data_attr_checks=[],
                exit_event=self._event_class.NONE,
            )
        )


class TestValidateOracleRound(BaseValidateRoundTest):
    """Test ValidateSafeRound."""

    test_class = ValidateOracleRound
    test_payload = VotingOraclePayload
    _event_class = OracleDeploymentEvent
    _synchronized_data_class = OracleDeploymentSynchronizedSata


class BaseSelectKeeperRoundTest(BaseCollectSameUntilThresholdRoundTest):
    """Test SelectKeeperTransactionSubmissionARound"""

    test_class: Type[CollectSameUntilThresholdRound]
    test_payload: Type[BaseTxPayload]

    _synchronized_data_class = SynchronizedData

    @staticmethod
    def _participant_to_selection(
        participants: FrozenSet[str], keepers: str
    ) -> Mapping[str, BaseTxPayload]:
        """Get participant to selection"""
        return get_participant_to_selection(participants, keepers)

    def test_run(
        self,
        most_voted_payload: str = "keeper",
        keepers: str = "",
        exit_event: Optional[Any] = None,
    ) -> None:
        """Run tests."""
        test_round = self.test_class(
            synchronized_data=self.synchronized_data.update(
                keepers=keepers,
            ),
            context=mock.MagicMock(),
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=self._participant_to_selection(
                    self.participants, most_voted_payload
                ),
                synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                    participant_to_selection=CollectionRound.serialize_collection(
                        self._participant_to_selection(
                            self.participants, most_voted_payload
                        )
                    )
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.participant_to_selection.keys()
                    if exit_event is None
                    else None
                ],
                most_voted_payload=most_voted_payload,
                exit_event=self._event_class.DONE if exit_event is None else exit_event,
            )
        )


class TestSelectKeeperOracleRound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperTransactionSubmissionRoundB."""

    test_class = SelectKeeperOracleRound
    test_payload = SelectKeeperPayload
    _event_class = OracleDeploymentEvent


def test_synchronized_datas() -> None:
    """Test SynchronizedData."""

    participants = get_participants()
    participant_to_randomness = get_participant_to_randomness(participants, 1)
    participant_to_randomness_serialized = CollectionRound.serialize_collection(
        participant_to_randomness
    )
    most_voted_randomness = get_most_voted_randomness()
    participant_to_selection = get_participant_to_selection(participants)
    participant_to_selection_serialized = CollectionRound.serialize_collection(
        participant_to_selection
    )
    most_voted_keeper_address = get_most_voted_keeper_address()
    safe_contract_address = get_safe_contract_address()
    oracle_contract_address = get_safe_contract_address()
    participant_to_votes = get_participant_to_votes(participants)
    participant_to_votes_serialized = CollectionRound.serialize_collection(
        participant_to_votes
    )
    actual_keeper_randomness = int(most_voted_randomness, base=16) / MAX_INT_256

    synchronized_data__ = OracleDeploymentSynchronizedSata(
        AbciAppDB(
            setup_data=AbciAppDB.data_to_lists(
                dict(
                    participants=tuple(get_participants()),
                    participant_to_randomness=participant_to_randomness_serialized,
                    most_voted_randomness=most_voted_randomness,
                    participant_to_selection=participant_to_selection_serialized,
                    participant_to_votes=participant_to_votes_serialized,
                    most_voted_keeper_address=most_voted_keeper_address,
                    safe_contract_address=safe_contract_address,
                    oracle_contract_address=oracle_contract_address,
                )
            ),
        )
    )
    assert synchronized_data__.participants == participants
    assert synchronized_data__.participant_to_randomness == participant_to_randomness
    assert synchronized_data__.participant_to_selection == participant_to_selection
    assert synchronized_data__.participant_to_votes == participant_to_votes
    assert (
        abs(synchronized_data__.keeper_randomness - actual_keeper_randomness) < 1e-10
    )  # avoid equality comparisons between floats
    assert synchronized_data__.most_voted_randomness == most_voted_randomness
    assert synchronized_data__.most_voted_keeper_address == most_voted_keeper_address
    assert synchronized_data__.safe_contract_address == safe_contract_address
    assert synchronized_data__.oracle_contract_address == oracle_contract_address
