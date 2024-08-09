from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3

app = FastAPI()

# Initialize SQLite database connection
def init_db():
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            score INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class Player(BaseModel):
    user_id: str
    username: str
    score: int

class PlayerUpdate(BaseModel):
    score: int

# API endpoints
@app.post("/submit_score/", response_model=Player)
def submit_score(player: Player):
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute('SELECT * FROM leaderboard WHERE user_id = ?', (player.user_id,))
    existing_player = cursor.fetchone()

    if existing_player:
        # Update score if the new score is higher
        if player.score > existing_player[2]:
            cursor.execute('UPDATE leaderboard SET score = ? WHERE user_id = ?',
                           (player.score, player.user_id))
            conn.commit()
        else:
            raise HTTPException(status_code=400, detail="New score is not higher than existing score.")
    else:
        cursor.execute('INSERT INTO leaderboard (user_id, username, score) VALUES (?, ?, ?)',
                       (player.user_id, player.username, player.score))
        conn.commit()

    cursor.execute('SELECT * FROM leaderboard WHERE user_id = ?', (player.user_id,))
    updated_player = cursor.fetchone()
    conn.close()

    return Player(user_id=updated_player[0], username=updated_player[1], score=updated_player[2])

@app.get("/leaderboard/", response_model=List[Player])
def get_leaderboard():
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM leaderboard ORDER BY score DESC LIMIT 10')
    leaderboard = cursor.fetchall()
    conn.close()

    return [Player(user_id=row[0], username=row[1], score=row[2]) for row in leaderboard]
