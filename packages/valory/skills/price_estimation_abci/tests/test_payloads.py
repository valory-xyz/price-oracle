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

"""Test the payloads.py module of the skill."""

# pylint: skip-file

from packages.valory.skills.price_estimation_abci.payloads import (
    EstimatePayload,
    ObservationPayload,
    TransactionHashPayload,
)


def test_observation_payload() -> None:
    """Test `ObservationPayload`."""

    payload = ObservationPayload(sender="sender", observation=1.0)

    assert payload.observation == 1.0
    assert payload.data == {"observation": 1.0}


def test_estimate_payload() -> None:
    """Test `EstimatePayload`."""

    payload = EstimatePayload(sender="sender", estimate=1.0)

    assert payload.estimate == 1.0
    assert payload.data == {"estimate": 1.0}


def test_transaction_hash_payload() -> None:
    """Test `TransactionHashPayload`."""

    payload = TransactionHashPayload(
        sender="sender", signature="sig", data_json="data", tx_hash="hash"
    )

    assert payload.signature == "sig"
    assert payload.data_json == "data"
    assert payload.tx_hash == "hash"
    assert payload.data == {"signature": "sig", "data_json": "data", "tx_hash": "hash"}
