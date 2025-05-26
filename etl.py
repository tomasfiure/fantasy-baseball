import pandas as pd
import sqlite3
import requests
from io import StringIO

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
        return pd.DataFrame()  # Empty DF fallback

def save_to_sqlite(df, db_name='hitters_stats.db'):
    """
    Saves a DataFrame to a SQLite DB (table: 'hitters').
    """
    conn = sqlite3.connect(db_name)
    df.to_sql('hitters', conn, if_exists='replace', index=False)
    conn.close()
    print("✅ Data saved to SQLite DB.")

if __name__ == '__main__':
    # 1️⃣ Get expected stats from Savant
    savant_df = get_savant_expected_stats()

    if not savant_df.empty:
        # 2️⃣ Process / clean data as needed
        # For now, let's keep it raw — you can add name normalization or merge with other data later

        # 3️⃣ Save to SQLite
        save_to_sqlite(savant_df)

    print("🎉 ETL pipeline complete.")
