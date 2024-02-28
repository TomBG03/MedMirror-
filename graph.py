# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# <UserAuthConfigSnippet>
from configparser import SectionProxy
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder)
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody)
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.event import Event
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.location import Location
from msgraph.generated.models.attendee import Attendee
from msgraph import GraphServiceClient
from msgraph.generated.users.item.events.events_request_builder import EventsRequestBuilder
from datetime import datetime
import requests


class Graph:
    settings: SectionProxy
    device_code_credential: DeviceCodeCredential
    user_client: GraphServiceClient

    def __init__(self, config: SectionProxy):
        self.settings = config
        client_id = self.settings['clientId']
        tenant_id = self.settings['tenantId']
        graph_scopes = self.settings['graphUserScopes'].split(' ')

        self.device_code_credential = DeviceCodeCredential(client_id, tenant_id = tenant_id)
        self.user_client = GraphServiceClient(self.device_code_credential, graph_scopes)
# </UserAuthConfigSnippet>

    # <GetUserTokenSnippet>
    async def get_user_token(self):
        graph_scopes = self.settings['graphUserScopes']
        access_token = self.device_code_credential.get_token(graph_scopes)
        return access_token.token
    # </GetUserTokenSnippet>

    # <GetUserSnippet>
    async def get_user(self):
        # Only request specific properties using $select
        query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters(
            select=['displayName', 'mail', 'userPrincipalName']
        )

        request_config = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )

        user = await self.user_client.me.get(request_configuration=request_config)
        return user
    # </GetUserSnippet>

    # <GetInboxSnippet>
    async def get_inbox(self, filter_by_unread: bool = False, filter_by_sender: str = None, filter_by_subject: str = None, filter_by_received_date: str = None, filter_by_received_time: str = None, top: int = None):
        query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            # Only request specific properties
            select=['from', 'isRead', 'receivedDateTime', 'subject'],
            # Sort by received time, newest first
            orderby=['receivedDateTime DESC']
        )
        if filter_by_unread:
            query_params.filter = "isRead eq false"
        if filter_by_sender:
            query_params.filter = f"from/emailAddress/address eq '{filter_by_sender}'"
        if filter_by_subject:
            query_params.filter = f"subject eq '{filter_by_subject}'"
        if filter_by_received_date:
            query_params.filter = f"receivedDateTime ge {filter_by_received_date}"
        if filter_by_received_time:
            query_params.filter = f"receivedDateTime ge {filter_by_received_time}"
        if top:
            query_params.top = top
            
        request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters= query_params
        )

        messages = await self.user_client.me.mail_folders.by_mail_folder_id('inbox').messages.get(
                request_configuration=request_config)
        return messages
    # </GetInboxSnippet>

    # <SendMailSnippet>
    async def send_mail(self, subject: str, body: str, recipient: str):
        message = Message()
        message.subject = subject

        message.body = ItemBody()
        message.body.content_type = BodyType.Text
        message.body.content = body

        to_recipient = Recipient()
        to_recipient.email_address = EmailAddress()
        to_recipient.email_address.address = recipient
        message.to_recipients = []
        message.to_recipients.append(to_recipient)

        request_body = SendMailPostRequestBody()
        request_body.message = message

        await self.user_client.me.send_mail.post(body=request_body)
        
    # </SendMailSnippet>

    async def get_calendars(self):
        result = await self.user_client.me.calendars.get()
        return result
    
    async def get_calendar_events(self, top: int = 5):
        today = datetime.now().strftime("%Y-%m-%d")
        
        query_params = EventsRequestBuilder.EventsRequestBuilderGetQueryParameters(
            # select=["subject", "body", "bodyPreview", "organizer", "attendees", "start", "end", "location"],
            # select=["subject", "organizer", "attendees", "start", "end", "location"],
            select = ["subject", "start", "end"],
            top=top,
            orderby=["start/dateTime ASC"],
            filter=f"start/dateTime ge '{today}'"
                
        )
        request_configuration = EventsRequestBuilder.EventsRequestBuilderGetRequestConfiguration(
        query_parameters = query_params,
        )
        request_configuration.headers.add("Prefer", "outlook.timezone=\"Etc/GMT\"")
        result = await self.user_client.me.events.get(request_configuration = request_configuration)
        return result 
    
    async def create_event(self, calendar_id: str, subject: str, start: str, end: str, location: str = None, body: str = None, attendees: list = None, is_online : bool = False):
        request_body = Event(
            subject = subject,

            start = DateTimeTimeZone(
                date_time = start,
                time_zone = "Etc/GMT",
            ),
            end = DateTimeTimeZone(
                date_time = end,
                time_zone = "Etc/GMT",
            ),
            is_online_meeting = is_online
        )
        if location:
            request_body.location = Location(display_name = location)
        if attendees:
            #logic for attendees
            request_body.attendees = []
        if body:
            request_body.body = ItemBody(content = body, content_type = BodyType.text)

        result = await self.user_client.me.calendars.by_calendar_id(calendar_id).events.post(request_body)
        return result
    

    async def get_ToDo_lists(self):
        result = await self.user_client.me.todo.lists.get()
        return result
    
    async def get_ToDo_tasks(self, list_id: str):
        try:
            result = await self.user_client.me.todo.lists.by_todo_task_list_id(list_id).tasks.get()
            return result
        except Exception as e:
            return "Unable to get tasks"



    
