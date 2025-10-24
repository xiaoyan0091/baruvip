from flask import Flask, render_template, jsonify, request, abort
import sqlite3
import os
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qsl
from .utils import is_valid_init_data

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def authenticate_request():
    init_data = request.headers.get("X-Telegram-Init-Data")

    if not init_data:
        abort(403, description="Access Denied: Missing InitData")

    if not is_valid_init_data(init_data, BOT_TOKEN):
        abort(403, description="Access Denied: Invalid InitData")

    try:
        user_info = dict(parse_qsl(init_data)).get('user')
        user_id = json.loads(user_info).get('id')
        if user_id != OWNER_ID:
            abort(403, description="Access Denied: You are not the owner.")
    except (json.JSONDecodeError, KeyError, TypeError):
        abort(403, description="Access Denied: Invalid user data in InitData")

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    conn = get_db_connection()

    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    vip_active = conn.execute("SELECT COUNT(*) FROM users WHERE vip_status = 'active'").fetchone()[0]
    vip_expired = conn.execute("SELECT COUNT(*) FROM users WHERE vip_status = 'expired'").fetchone()[0]
    pending_approval = conn.execute("SELECT COUNT(*) FROM payments WHERE approval_status = 'pending'").fetchone()[0]

    # User registration chart data (last 7 days)
    user_chart_data = {'labels': [], 'data': []}
    for i in range(6, -1, -1):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        user_chart_data['labels'].append(date.strftime('%a'))
        count = conn.execute('SELECT COUNT(*) FROM users WHERE date(created_at) = ?', (date_str,)).fetchone()[0]
        user_chart_data['data'].append(count)

    conn.close()

    return jsonify({
        'total_users': total_users,
        'vip_active': vip_active,
        'vip_expired': vip_expired,
        'pending_approval': pending_approval,
        'user_chart': user_chart_data,
        'status_chart': {
            'labels': ['Active', 'Expired', 'Pending'],
            'data': [vip_active, vip_expired, pending_approval]
        }
    })

@app.route('/api/users')
def api_users():
    conn = get_db_connection()
    users = conn.execute('SELECT user_id, full_name, username, vip_start_date, vip_end_date, vip_status FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
