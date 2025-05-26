import pandas as pd
import sqlite3

# Mock data
data = {
    'name': ['Player A', 'Player B'],
    'team': ['NYM', 'LAD'],
    'xwOBA': [0.350, 0.315],
    'xSLG': [0.525, 0.488],
    'avg_order_vs_rhp': [3.1, 5.6],
    'avg_order_vs_lhp': [1.9, 6.0],
    'platoon_flag': ['Both', 'RHP-only']
}
df = pd.DataFrame(data)

conn = sqlite3.connect("hitters_stats.db")
df.to_sql("hitters", conn, if_exists="replace", index=False)
conn.close()
