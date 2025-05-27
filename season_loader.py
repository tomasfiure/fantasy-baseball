import requests
import sqlite3
from datetime import datetime, timedelta

def get_boxscore(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    response = requests.get(url)
    if response.ok:
        return response.json()
    else:
        print(f"Error fetching boxscore for {game_pk}")
        return {}

def get_games_on_date(date_str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"
    response = requests.get(url)
    games = []
    if response.ok:
        data = response.json()
        dates = data.get("dates", [])
        for d in dates:
            for g in d.get("games", []):
                games.append({
                    "gamePk": g["gamePk"],
                    "gameDate": g["officialDate"]
                })
    return games

def get_pitcher_hand(pitcher_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}"
    response = requests.get(url)
    if response.ok:
        data = response.json()
        hand_code = data['people'][0]['pitchHand']['code']
        return hand_code
    else:
        print(f"Error fetching pitcher data for ID {pitcher_id}")
        return "Unknown"

def extract_lineups_from_boxscore(game_pk, game_date):
    box = get_boxscore(game_pk)
    lineups = []

    for team_side in ["home", "away"]:
        team_abbr = box["teams"][team_side]["team"]["abbreviation"]
        players_dict = box["teams"][team_side]["players"]
        batters_list = box["teams"][team_side]["batters"]

        opponent_side = "home" if team_side == "away" else "away"
        opponent_pitchers = box["teams"][opponent_side]["pitchers"]
        if not opponent_pitchers:
            continue
        starter_id = opponent_pitchers[0]
        pitcher_hand = get_pitcher_hand(starter_id)

        starters = []
        for player_id in batters_list:
            player_data = players_dict.get(f"ID{player_id}", {})
            is_sub = player_data.get("gameStatus", {}).get("isSubstitute", True)
            if not is_sub:
                player_name = player_data.get("person", {}).get("fullName", "Unknown Player")
                starters.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "batting_order": len(starters) + 1
                })
            if len(starters) == 9:
                break

        for starter in starters:
            lineup_entry = {
                "game_pk": game_pk,
                "game_date": game_date,
                "player_id": starter["player_id"],
                "player_name": starter["player_name"],
                "team": team_abbr,
                "batting_order": starter["batting_order"],
                "pitcher_hand": pitcher_hand
            }
            lineups.append(lineup_entry)

    return lineups

def create_db(db_name="lineups.db"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_lineups (
            game_pk INTEGER,
            game_date TEXT,
            player_id INTEGER,
            player_name TEXT,
            team TEXT,
            batting_order INTEGER,
            pitcher_hand TEXT,
            UNIQUE (game_pk, player_id)
        )
    """)
    conn.commit()
    conn.close()
    print(f"✅ Created (or verified) DB: {db_name}")

def insert_lineups(lineups, db_name="lineups.db"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    for entry in lineups:
        c.execute("""
            INSERT OR IGNORE INTO daily_lineups
            (game_pk, game_date, player_id, player_name, team, batting_order, pitcher_hand)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["game_pk"],
            entry["game_date"],
            entry["player_id"],
            entry["player_name"],
            entry["team"],
            entry["batting_order"],
            entry["pitcher_hand"]
        ))
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(lineups)} lineup entries into {db_name} (ignoring duplicates)")

if __name__ == "__main__":
    # Setup DB
    create_db()

    # Set season start date (adjust if needed)
    start_date = datetime.strptime("2025-03-28", "%Y-%m-%d")
    today = datetime.now()
    date = start_date

    while date <= today:
        date_str = date.strftime("%Y-%m-%d")
        print(f"📅 Processing lineups for {date_str}...")
        games = get_games_on_date(date_str)
        day_lineups = []
        for game in games:
            game_pk = game["gamePk"]
            game_date = game["gameDate"]
            lineup_entries = extract_lineups_from_boxscore(game_pk, game_date)
            day_lineups.extend(lineup_entries)

        if day_lineups:
            insert_lineups(day_lineups)
        else:
            print("No games found for this day.")
        date += timedelta(days=1)

    print("🎉 Season data load complete!")
