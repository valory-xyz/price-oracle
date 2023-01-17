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

"""Test the models.py module of the skill."""

# pylint: skip-file

from abc import ABC
from enum import Enum
from typing import Optional, Tuple

from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BaseSynchronizedData,
)
from packages.valory.skills.abstract_round_abci.test_tools.base import DummyContext
from packages.valory.skills.price_estimation_abci.models import SharedState


class ConcreteRound(AbstractRound, ABC):
    """A ConcreteRoundA for testing purposes."""

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Handle the end of the block."""


class TestSharedState:
    """Test SharedState(Model) class."""

    def test_initialization(
        self,
    ) -> None:
        """Test initialization."""
        SharedState(name="", skill_context=DummyContext())
