import asyncio
import json
from typing import Any, Union, Dict
from uuid import UUID

from langchain.callbacks.base import AsyncCallbackHandler
from loguru import logger

from source.helpers.context_helpers import user_id_var
from source.helpers.websocket_helpers import WebsocketManager, connection_manager
from source.schemas.websocket_schema import WebsocketMessage, WebsocketMessageStatus
import asyncio

class AsyncClientStreamingCallbackHandler(AsyncCallbackHandler):

    def __init__(self, websocket_manager: WebsocketManager):
        self.connection_manager = websocket_manager

    async def on_llm_error(
            self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when LLM errors."""
        user_id = user_id_var.get()

        logger.error(error)

        message = WebsocketMessage(**{
            "user_id": str(user_id),
            "status": WebsocketMessageStatus.ERROR,
            "data": "An Internal Error Occured!"
        }).dict()

        await self.connection_manager.send_message(json.dumps(message), user_id)

    async def on_llm_start(
            self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Any:
        """Run when chain starts running."""
        user_id: UUID = user_id_var.get()

        message = WebsocketMessage(**{
            "user_id": str(user_id),
            "status": WebsocketMessageStatus.START
        }).dict()

        await self.connection_manager.send_message(json.dumps(message), user_id)

    async def on_llm_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""

        user_id = user_id_var.get()

        message = WebsocketMessage(**{
            "user_id": str(user_id),
            "status": WebsocketMessageStatus.END
        }).dict()

        await self.connection_manager.send_message(json.dumps(message), user_id)

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        '''
        Run on new LLM token. Only available when streaming is enabled.
        :param token:
        :param kwargs:
        :return:
        '''
        user_id = user_id_var.get()

        message = WebsocketMessage(**{
            "user_id": str(user_id),
            "status": WebsocketMessageStatus.SENDING,
            "data": token
        }).dict()

        await asyncio.sleep(0.025)

        await self.connection_manager.send_message(json.dumps(message), user_id)


streaming_callbacks = [AsyncClientStreamingCallbackHandler(websocket_manager=connection_manager)]
