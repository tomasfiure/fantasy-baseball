import pandas as pd
import requests
from io import StringIO

# The CSV URL for Baseball Savant
csv_url = ("https://baseballsavant.mlb.com/leaderboard/custom?"
           "year=2025&type=batter&filter=&min=100"
           "&selections=ab%2Cpa%2Ck_percent%2Cbb_percent%2Cbatting_avg%2Cslg_percent"
           "%2Con_base_percent%2Cb_rbi%2Cb_total_bases%2Cr_total_stolen_base%2Cxba%2Cxslg"
           "%2Cwoba%2Cxwoba%2Cxobp%2Cxbadiff%2Cxslgdiff%2Cwobadiff%2Cavg_swing_speed"
           "%2Csweet_spot_percent%2Csolidcontact_percent%2Chard_hit_percent"
           "%2Cavg_best_speed%2Cavg_hyper_speed&chart=false&x=ab&y=ab"
           "&r=no&chartType=beeswarm&sort=xwoba&sortDir=desc&csv=true")

# Create a session with browser-like headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
response = requests.get(csv_url, headers=headers)

# Check if the request succeeded
if response.status_code == 200:
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))
    print(df.columns)
else:
    print(f"Failed to fetch CSV. Status code: {response.status_code}")
