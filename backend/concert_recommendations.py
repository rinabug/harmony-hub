import os
import requests
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv

CONSUMER_KEY = 'HUcIiU1Vx1zUbEzgVkz1f3ypAbQXzVnP'
CONSUMER_SECRET = 'rHo3SXLeP3BuqcD4'

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

BASE_URL = 'https://app.ticketmaster.com/discovery/v2/'

def get_events(location, genre, radius):
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    params = {
        'apikey': CONSUMER_KEY,
        'keyword': genre,
        'startDateTime': f"{start_date}T00:00:00Z",
        'endDateTime': f"{end_date}T23:59:59Z",
        'size': 20,
        'sort': 'date,asc',
        'segmentName': 'music',
        'classificationName': genre,
        'city': location,
        'radius': radius,
        'unit': 'miles'
    }

    response = requests.get(f"{BASE_URL}events.json", params=params)

    if response.status_code == 200:
        data = response.json()
        if '_embedded' in data and 'events' in data['_embedded']:
            return data['_embedded']['events']
    return []

def format_events(events):
    formatted_events = []
    for event in events:
        name = event['name']
        date = event['dates']['start']['localDate']
        time = event['dates']['start'].get('localTime', 'Time not specified')
        venue = event['_embedded']['venues'][0]['name']
        city = event['_embedded']['venues'][0]['city']['name']
        state = event['_embedded']['venues'][0]['state']['stateCode']
        classifications = event['classifications'][0]
        event_type = classifications['segment']['name']
        genre = classifications['genre']['name']
        formatted_events.append(f"Event: {name}, Genre: {genre}, Event Type: {event_type}, Date: {date}, Time: {time}, Venue: {venue}, Location: {city}, {state}")
    return formatted_events

def get_chatgpt_recommendations(events, user_genre):
    events_text = "\n".join(events)
    prompt = f"Given the user's favorite genre '{user_genre}' and the following list of events:\n{events_text}\nPlease recommend 1 event that the user might enjoy."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful event recommendation assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def get_concert_recommendations(location, genres, radius):
    all_events = []
    for genre in genres:
        events = get_events(location, genre, radius)
        all_events.extend(format_events(events))
    
    if not all_events:
        return None, []

    chatgpt_recommendation = get_chatgpt_recommendations(all_events, genres)
    
    return chatgpt_recommendation, all_events