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

"""This module contains the handler for the 'price_estimation_abci' skill."""
import json
from enum import Enum
from typing import Tuple, cast

from aea.protocols.base import Message

from packages.fetchai.connections.http_server.connection import (
    PUBLIC_ID as HTTP_SERVER_PUBLIC_ID,
)
from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.abstract_round_abci.dialogues import (
    HttpDialogue,
    HttpDialogues,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    HttpHandler as BaseHttpHandler,
)
from packages.valory.skills.price_estimation_abci.models import (
    SHARED_STATE_SERVICE_DATA_BYTES_KEY_NAME,
    SHARED_STATE_SIGNATURES_KEY_NAME,
)


class HttpMethod(Enum):
    """Http methods"""

    GET = "get"
    HEAD = "head"
    POST = "post"


class HttpServerHandler(BaseHttpHandler):
    """This implements the echo handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id
    allowed_response_performatives = frozenset({HttpMessage.Performative.REQUEST})
    json_content_header = "Content-Type: application/json\n"

    def handle(self, message: Message) -> None:
        """Handle incoming http request."""
        http_msg = cast(HttpMessage, message)
        if (
            http_msg.performative == HttpMessage.Performative.REQUEST
            and message.sender == str(HTTP_SERVER_PUBLIC_ID.without_hash())
        ):
            self.request_handle(message)
            return None
        return super().handle(message)

    def request_handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        http_msg = cast(HttpMessage, message)

        # Check if this is a request sent from the http_server skill
        if (
            http_msg.performative != HttpMessage.Performative.REQUEST
            or message.sender != str(HTTP_SERVER_PUBLIC_ID.without_hash())
        ):
            super().handle(message)
            return

        # Retrieve dialogues
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(HttpDialogue, http_dialogues.update(http_msg))

        # Invalid message
        if http_dialogue is None:
            self.context.logger.info(
                "Received invalid http message={}, unidentified dialogue.".format(
                    http_msg
                )
            )
            return

        # Handle message
        self.context.logger.info(
            "Received http request with method={}, url={} and body={!r}".format(
                http_msg.method,
                http_msg.url,
                http_msg.body,
            )
        )

        code, data_bytes = self.get_data()
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=code,
            status_text="Success",
            headers=f"{self.json_content_header}",
            body=data_bytes,
        )

        # Send response
        self.context.logger.info("Responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def get_data(self) -> Tuple[int, bytes]:
        """Get data and status code for resonse."""
        data = {
            "payload": self.context.shared_state.get(
                SHARED_STATE_SERVICE_DATA_BYTES_KEY_NAME, b""
            ).decode("utf-8"),
            "signatures": self.context.shared_state.get(
                SHARED_STATE_SIGNATURES_KEY_NAME,
                {},
            ),
        }
        data_bytes = json.dumps(data).encode("utf-8")
        return 200, data_bytes
