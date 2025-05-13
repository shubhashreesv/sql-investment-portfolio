from flask import Flask, request, jsonify
import sqlite3
import requests
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

API_KEY = "your-api-key"
BASE_URL = "https://finnhub.io/api/v1/quote"

# Setup DB
def get_db():
    conn = sqlite3.connect("portfolio.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/add", methods=["POST"])
def add_investment():
    data = request.json
    symbol = data["symbol"].upper()
    shares = int(data["shares"])
    buy_price = float(data["buy_price"])
    buy_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO investments (symbol, shares, buy_price, buy_date) VALUES (?, ?, ?, ?)",
                (symbol, shares, buy_price, buy_date))
    conn.commit()
    return jsonify({"message": "Investment added successfully"}), 201

@app.route("/portfolio", methods=["GET"])
def get_portfolio():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM investments")
    investments = cur.fetchall()

    result = []
    total_invested = 0
    total_value = 0

    for inv in investments:
        symbol = inv["symbol"]
        shares = inv["shares"]
        buy_price = inv["buy_price"]
        invested = shares * buy_price

        r = requests.get(f"{BASE_URL}?symbol={symbol}&token={API_KEY}")
        current_price = r.json().get("c", 0)
        value = shares * current_price
        profit_loss = value - invested

        result.append({
            "symbol": symbol,
            "shares": shares,
            "buy_price": buy_price,
            "current_price": current_price,
            "profit_loss": profit_loss
        })

        total_invested += invested
        total_value += value

    return jsonify({
        "portfolio": result,
        "total_invested": total_invested,
        "total_value": total_value,
        "total_profit_loss": total_value - total_invested
    })

if __name__ == "__main__":
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS investments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        shares INTEGER NOT NULL,
        buy_price REAL NOT NULL,
        buy_date TEXT NOT NULL
    )""")
    conn.close()
    app.run(debug=True)
