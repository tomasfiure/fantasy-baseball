import pandas as pd
import sqlite3
import requests
from io import StringIO
from datetime import datetime, timedelta

# ========== Savant Advanced Stats Fetching ==========

def get_savant_expected_stats():
    """
    Fetches custom leaderboard data from Baseball Savant (with headers for 403 fix).
    """
    csv_url = ("https://baseballsavant.mlb.com/leaderboard/custom?"
               "year=2025&type=batter&filter=&min=100"
               "&selections=ab%2Cpa%2Ck_percent%2Cbb_percent%2Cbatting_avg%2Cslg_percent"
               "%2Con_base_percent%2Cb_rbi%2Cb_total_bases%2Cr_total_stolen_base%2Cxba%2Cxslg"
               "%2Cwoba%2Cxwoba%2Cxobp%2Cxbadiff%2Cxslgdiff%2Cwobadiff%2Cavg_swing_speed"
               "%2Csweet_spot_percent%2Csolidcontact_percent%2Chard_hit_percent"
               "%2Cavg_best_speed%2Cavg_hyper_speed&chart=false&x=ab&y=ab"
               "&r=no&chartType=beeswarm&sort=xwoba&sortDir=desc&csv=true")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(csv_url, headers=headers)

    if response.status_code == 200:
        csv_data = response.content.decode('utf-8')
        df = pd.read_csv(StringIO(csv_data))
        print("✅ Successfully fetched Savant data")
        return df
    else:
        print(f"❌ Failed to fetch Savant data. Status code: {response.status_code}")
        return pd.DataFrame()

def save_savant_to_sqlite(df, db_name='hitters_stats.db'):
    """
    Saves a DataFrame to a SQLite DB (table: 'hitters').
    """
    conn = sqlite3.connect(db_name)
    df.to_sql('hitters', conn, if_exists='replace', index=False)
    conn.close()
    print("✅ Savant data saved to SQLite DB.")

# ========== Daily Lineup ETL ==========

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
    print(f"✅ Inserted {len(lineups)} lineup entries (ignoring duplicates).")

# ========== Main Daily ETL ==========

if __name__ == '__main__':
    # 1️⃣ Fetch expected stats from Savant & save to DB
    savant_df = get_savant_expected_stats()
    if not savant_df.empty:
        save_savant_to_sqlite(savant_df)

    # 2️⃣ Fetch yesterday's lineups & append to DB
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"📅 Fetching lineups for yesterday: {yesterday}")

    games = get_games_on_date(yesterday)
    day_lineups = []
    for game in games:
        game_pk = game["gamePk"]
        game_date = game["gameDate"]
        lineup_entries = extract_lineups_from_boxscore(game_pk, game_date)
        day_lineups.extend(lineup_entries)

    if day_lineups:
        insert_lineups(day_lineups)
    else:
        print("No games found for yesterday.")

    print("🎉 Daily ETL pipeline complete.")
