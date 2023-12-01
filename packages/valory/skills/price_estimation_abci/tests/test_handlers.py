# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, cast
from unittest.mock import MagicMock, Mock, patch

from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.valory.connections.http_server.connection import (
    PUBLIC_ID as HTTP_SERVER_PUBLIC_ID,
)
from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.price_estimation_abci.dialogues import HttpDialogues
from packages.valory.skills.price_estimation_abci.handlers import HttpServerHandler
from packages.valory.skills.price_estimation_abci.rounds import SynchronizedData


PACKAGE_DIR = Path(__file__).parents[1]

HTTP_SERVER_SENDER = str(HTTP_SERVER_PUBLIC_ID.without_hash())


@dataclass
class HandlerTestCase:  # pylint: disable=too-many-instance-attributes
    """HandlerTestCase"""

    name: str
    request_url: str
    request_body: bytes
    token_to_data: Dict[str, str]
    response_status_code: int
    response_status_text: str
    response_headers: str
    response_body: bytes
    method: str
    n_outbox_msgs: int
    set_last_update_time: bool = True


class TestHttpHandler(BaseSkillTestCase):
    """Test HttpHandler of http_echo."""

    path_to_skill = PACKAGE_DIR

    @classmethod
    def setup_class(cls, **kwargs: Any) -> None:
        """Setup the test class."""
        super().setup_class(**kwargs)
        cls._skill.skill_context.state = MagicMock()
        cls.http_handler = cast(
            HttpServerHandler, cls._skill.skill_context.handlers.http
        )
        cls.logger = cls._skill.skill_context.logger

        cls.http_dialogues = cast(
            HttpDialogues, cls._skill.skill_context.http_dialogues
        )

        cls.get_method = "get"
        cls.post_method = "post"
        cls.url = "http://localhost:8000/"
        cls.version = "some_version"
        cls.headers = ""
        cls.body = b"some_body/"
        cls.sender = HTTP_SERVER_SENDER
        cls.skill_id = str(cls._skill.skill_context.skill_id)

        cls.status_code = 100
        cls.status_text = "some_status_text"

        cls.content = b"some_content"
        cls.list_of_messages = (
            DialogueMessage(
                HttpMessage.Performative.REQUEST,
                {
                    "method": cls.get_method,
                    "url": cls.url,
                    "version": cls.version,
                    "headers": cls.headers,
                    "body": cls.body,
                },
            ),
        )

    def setup(self, **kwargs: Any) -> None:
        """Setup"""
        self.http_handler.setup()

    def test_setup(self) -> None:
        """Test the setup method of the handler."""
        assert self.http_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self) -> None:
        """Test the _handle_unidentified_dialogue method of the handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=HttpMessage.Performative.REQUEST,
            to=self.skill_id,
            method=self.get_method,
            url=self.url,
            version=self.version,
            headers=self.headers,
            body=self.body,
            sender=HTTP_SERVER_SENDER,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"Received invalid http message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_request_get_data_not_ready(self) -> None:
        """Test the _handle_request method of the handler where method is get."""
        # setup
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message(
                message_type=HttpMessage,
                performative=HttpMessage.Performative.REQUEST,
                to=self.skill_id,
                sender=self.sender,
                method="get",
                url="http://localhost:8000/",
                version=self.version,
                headers=self.headers,
                body="",
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            mock_now_time = datetime.datetime(2022, 1, 1)
            datetime_mock = Mock(wraps=datetime.datetime)
            datetime_mock.now.return_value = mock_now_time

            with patch("datetime.datetime", new=datetime_mock), patch.object(
                self.http_handler.context.state.round_sequence.latest_synchronized_data.db,
                "get",
                return_value="",
            ):
                self.http_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            "Received http request with method={}, url={} and body={!r}".format(
                incoming_message.method, incoming_message.url, incoming_message.body
            ),
        )

        # _handle_get
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.RESPONSE,
            to=incoming_message.sender,
            sender=incoming_message.to,
            version=incoming_message.version,
            status_code=503,
        )
        assert has_attributes, error_str
        assert message.body == b"Data not ready"

        mock_logger.assert_any_call(
            logging.INFO,
            f"Responding with: {message}",
        )

    def test_handle_request_get_data_ready(self) -> None:
        """Test the _handle_request method of the handler where method is get."""
        # setup
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message(
                message_type=HttpMessage,
                performative=HttpMessage.Performative.REQUEST,
                to=self.skill_id,
                sender=self.sender,
                method="get",
                url="http://localhost:8000/",
                version=self.version,
                headers=self.headers,
                body="",
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            mock_now_time = datetime.datetime(2022, 1, 1)
            datetime_mock = Mock(wraps=datetime.datetime)
            datetime_mock.now.return_value = mock_now_time

            with patch("datetime.datetime", new=datetime_mock), patch.object(
                self.http_handler.context.state.round_sequence.latest_synchronized_data.db,
                "get",
                return_value="some payload",
            ), patch.object(
                SynchronizedData,
                "_get_deserialized",
                return_value={"addr": MagicMock(signature="sig")},
            ):
                self.http_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            "Received http request with method={}, url={} and body={!r}".format(
                incoming_message.method, incoming_message.url, incoming_message.body
            ),
        )

        # _handle_get
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.RESPONSE,
            to=incoming_message.sender,
            sender=incoming_message.to,
            version=incoming_message.version,
            status_code=200,
            headers="Content-Type: application/json\n",
        )
        assert has_attributes, error_str
        assert (
            message.body
            == b'{"payload": "some payload", "signatures": {"addr": "sig"}}'
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"Responding with: {message}",
        )

    def test_teardown(self) -> None:
        """Test the teardown method of the handler."""
        assert self.http_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
