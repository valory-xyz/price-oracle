# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

from packages.valory.skills.liquidity_provision.models import Params, SharedState


DEPLOY_SAFE_STATE = "deploy_safe"
FINALIZE_STATE = "finalize"


class DummyContext:
    """Dummy Context class for shared state."""

    class params:
        """Dummy param variable."""

        round_timeout_seconds: float = 1.0


class TestSharedState:
    """Test SharedState(Model) class."""

    def test_initialization(
        self,
    ) -> None:
        """Test initialization."""
        SharedState(name="", skill_context=DummyContext())


class TestParams:
    """Test params."""

    def test_initialization(
        self,
    ) -> None:
        """Test initialization."""
        params = Params(
            name="",
            skill_context=DummyContext(),
            tendermint_url="",
            consensus={"max_participants": 1},
            max_healthcheck=10,
            round_timeout_seconds=1,
            sleep_time=1,
            retry_timeout=1,
            retry_attempts=1,
        )
        assert not params.is_health_check_timed_out()
        params.increment_retries()