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

"""This module contains the transaction payloads for common apps."""

from dataclasses import dataclass
from typing import Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


@dataclass(frozen=True)
class TransactionHashSamePayload(BaseTxPayload):
    """Represent a transaction payload of type 'tx_hash'."""

    tx_hash: Optional[str]


@dataclass(frozen=True)
class TransactionHashPayload(BaseTxPayload):
    """Represent a transaction payload of type 'tx_hash'."""

    signature: Optional[str]
    data_json: Optional[str]
    tx_hash: Optional[str]


@dataclass(frozen=True)
class ObservationPayload(BaseTxPayload):
    """Represent a transaction payload of type 'observation'."""

    observation: float


@dataclass(frozen=True)
class EstimatePayload(BaseTxPayload):
    """Represent a transaction payload of type 'estimate'."""

    estimate: float
