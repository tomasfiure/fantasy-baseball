from flask import Flask, render_template
import sqlite3
import pandas as pd

app = Flask(__name__)

def load_savant_data():
    conn = sqlite3.connect("hitters_stats.db")
    df = pd.read_sql_query("SELECT * FROM hitters", conn)
    conn.close()
    return df.to_dict(orient='records')

def compute_batting_order_stats(db_name="lineups.db"):
    conn = sqlite3.connect(db_name)
    df = pd.read_sql("SELECT * FROM daily_lineups", conn)
    conn.close()

    # Count games by hand
    counts = df.groupby(['player_id', 'player_name', 'pitcher_hand']).size().unstack(fill_value=0)

    # Calculate averages
    averages = df.groupby(['player_id', 'player_name', 'pitcher_hand'])['batting_order'].mean().unstack()

    # Final merged dataframe with game counts
    final = pd.DataFrame({
        'player_id': counts.index.get_level_values('player_id'),
        'player_name': counts.index.get_level_values('player_name'),
        'avg_order_vs_L': averages.get('L', pd.Series(index=averages.index)),
        'avg_order_vs_R': averages.get('R', pd.Series(index=averages.index)),
        'games_vs_L': counts.get('L', pd.Series(0, index=counts.index)),
        'games_vs_R': counts.get('R', pd.Series(0, index=counts.index))
    }).fillna('N/A')

    return final.to_dict(orient='records')

@app.route('/')
def index():
    # Load Savant expected stats data
    savant_data = load_savant_data()
    
    # Load lineup average order data
    lineup_data = compute_batting_order_stats()

    # Render template with both datasets
    return render_template("index.html", data=savant_data, lineup_data=lineup_data)

if __name__ == '__main__':
    app.run(debug=True)
