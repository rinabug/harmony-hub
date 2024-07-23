import sqlite3
import random
import os
import re
from openai import OpenAI

OPENAI_API_KEY = os.getenv('OPENAI_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

def create_leaderboard_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        score INTEGER DEFAULT 0,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    ''')
    conn.commit()

def update_score(conn, username, points):
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO leaderboard (username, score) 
    VALUES (?, ?)
    ON CONFLICT(username) 
    DO UPDATE SET score = score + ?
    ''', (username, points, points))
    conn.commit()

def get_leaderboard(conn):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT username, score 
    FROM leaderboard 
    ORDER BY score DESC 
    LIMIT 10
    ''')
    return [{"username": row[0], "score": row[1]} for row in cursor.fetchall()]

def get_friends_leaderboard(conn, username):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT username, score 
    FROM leaderboard 
    WHERE username IN (
        SELECT friend_username 
        FROM friends 
        WHERE username = ?
    ) 
    ORDER BY score DESC 
    LIMIT 10
    ''', (username,))
    return [{"username": row[0], "score": row[1]} for row in cursor.fetchall()]

def generate_trivia_question(artists, asked_questions=[]):
    if not artists:
        return None

    artist = random.choice(artists)
    prompt = f"Generate a music trivia question about the artist {artist} "
    prompt += "with four multiple-choice options. Format the response as: Question\\nA) Option\\nB) Option\\nC) Option\\nD) Option\\nCorrect Answer: Letter"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a music trivia expert."},
                {"role": "user", "content": prompt}
            ]
        )

        question_data = response.choices[0].message.content
        pattern = r"Question\s*(.*)\s*A\)\s*(.*)\s*B\)\s*(.*)\s*C\)\s*(.*)\s*D\)\s*(.*)\s*Correct Answer:\s*([A-D])"
        match = re.match(pattern, question_data, re.DOTALL)

        if match:
            question = match.group(1).strip().replace('\n', '').replace(':', '')
            options = {
                'A': match.group(2).strip().replace('\n', '').replace(':', ''),
                'B': match.group(3).strip().replace('\n', '').replace(':', ''),
                'C': match.group(4).strip().replace('\n', '').replace(':', ''),
                'D': match.group(5).strip().replace('\n', '').replace(':', ''),
            }
            correct_answer = match.group(6).strip()

            # Check if question has been asked before
            if question in asked_questions:
                return generate_trivia_question(artists, asked_questions)  # Recursive call to get a new question
            else:
                return {'question': question, 'options': options, 'correct_answer': correct_answer}

        else:
            print("Error. Unable to parse the question data.")
            print(question_data)
            return None

    except Exception as e:
        print(f"Error generating trivia question: {e}")
        return None

def play_trivia(conn, username, sp):
    print("\nWelcome to Trivia!")
    score = 0
    num_questions = 5

    # Fetch user's top artists
    top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')
    artist_names = [artist['name'] for artist in top_artists['items']]

    for _ in range(num_questions):
        question_data = generate_trivia_question(artist_names)
        
        if question_data:
            print(question_data['question'])
            for key, value in question_data['options'].items():
                print(f"{key}) {value}")
            user_answer = input("Your answer (A/B/C/D): ").upper()

            if user_answer == question_data['correct_answer']:
                print("Correct!")
                score += 1
            else:
                print(f"Sorry, the correct answer was {question_data['correct_answer']}")
        else:
            print("Failed to generate a question. Skipping.")

    print(f"\nYou scored {score} out of {num_questions}")
    update_score(conn, username, score)
