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

"""This module contains the shared state for the price estimation app ABCI application."""

from typing import Any, List, OrderedDict

from aea.skills.base import Model

from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import ResponseInfo, RetriesInfo
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.oracle_deployment_abci.models import Params as OracleParams
from packages.valory.skills.price_estimation_abci.rounds import PriceAggregationAbciApp
from packages.valory.skills.transaction_settlement_abci.models import TransactionParams


MARGIN = 5
MULTIPLIER = 2

Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


class Params(OracleParams, TransactionParams):
    """Parameters."""

    observation_aggregator_function: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.observation_aggregator_function = self._ensure(
            "observation_aggregator_function", kwargs, str
        )
        self.is_broadcasting_to_server = kwargs.pop("broadcast_to_server", False)
        super().__init__(*args, **kwargs)


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = PriceAggregationAbciApp


# TODO remove this workaround when the types get fixed in `open-autonomy`
class FixedApiSpecs(ApiSpecs):
    """A model that wraps APIs to get cryptocurrency prices."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize ApiSpecsModel."""
        self.url: str = self._ensure("url", kwargs, str)
        self.api_id: str = self._ensure("api_id", kwargs, str)
        self.method: str = self._ensure("method", kwargs, str)
        self.headers = self._ensure("headers", kwargs, List[OrderedDict[str, str]])
        self.parameters = self._ensure("parameters", kwargs, List[List[str]])
        self.response_info = ResponseInfo.from_json_dict(kwargs)
        self.retries_info = RetriesInfo.from_json_dict(kwargs)
        super(Model, self).__init__(*args, **kwargs)  # pylint: disable=bad-super-call
        self._frozen = True


class RandomnessApi(FixedApiSpecs):
    """A model for randomness api specifications."""


class PriceApi(FixedApiSpecs):
    """A model for various cryptocurrency price api specifications."""

    convert_id: str
    currency_id: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize PriceApi."""
        self.convert_id = self._ensure("convert_id", kwargs, str)
        self.currency_id = self._ensure("currency_id", kwargs, str)
        super().__init__(*args, **kwargs)


class ServerApi(FixedApiSpecs):
    """A model for oracle web server api specs"""
