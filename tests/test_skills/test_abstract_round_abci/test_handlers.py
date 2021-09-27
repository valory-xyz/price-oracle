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

"""Test the handlers.py module of the skill."""
from typing import cast
from unittest import mock
from unittest.mock import MagicMock

import pytest
from aea.configurations.data_types import PublicId

from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import CheckTxType, CheckTxTypeEnum
from packages.valory.skills.abstract_round_abci.base import (
    AddBlockError,
    ERROR_CODE,
    OK_CODE,
    SignatureNotValidError,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    AbciDialogue,
    AbciDialogues,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    ABCIRoundHandler,
    exception_to_info_msg,
)


def test_exception_to_info_msg():
    """Test 'exception_to_info_msg' helper function."""
    exception = Exception("exception message")
    expected_string = f"{exception.__class__.__name__}: {str(exception)}"
    actual_string = exception_to_info_msg(exception)
    assert expected_string == actual_string


class TestABCIRoundHandler:
    """Test 'ABCIRoundHandler'."""

    def setup(self):
        """Set up the tests."""
        self.context = MagicMock(skill_id=PublicId.from_str("dummy/skill:0.1.0"))
        self.dialogues = AbciDialogues(name="", skill_context=self.context)
        self.handler = ABCIRoundHandler(name="", skill_context=self.context)

    def test_info(self):
        """Test the 'info' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_INFO,
            version="",
            block_version=0,
            p2p_version=0,
        )
        response = self.handler.info(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_INFO

    def test_begin_block(self):
        """Test the 'begin_block' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_BEGIN_BLOCK,
            hash=b"",
            header=MagicMock(),
            last_commit_info=MagicMock(),
            byzantine_validators=MagicMock(),
        )
        response = self.handler.begin_block(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_BEGIN_BLOCK

    @mock.patch("packages.valory.skills.abstract_round_abci.handlers.Transaction")
    def test_check_tx(self, *_):
        """Test the 'check_tx' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_CHECK_TX,
            tx=b"",
            type=CheckTxType(CheckTxTypeEnum.NEW),
        )
        response = self.handler.check_tx(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_CHECK_TX
        assert response.code == OK_CODE

    @mock.patch(
        "packages.valory.skills.abstract_round_abci.handlers.Transaction.decode",
        side_effect=SignatureNotValidError,
    )
    def test_check_tx_negative(self, *_):
        """Test the 'check_tx' handler method, negative case."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_CHECK_TX,
            tx=b"",
            type=CheckTxType(CheckTxTypeEnum.NEW),
        )
        response = self.handler.check_tx(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_CHECK_TX
        assert response.code == ERROR_CODE

    @mock.patch("packages.valory.skills.abstract_round_abci.handlers.Transaction")
    def test_deliver_tx(self, *_):
        """Test the 'deliver_tx' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
            tx=b"",
        )
        response = self.handler.deliver_tx(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_DELIVER_TX
        assert response.code == OK_CODE

    @mock.patch(
        "packages.valory.skills.abstract_round_abci.handlers.Transaction.decode",
        side_effect=SignatureNotValidError,
    )
    def test_deliver_tx_negative(self, *_):
        """Test the 'deliver_tx' handler method, negative case."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_DELIVER_TX,
            tx=b"",
        )
        response = self.handler.deliver_tx(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_DELIVER_TX
        assert response.code == ERROR_CODE

    def test_end_block(self):
        """Test the 'end_block' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_END_BLOCK,
            height=1,
        )
        response = self.handler.end_block(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_END_BLOCK

    def test_commit(self):
        """Test the 'commit' handler method."""
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_COMMIT,
        )
        response = self.handler.commit(
            cast(AbciMessage, message), cast(AbciDialogue, dialogue)
        )
        assert response.performative == AbciMessage.Performative.RESPONSE_COMMIT

    def test_commit_negative(self):
        """Test the 'commit' handler method, negative case."""
        self.context.state.period.commit.side_effect = AddBlockError()
        message, dialogue = self.dialogues.create(
            counterparty="",
            performative=AbciMessage.Performative.REQUEST_COMMIT,
        )
        with pytest.raises(AddBlockError):
            self.handler.commit(
                cast(AbciMessage, message), cast(AbciDialogue, dialogue)
            )
