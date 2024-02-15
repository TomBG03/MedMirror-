# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# <ProgramSnippet>
import asyncio
import configparser
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from graph import Graph

async def main():
    print('Python Graph Tutorial\n')

    # Load settings
    config = configparser.ConfigParser()
    config.read(['config.cfg', 'config.dev.cfg'])
    azure_settings = config['azure']

    graph: Graph = Graph(azure_settings)

    await greet_user(graph)

    choice = -1

    while choice != 0:
        print('Please choose one of the following options:')
        print('0. Exit')
        print('1. Display access token')
        print('2. List my inbox')
        print('3. Send mail')
        print('4. Make a Graph call')


        try:
            choice = int(input())
        except ValueError:
            choice = -1

        try:
            if choice == 0:
                print('Goodbye...')
            elif choice == 1:
                await display_access_token(graph)
            elif choice == 2:
                await list_inbox(graph)
            elif choice == 3:
                await send_mail(graph)
            elif choice == 4:
                await make_graph_call(graph)
            else:
                print('Invalid choice!\n')
        except ODataError as odata_error:
            print('Error:')
            if odata_error.error:
                print(odata_error.error.code, odata_error.error.message)
# </ProgramSnippet>

# <GreetUserSnippet>
async def greet_user(graph: Graph):
    user = await graph.get_user()
    if user:
        print('Hello,', user.display_name)
        # For Work/school accounts, email is in mail property
        # Personal accounts, email is in userPrincipalName
        print('Email:', user.mail or user.user_principal_name, '\n')
# </GreetUserSnippet>

# <DisplayAccessTokenSnippet>
async def display_access_token(graph: Graph):
    token = await graph.get_user_token()
    print('User token:', token, '\n')
# </DisplayAccessTokenSnippet>

# <ListInboxSnippet>
async def list_inbox(graph: Graph):
    message_page = await graph.get_inbox()
    if message_page and message_page.value:
        # Output each message's details
        for message in message_page.value:
            print('Message:', message.subject)
            if (
                message.from_ and
                message.from_.email_address
            ):
                print('  From:', message.from_.email_address.name or 'NONE')
            else:
                print('  From: NONE')
            print('  Status:', 'Read' if message.is_read else 'Unread')
            print('  Received:', message.received_date_time)

        # If @odata.nextLink is present
        more_available = message_page.odata_next_link is not None
        print('\nMore messages available?', more_available, '\n')
# </ListInboxSnippet>

# <SendMailSnippet>
async def send_mail(graph: Graph):
    # Send mail to the signed-in user
    # Get the user for their email address
    user = await graph.get_user()
    if user:
        user_email = "aivashkina70@gmail.com"
        # user_email = user.mail or user.user_principal_name

        await graph.send_mail('Testing Microsoft Graph', 'Hey Anna look at this!', user_email or '')
        print('Mail sent.\n')
# </SendMailSnippet>

async def list_calendar_events(graph: Graph):
    event_page = await graph.get_calendar_events()
    if event_page and event_page.value:
        # Output each event's details
        for event in event_page.value:
            print('Event:', event.subject)
            if (
                event.organizer and
                event.organizer.email_address
            ):
                print('  Organizer:', event.organizer.email_address.name or 'NONE')
            else:
                print('  Organizer: NONE')
            print('  Start:', event.start.date_time)
            print('  End:', event.end.date_time)

        # If @odata.nextLink is present
        more_available = event_page.odata_next_link is not None
        print('\nMore events available?', more_available, '\n')

# <MakeGraphCallSnippet>
async def make_graph_call(graph: Graph):
    events = await graph.make_graph_call()
    if events and events.value:
        for event in events.value:
            print('Event:', event.subject)
            print('  Start:', event.start.date_time)
            print('  End:', event.end.date_time)
            print('  Location:', event.location.display_name)
            print('  Organizer:', event.organizer.email_address.name)
            print('  Attendees:', len(event.attendees), '\n')   
# </MakeGraphCallSnippet>

# Run main
asyncio.run(main())
