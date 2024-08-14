from pieces_os_client import (
    ApiClient,
    Application,
    Configuration,
    ConversationApi,
    ConversationMessageApi,
    ConversationMessagesApi,
    ConversationsApi,
    QGPTApi,
    UserApi,
    FormatApi,
    ConnectorApi,
    SeededConnectorConnection,
    SeededTrackedApplication,
    AssetApi,
    AssetsApi,
    FragmentMetadata
)
from typing import Optional
import platform

from .assets import AssetWrapper
from .streamed_identifiers import AssetSnapshot
from .websockets import *

class PiecesClient:
    def __init__(self, config: dict, seeded_connector: SeededConnectorConnection = None):
        self.host = config['baseUrl'][:-1] if config['baseUrl'].endswith("/") else config['baseUrl']

        self.config = Configuration(
            host=self.host
        )

        self.api_client = ApiClient(self.config)

        self.conversation_message_api = ConversationMessageApi(self.api_client)
        self.conversation_messages_api = ConversationMessagesApi(self.api_client)
        self.conversations_api = ConversationsApi(self.api_client)
        self.conversation_api = ConversationApi(self.api_client)
        self.qgpt_api = QGPTApi(self.api_client)
        self.user_api = UserApi(self.api_client)
        self.assets_api = AssetsApi(self.api_client)
        self.asset_api = AssetApi(self.api_client)
        self.format_api = FormatApi(self.api_client)
        self.connector_api = ConnectorApi(self.api_client)

        # Websocket urls
        if 'http' not in self.host:
            raise TypeError("Invalid host url\n Host should start with http or https")
        ws_base_url:str = self.host.replace('http','ws')
        
        self.ASSETS_IDENTIFIERS_WS_URL = ws_base_url + "/assets/stream/identifiers"
        self.AUTH_WS_URL = ws_base_url + "/user/stream"
        self.ASK_STREAM_WS_URL = ws_base_url + "/qgpt/stream"
        self.CONVERSATION_WS_URL = ws_base_url + "/conversations/stream/identifiers"
        self.HEALTH_WS_URL = ws_base_url + "/.well-known/stream/health"

        local_os = platform.system().upper() if platform.system().upper() in ["WINDOWS","LINUX","DARWIN"] else "WEB"
        local_os = "MACOS" if local_os == "DARWIN" else local_os
        seeded_connector = seeded_connector or SeededConnectorConnection(
            application=SeededTrackedApplication(
                name = "OPEN_SOURCE",
                platform = local_os,
                version = "0.0.1"))

        self.tracked_application = self.connector_api.connect(seeded_connector_connection=seeded_connector).application


        self.conversation_ws = ConversationWS(self)
        self.assets_ws = AssetsIdentifiersWS(self)

        # Start all initilized websockets
        BaseWebsocket.start_all()

    @staticmethod
    def assets():
        return [AssetWrapper(id) for id in AssetSnapshot.identifiers_snapshot.keys()]

    @staticmethod
    def asset(asset_id):
        return AssetWrapper(asset_id)

    @staticmethod
    def create_asset(content:str,metadata:Optional[FragmentMetadata]=None):
        return AssetWrapper(AssetSnapshot.create(content,metadata))


    # def create_conversation(self,first_message:str, name:str="New Conversation") -> dict:

    #     try:
    #         new_conversation = self.conversations_api.conversations_create_specific_conversation(
    #             seeded_conversation={
    #                 'name': name,
    #                 # 'type': ConversationTypeEnum.Copilot,
    #                 'type': 'COPILOT',
    #             }
    #         )

    #         if first_message:
    #             answer = self.prompt_conversation(
    #                 message=first_message,
    #                 conversation_id=new_conversation.id,
    #             )

    #             return {
    #                 'conversation': new_conversation,
    #                 'answer': answer
    #             }

    #         return {'conversation': new_conversation}
    #     except Exception as error:
    #         print(f'Error creating conversation: {error}')
    #         return

    # def get_conversation(self, conversation_id: str, include_raw_messages: bool = False) -> dict:
    #     conversation_messages = []

    #     try:
    #         conversation = self.conversation_api.conversation_get_specific_conversation(
    #             conversation=conversation_id,
    #         )

    #         if not include_raw_messages:
    #             return conversation.__dict__

    #         for message_id, index in (conversation.messages.indices or {}).items():
    #             message_response = self.conversation_message_api.message_specific_message_snapshot(
    #                 message=message_id,
    #             )

    #             if (not message_response.fragment or
    #                     not message_response.fragment.string or
    #                     not message_response.fragment.string.raw):
    #                 continue

    #             conversation_messages.append({
    #                 'message': message_response.fragment.string.raw,
    #                 'is_user_message': message_response.role == 'USER',
    #             })

    #         return {
    #             **conversation.__dict__,
    #             'raw_messages': conversation_messages,
    #         }
    #     except Exception as error:
    #         print(f'Error getting conversation: {error}')
    #         return None


    # def ask_question(self, question: str) -> str:
    #     try:
    #         answer = self.qgpt_api.question(
    #             qgpt_question_input={
    #                 'query': question,
    #                 'pipeline': {
    #                     'conversation': {
    #                         'generalizedCodeDialog': {},
    #                     },
    #                 },
    #                 'relevant': {
    #                     'iterable': [],
    #                 }
    #             }
    #         )
    #         return answer.answers.iterable[0].text
    #     except Exception as error:
    #         print(f'Error asking question: {error}')
    #         return 'Error asking question'


    # def prompt_conversation(self, message: str, conversation_id: str, regenerate_conversation_name: bool = False) -> dict:
    #     try:
    #         conversation = self.get_conversation(
    #             conversation_id=conversation_id,
    #             include_raw_messages=True,
    #         )

    #         if not conversation:
    #             return {'text': 'Conversation not found'}

    #         user_message = self.conversation_messages_api.messages_create_specific_message(
    #             seeded_conversation_message={
    #                 # 'role': QGPTConversationMessageRoleEnum.User,
    #                 'role': 'USER',
    #                 'fragment': {
    #                     'string': {
    #                         'raw': message,
    #                     },
    #                 },
    #                 'conversation': {'id': conversation_id},
    #             }
    #         )

    #         relevant_conversation_messages = [
    #             {
    #                 'seed': {
    #                     # 'type': SeedTypeEnum.Asset,
    #                     'type': 'SEEDED_ASSET',
    #                     'asset': {
    #                         'application': self.tracked_application.to_dict(),
    #                         'format': {
    #                             'fragment': {
    #                                 'string': {
    #                                     'raw': msg['message'],
    #                                 },
    #                             },
    #                         },
    #                     },
    #                 }
    #             }
    #             for msg in (conversation.get('raw_messages') or [])
    #         ]

    #         answer = self.qgpt_api.question(
    #             qgpt_question_input={
    #                 'query': message,
    #                 'pipeline': {
    #                     'conversation': {
    #                         'contextualizedCodeDialog': {},
    #                     },
    #                 },
    #                 'relevant': {
    #                     'iterable': relevant_conversation_messages,
    #                 },
    #             }
    #         )

    #         bot_message = self.conversation_messages_api.messages_create_specific_message(
    #             seeded_conversation_message={
    #                 # 'role': QGPTConversationMessageRoleEnum.Assistant,
    #                 'role': 'ASSISTANT',
    #                 'fragment': {
    #                     'string': {
    #                         'raw': answer.answers.iterable[0].text,
    #                     },
    #                 },
    #                 'conversation': {'id': conversation_id},
    #             }
    #         )

    #         if regenerate_conversation_name:
    #             self.update_conversation_name(conversation_id=conversation_id)

    #         return {
    #             'text': answer.answers.iterable[0].text,
    #             'user_message_id': user_message.id,
    #             'bot_message_id': bot_message.id,
    #         }
    #     except Exception as error:
    #         print(f'Error prompting conversation: {error}')
    #         return {'text': 'Error asking question'}

    # def update_conversation_name(self, conversation_id: str) -> str:
    #     try:
    #         conversation = self.conversation_api.conversation_specific_conversation_rename(
    #             conversation=conversation_id,
    #         )
    #         return conversation.name
    #     except Exception as error:
    #         print(f'Error updating conversation name: {error}')
    #         return 'Error updating conversation name'

    def get_user_profile_picture(self) -> str:
        try:
            user_res = self.user_api.user_snapshot()
            return user_res.user.picture or None
        except Exception as error:
            print(f'Error getting user profile picture: {error}')
            return None
