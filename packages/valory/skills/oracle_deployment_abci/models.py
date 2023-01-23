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

from typing import Any, Dict, Union

from aea.skills.base import Model

from packages.valory.skills.abstract_round_abci.models import ApiSpecs, BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import ResponseInfo, RetriesInfo
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.oracle_deployment_abci.rounds import OracleDeploymentAbciApp


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = OracleDeploymentAbciApp


class Params(BaseParams):
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.oracle_params = self._ensure("oracle", kwargs, Dict[str, Union[int, str]])
        super().__init__(*args, **kwargs)


# TODO remove this workaround when the types get fixed in `open-autonomy`
class FixedApiSpecs(ApiSpecs):
    """A model that wraps APIs to get cryptocurrency prices."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize ApiSpecsModel."""
        self.url: str = self._ensure("url", kwargs, str)
        self.api_id: str = self._ensure("api_id", kwargs, str)
        self.method: str = self._ensure("method", kwargs, str)
        self.headers = kwargs.pop("headers", [])
        self.parameters = kwargs.pop("parameters", [])
        self.response_info = ResponseInfo.from_json_dict(kwargs)
        self.retries_info = RetriesInfo.from_json_dict(kwargs)
        super(Model, self).__init__(*args, **kwargs)  # pylint: disable=bad-super-call
        self._frozen = True


class RandomnessApi(FixedApiSpecs):
    """A model for randomness api specifications."""


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
