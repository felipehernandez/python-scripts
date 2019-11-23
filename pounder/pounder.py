# google api
from __future__ import print_function

import random
from time import sleep

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

import datetime

# voice
import pyttsx3

PRE_MEETING_ALARM = 5

VOICES_EN = {
    'Allison',  # en_US
    'Daniel',  # en_GB
    'Fiona',  # en-scotland
    'Fred',  # en_US
    'Karen',  # en_AU
    'Kate',  # en_GB
    'Moira',  # en_IE
    'Oliver',  # en_GB
    'Samantha',  # en_US
    'Serena',  # en_GB
    'Tessa',  # en_ZA
    'Veena',  # en_IN
    'Victoria'  # en_US
}
VOICES_ES = {
    'Diego',  # es_AR
    'Jorge',  # es_ES
    'Juan',  # es_MX
    'Monica',  # es_ES
    'Paulina'  # es_MX
}

MESSAGES_PRE_MEETING = [
    'You have a meeting about {summary} in {minutes} minutes',
    'You still have {minutes} minutes to arrive to {summary}',
    'Move your lazy ass, you only have {minutes} minutes to make it to {summary}',
    '{summary}, Remember? It is going to be a pound in {minutes} minutes',
    'Do you hear that sound? It is your pound for being late to {summary}',
    'It is 5 o clock. I lied, But you can still use that momentum, to stand up and go to {summary}',
    'I know you cannot wait for {summary} so guess what! Wait is over',
    'I can see that glass of water is half empty. Fill it and take it to {summary}',
    'Man! I am better than that tube over there. Alessia ? Now. On your way to {summary}',
    'Roses are red. Violets are blue. I am just a script. {summary}',
    'Production is down!. Now that I have you attention. {summary}',
    'One. One.Two.Three.Four. {summary}',
    'TIK.TAK model founder. TIK. {summary}, TAK',
    '{summary} Or driving a formula 1. Tough decisions',
    'Note to myself. Do not put {summary} in your POJOS',
    'TOC.TOC. Who iss there? {summary}. Period. Move'
]
MESSAGES_BEER_O_CLOCK = [
    'It is beer o clock. Where is Gianni when you need him?'
]
MESSAGES_FOUR_O_CLOCK = [
    'Oh. shit! It\'s already 4 o\'clock!'
]

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'

EVENTS = None
VOICE_ENGINE = None


def set_up_voice():
    global VOICE_ENGINE

    VOICE_ENGINE = pyttsx3.init()
    voices = VOICE_ENGINE.getProperty('voices')
    for voice in voices:
        if voice.name.encode("utf-8").decode('utf-8') == 'Serena':
            VOICE_ENGINE.setProperty('voice', voice.id)
            VOICE_ENGINE.setProperty('rate', 10)


def main_loop():
    set_up_voice()

    while True:
        check_events()
        sleep(59)


def check_events():
    beer_o_clock()
    four_o_clock()
    meetings()


####################################################################################################
# BEER O'CLOCK
####################################################################################################

def beer_o_clock():
    if is_beer_o_clock(datetime.datetime.now()):
        output_message(select_random_message(MESSAGES_BEER_O_CLOCK))


def is_beer_o_clock(now):
    return now.weekday() is 4 and now.hour is 16 and now.minute is 0


####################################################################################################
# FOUR O'CLOCK
####################################################################################################

def four_o_clock():
    if is_four_o_clock(datetime.datetime.now()):
        output_message(select_random_message(MESSAGES_FOUR_O_CLOCK))


def is_four_o_clock(now):
    return now.weekday() is not 4 and now.hour is 16 and now.minute is 0  # 16:00 UTC


####################################################################################################
# MEETINGS
####################################################################################################

def meetings():
    global EVENTS

    now = datetime.datetime.now().astimezone(datetime.timezone.utc)
    load_events(now)

    if not EVENTS:
        log_action('No upcoming events found.')
    else:
        for event in EVENTS:
            difference_in_minutes = calculate_difference_in_minutes(now, to_date_time(
                event['start']['dateTime']))
            if difference_in_minutes < PRE_MEETING_ALARM:
                generate_pre_meeting_notification(event, difference_in_minutes)
                EVENTS.remove(event)
            else:
                log_action("Minutes until next calendar event: {}".format(difference_in_minutes))
                break


def load_events(now):
    global EVENTS
    if EVENTS is None or now.minute is 1:
        capture_next_events(now)


def capture_next_events(now):
    global EVENTS

    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('files/credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))
    # Call the Calendar API
    log_action('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary',
                                          timeMin=datetime.datetime.utcnow().isoformat() + 'Z',
                                          # 'Z' indicates UTC time
                                          maxResults=20,
                                          singleEvents=True,
                                          orderBy='startTime').execute().get('items', [])
    EVENTS = list(
        filter(lambda event: 'dateTime' in event['start'] and now < to_date_time(event['start']['dateTime']),
               events_result))


def to_date_time(date_in_google_api_format):
    return datetime.datetime.strptime(date_in_google_api_format,
                                      '%Y-%m-%dT%H:%M:%S%z').astimezone(datetime.timezone.utc)


def generate_pre_meeting_notification(event, difference_in_minutes):
    output_message(generate_pre_meeting_message(event, difference_in_minutes))


def generate_pre_meeting_message(event, difference_in_minutes):
    return select_random_message(MESSAGES_PRE_MEETING).format(summary=event['summary'],
                                                              minutes=difference_in_minutes)


####################################################################################################
# UTILS
####################################################################################################

def select_random_message(messages):
    return messages[random.randint(0, len(messages) - 1)]


def output_message(message):
    log_action('Voice: "{}"'.format(message))
    VOICE_ENGINE.say(message)
    VOICE_ENGINE.runAndWait()
    VOICE_ENGINE.stop()


def calculate_difference_in_minutes(time1, time2):
    difference = time2 - time1
    datetime.timedelta(0, 8, 562000)
    minutes, seconds = divmod(difference.days * 86400 + difference.seconds, 60)
    return minutes


def log_action(action):
    print('{} : {}'.format(datetime.datetime.now(), action))


if __name__ == '__main__': main_loop()
