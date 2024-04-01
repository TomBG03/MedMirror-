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
from msgraph.generated.models.todo_task import TodoTask
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.event import Event
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.location import Location
from msgraph.generated.models.attendee import Attendee
from msgraph import GraphServiceClient
from msgraph.generated.users.item.events.events_request_builder import EventsRequestBuilder
# from msgraph.generated.users.item.calendar.calendarView.calendar_view_request_builder import CalendarViewRequestBuilder
from msgraph.generated.models.subscription import Subscription
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

    #############################################################
    # User functions                                            #
    #############################################################
   
    async def get_user_token(self):
        graph_scopes = self.settings['graphUserScopes']
        access_token = self.device_code_credential.get_token(graph_scopes)
        return access_token.token
  
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

    #############################################################
    # Email functions                                           #
    #############################################################
    async def get_inbox(self, filter_by_unread: bool = False, filter_by_sender: str = None, filter_by_subject: str = None, filter_by_received_date: str = None, filter_by_received_time: str = None, top: int = None):
        query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            # Only request specific properties
            select=['id','from','isRead','receivedDateTime','subject','body'],
            # Sort by received time, newest first
            orderby=['receivedDateTime DESC']
        )
        if filter_by_unread:
            query_params.filter = "isRead eq false"
        if filter_by_sender is not None:
            query_params.filter = f"from/emailAddress/address eq '{filter_by_sender}'"
        if filter_by_subject is not None:
            query_params.filter = f"subject eq '{filter_by_subject}'"
        if filter_by_received_date is not None:
            query_params.filter = f" and receivedDateTime ge {filter_by_received_date}"
        if filter_by_received_time is not None:
            query_params.filter = f"receivedDateTime ge {filter_by_received_time}"
        if top is not None:
            query_params.top = top
            
        request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters= query_params
        )

        messages = await self.user_client.me.mail_folders.by_mail_folder_id('inbox').messages.get(
                request_configuration=request_config)
    
        message_data = []
        for message in messages.value:
            message_data.append({
                'id': message.id,
                'subject': message.subject,
                'received_date': message.received_date_time,
                'from': message.from_.email_address.address
            })
       
        return message_data
    
    async def read_email(self, message_id: str):
        message = await self.user_client.me.messages.by_message_id(message_id).get()
        message_data = message.body_preview
        return message_data
    
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
        try:
            result = await self.user_client.me.send_mail.post(body=request_body)
            return "Email sent successfully"
        except Exception as e:
            return "Unable to send email"
    # </SendMailSnippet>


    #############################################################
    # Calendar functions                                        #
    #############################################################
    async def get_calendars(self):
        result = await self.user_client.me.calendars.get()
        return result
    
    async def get_calendar_events(self, top: int = None, start_date: str = None, end_date: str = None):
        
        query_params = EventsRequestBuilder.EventsRequestBuilderGetQueryParameters(
            select = ["subject", "start", "end"],
            orderby=["start/dateTime ASC"],   
        )
        if top is not None:
            query_params.top = top
        # if start_date is not None and end_date is not None:
        #     query_params.filter = f"start/dateTime ge '{start_date}' and end/dateTime le '{end_date}'"
        if start_date is not None:
            query_params.filter = f"start/dateTime ge '{start_date}'"
        request_configuration = EventsRequestBuilder.EventsRequestBuilderGetRequestConfiguration(
        query_parameters = query_params,
        )
        request_configuration.headers.add("Prefer", "outlook.timezone=\"Etc/GMT\"")
        events = await self.user_client.me.events.get(request_configuration = request_configuration)
        event_data = []
        for event in events.value:
            event_data.append({
                "event_id": event.id,
                "subject": event.subject,
                "start": event.start.date_time,
                "end": event.end.date_time
            })
        return event_data

    async def list_calendar_view(self, start_date: str = None, end_date: str = None):
        access_token = await self.get_user_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'prefer': 'outlook.timezone="GMT Standard Time"'
        }
        # start_date = "2024-03-29T00:00:00"
        # end_date = "2024-03-29T23:59:59"
        start_date = start_date
        end_date = end_date
        
        url = f"https://graph.microsoft.com/v1.0/me/calendar/calendarView?startDateTime={start_date}&endDateTime={end_date}"

        result = requests.get(url, headers=headers)

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
            request_body.body = ItemBody(content = body, content_type = BodyType.Text)

        result = await self.user_client.me.calendars.by_calendar_id(calendar_id).events.post(request_body)
        return "Event created successfully"
    
    async def edit_event(self, event_id: str, subject: str = None, start: str = None, end: str = None, location: str = None, body: str = None, attendees: list = None, is_online : bool = False):
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
            request_body.body = ItemBody(content = body, content_type = BodyType.Text)

        result = await self.user_client.me.events.by_event_id(event_id).patch(request_body)

        return "Event updated successfully"

    async def delete_event(self, event_id: str):
        result = await self.user_client.me.events.by_event_id(event_id).delete()
        return f"Event deleted successfully"
    
    #############################################################
    # ToDo List functions                                       #
    #############################################################
    async def get_ToDo_lists(self):
        result = await self.user_client.me.todo.lists.get()
        return result
    
    async def get_ToDo_tasks(self, list_id: str):
        tasks = []
        try:
            task_data = []
            tasks = await self.user_client.me.todo.lists.by_todo_task_list_id(list_id).tasks.get()
            for task in tasks.value:
                task_data.append({
                    "task_id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "created_date": task.created_date_time,
                    "due_date": task.due_date_time
                })
            print(task_data)
            return task_data
        except Exception as e:
            return "Unable to get tasks"

    async def create_task(self, list_id: str, title: str, due_date: str, body: str = None, reminder_date: str = None):
        task = TodoTask(
        title=title,
        dueDateTime=DateTimeTimeZone(date_time=due_date, time_zone="Etc/GMT"),
        # Construct the body using the appropriate class, if necessary
        body=ItemBody(content = body, content_type = BodyType.Text) if body else None,
        )
        if reminder_date is not None:
            task.reminderDateTime=reminder_date
            task.isReminderOn=True
        
        result = await self.user_client.me.todo.lists.by_todo_task_list_id(list_id).tasks.post(task)
        return result
    
    async def edit_task(self, list_id: str, task_id: str, title: str = None, due_date: str = None, body: str = None):
        task = TodoTask(
        title=title,
        dueDateTime=DateTimeTimeZone(date_time=due_date, time_zone="Etc/GMT"),
        # Construct the body using the appropriate class, if necessary
        body=ItemBody(content = body, content_type = BodyType.Text) if body else None,
        )
        result = await self.user_client.me.todo.lists.by_todo_task_list_id(list_id).tasks.by_todo_task_id(task_id).patch(task)
        return result
    
    async def delete_task(self, list_id: str, task_id: str):
        result = await self.user_client.me.todo.lists.by_todo_task_list_id(list_id).tasks.by_todo_task_id(task_id).delete()
        return result
    #############################################################
    # Subscription functions                                    #
    #############################################################
    async def create_subscription(self, change_type: str, notification_url: str, resource: str, expiration_date_time: str):
        subscription = Subscription(
            change_type = change_type,
            notification_url = notification_url,
            resource = resource,
            expiration_date_time = expiration_date_time
        )
        result = await self.user_client.subscriptions.post(subscription)
        return result
    