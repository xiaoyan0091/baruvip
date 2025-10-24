import sqlite3
from sqlite3 import Error
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_FILE = "bot_vvip/database.db"

def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Error as e:
        logger.error(f"Error connecting to database: {e}")
    return None

def setup_database():
    """Create tables in the database if they don't exist."""
    create_tables_sql = [
        """CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            vip_start_date TEXT,
            vip_end_date TEXT,
            vip_status TEXT DEFAULT 'expired',
            payment_proof_message_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY,
            channel_title TEXT,
            channel_username TEXT,
            is_active INTEGER DEFAULT 1
        );""",
        """CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );""",
        """CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            duration_months INTEGER,
            payment_date TEXT DEFAULT CURRENT_TIMESTAMP,
            approval_status TEXT DEFAULT 'pending',
            approval_message_id INTEGER,
            approved_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );""",
        """CREATE TABLE IF NOT EXISTS backup_history (
            backup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_date TEXT DEFAULT CURRENT_TIMESTAMP,
            file_size INTEGER,
            file_path TEXT,
            backup_type TEXT DEFAULT 'auto'
        );"""
    ]
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()
            for table_sql in create_tables_sql:
                c.execute(table_sql)
            conn.commit()
        except Error as e:
            logger.error(f"Error creating tables: {e}")
        finally:
            conn.close()

def get_or_create_user(user_id: int, username: str, full_name: str):
    """Get a user from the database or create them if they don't exist."""
    conn = create_connection()
    user = None
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = c.fetchone()
            if not user:
                c.execute(
                    "INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
                    (user_id, username, full_name)
                )
                conn.commit()
                c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user = c.fetchone()
                logger.info(f"New user created: {full_name} ({user_id})")
        except Error as e:
            logger.error(f"Database error in get_or_create_user: {e}")
        finally:
            conn.close()
    return user

def add_channel(channel_id: int, channel_title: str, channel_username: str):
    """Add a VVIP channel to the database."""
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute(
                "INSERT INTO channels (channel_id, channel_title, channel_username) VALUES (?, ?, ?)",
                (channel_id, channel_title, channel_username)
            )
            conn.commit()
            logger.info(f"Channel added: {channel_title} ({channel_id})")
            return True
        except Error as e:
            logger.error(f"Database error in add_channel: {e}")
            return False
        finally:
            conn.close()
    return False

def remove_channel(channel_id: int):
    """Remove a VVIP channel from the database."""
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
            conn.commit()
            logger.info(f"Channel removed: {channel_id}")
            return True
        except Error as e:
            logger.error(f"Database error in remove_channel: {e}")
            return False
        finally:
            conn.close()
    return False

def get_setting(key: str):
    """Get a setting value from the database."""
    conn = create_connection()
    setting = None
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = c.fetchone()
            if result:
                setting = result['value']
        except Error as e:
            logger.error(f"Database error in get_setting for key '{key}': {e}")
        finally:
            conn.close()
    return setting

def set_setting(key: str, value: str):
    """Set a setting value in the database."""
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
            return True
        except Error as e:
            logger.error(f"Database error in set_setting for key '{key}': {e}")
            return False
        finally:
            conn.close()
    return False

def create_payment_record(user_id: int, amount: int, duration_months: int):
    """Creates a new payment record and returns the payment_id."""
    conn = create_connection()
    payment_id = None
    if conn:
        try:
            c = conn.cursor()
            c.execute(
                "INSERT INTO payments (user_id, amount, duration_months) VALUES (?, ?, ?)",
                (user_id, amount, duration_months)
            )
            conn.commit()
            payment_id = c.lastrowid
        except Error as e:
            logger.error(f"Database error in create_payment_record: {e}")
        finally:
            conn.close()
    return payment_id

def update_payment_approval_message_id(payment_id: int, message_id: int):
    """Updates a payment record with the approval message ID."""
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute(
                "UPDATE payments SET approval_message_id = ? WHERE payment_id = ?",
                (message_id, payment_id)
            )
            conn.commit()
            return True
        except Error as e:
            logger.error(f"Database error in update_payment_approval_message_id: {e}")
            return False
        finally:
            conn.close()
    return False

def get_payment(payment_id: int):
    """Retrieves a payment record by its ID."""
    conn = create_connection()
    payment = None
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            payment = c.fetchone()
        except Error as e:
            logger.error(f"Database error in get_payment: {e}")
        finally:
            conn.close()
    return payment

def activate_vip(user_id: int, months: int):
    """Activates or extends a user's VIP subscription."""
    conn = create_connection()
    if conn:
        try:
            from datetime import datetime, timedelta

            c = conn.cursor()

            # Check if user already has an active subscription
            c.execute("SELECT vip_end_date FROM users WHERE user_id = ? AND vip_status = 'active'", (user_id,))
            result = c.fetchone()

            start_date = datetime.now()
            if result and result['vip_end_date']:
                # If active, extend from the current end date
                start_date = datetime.fromisoformat(result['vip_end_date'])

            end_date = start_date + timedelta(days=30 * months)

            c.execute(
                """UPDATE users
                   SET vip_status = 'active', vip_start_date = ?, vip_end_date = ?
                   WHERE user_id = ?""",
                (start_date.isoformat(), end_date.isoformat(), user_id)
            )
            conn.commit()
            logger.info(f"VIP activated for user {user_id} for {months} months.")
            return True
        except Error as e:
            logger.error(f"Database error in activate_vip: {e}")
            return False
        finally:
            conn.close()
    return False

def update_payment_status(payment_id: int, status: str):
    """Updates the approval status of a payment."""
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute(
                "UPDATE payments SET approval_status = ?, approved_date = CURRENT_TIMESTAMP WHERE payment_id = ?",
                (status, payment_id)
            )
            conn.commit()
            return True
        except Error as e:
            logger.error(f"Database error in update_payment_status: {e}")
            return False
        finally:
            conn.close()
    return False

def get_active_channels():
    """Retrieves all active VVIP channels."""
    conn = create_connection()
    channels = []
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM channels WHERE is_active = 1")
            channels = c.fetchall()
        except Error as e:
            logger.error(f"Database error in get_active_channels: {e}")
        finally:
            conn.close()
    return channels

def get_expired_vip_users():
    """Retrieves all users whose VIP has expired but are still marked as active."""
    conn = create_connection()
    users = []
    if conn:
        try:
            from datetime import datetime
            now = datetime.now().isoformat()
            c = conn.cursor()
            c.execute("SELECT user_id FROM users WHERE vip_status = 'active' AND vip_end_date < ?", (now,))
            users = c.fetchall()
        except Error as e:
            logger.error(f"Database error in get_expired_vip_users: {e}")
        finally:
            conn.close()
    return users

def update_user_vip_status(user_id: int, status: str):
    """Updates the vip_status for a specific user."""
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("UPDATE users SET vip_status = ? WHERE user_id = ?", (status, user_id))
            conn.commit()
            return True
        except Error as e:
            logger.error(f"Database error in update_user_vip_status: {e}")
            return False
        finally:
            conn.close()
    return False

def add_backup_record(file_size: int, file_path: str, backup_type: str):
    """Adds a new backup record to the database."""
    conn = create_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute(
                "INSERT INTO backup_history (file_size, file_path, backup_type) VALUES (?, ?, ?)",
                (file_size, file_path, backup_type)
            )
            conn.commit()
        except Error as e:
            logger.error(f"Database error in add_backup_record: {e}")
        finally:
            conn.close()

# Initialize the database on module load
setup_database()
