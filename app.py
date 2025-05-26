from flask import Flask, render_template
import sqlite3
import pandas as pd

app = Flask(__name__)

def load_data():
    conn = sqlite3.connect("hitters_stats.db")
    df = pd.read_sql_query("SELECT * FROM hitters", conn)
    conn.close()
    return df.to_dict(orient='records')

@app.route('/')
def index():
    data = load_data()
    return render_template("index.html", data=data)

if __name__ == '__main__':
    app.run(debug=True)
