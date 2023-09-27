import uuid

from fastapi import WebSocket
from loguru import logger


class WebsocketManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        # If user exist, add its ws object
        if user_id in self.active_connections:
            self.active_connections[user_id].append(websocket)
        # Create a new list for the user
        else:
            self.active_connections[user_id] = [websocket]

    async def disconnect(self, user_id: uuid.UUID, websocket: WebSocket):
        logger.info(f'websocket {websocket} closed ')
        if user_id in self.active_connections.keys() and len(self.active_connections[user_id]) != 1:
            self.active_connections[user_id].remove(websocket)
        else:
            del self.active_connections[user_id]

    async def disconnect_all_cnx(self, user_id: uuid.UUID):
        try:
            del self.active_connections[user_id]
            logger.info('all websocket connection for this user are closed')
        except KeyError as error:
            logger.error(f"There is no open websocket connection for this user : {error}")

    async def send_message(self, message: str, user_id: uuid.UUID):
        """
                Send message to client via websocket
                :param user_id:
                :param message
                """
        try:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)
        except Exception as error:
            logger.error(f"Connection failed ! {error}")

    @staticmethod
    async def receive_data(websocket: WebSocket):
        """
        receive message from client
        :param websocket:
        :return: message received
        """
        return await websocket.receive_bytes()

    @staticmethod
    async def recv_text(websocket: WebSocket):
        """
        receive message from client
        :return: message received
        """

        logger.info("Receiving text from client")
        return await websocket.receive_text()


connection_manager = WebsocketManager()
