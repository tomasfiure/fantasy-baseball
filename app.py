from flask import Flask, render_template
import sqlite3
import pandas as pd

app = Flask(__name__)

def load_data():
    conn = sqlite3.connect("hitters_stats.db")
    df = pd.read_sql_query("SELECT * FROM hitters", conn)
    conn.close()
    return df

@app.route('/')
def index():
    df = load_data()
    return render_template("index.html", tables=[df.to_html(classes='data')], titles=df.columns.values)

if __name__ == '__main__':
    app.run(debug=True)
