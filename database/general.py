import sqlite3, os
from dotenv import load_dotenv
from contextlib import contextmanager


load_dotenv()
DB_PATH = os.getenv("DB_PATH")


@contextmanager
def get_cursor() -> sqlite3.Cursor:
    """
    Context manager for sqlite.Cursor
    """

    with sqlite3.connect(DB_PATH) as conn:
        try:
            yield conn.cursor()
            conn.commit()
        except sqlite3.DatabaseError:
            conn.rollback()


def init_db() -> None:
    """
    Initialization db: Create db and tables (if not exists yet)
    """

    check_db_dir()

    with get_cursor() as cursor:

        # Table users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                public_key TEXT UNIQUE NOT NULL,
                refresh_token TEXT UNIQUE
            );
        """)

        # Table notes
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        header TEXT NOT NULL,
                        content TEXT NOT NULL,
                        tags TEXT,
                        aes_key TEXT UNIQUE NOT NULL,
                        from_user_id INTEGER NOT NULL,
                        created_time TEXT NOT NULL,
                        active_time DATETIME,
                        last_edit_time TEXT,
                        last_edit_user INTEGER,
                        FOREIGN KEY (from_user_id) REFERENCES users(id)
                    );
                """)

        # Table statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                user_id INTEGER NOT NULL,
                count_creating_note INTEGER NOT NULL,
                count_reading_note INTEGER NOT NULL,
                count_deleting_note INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        # Table accesses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accesses (
                note_id INTEGER,
                user_id INTEGER,
                permission INTEGER NOT NULL,
                key TEXT UNIQUE NOT NULL,
                FOREIGN KEY (note_id) REFERENCES notes(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                PRIMARY KEY (note_id, user_id)
            );
        """)

        # Table restore password
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_restore (
                user_id INTEGER,
                key BLOB UNIQUE NOT NULL,
                expired_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        # Table shared by link
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_notes (
                note_id INTEGER,
                owner_id INTEGER,
                key TEXT UNIQUE NOT NULL,
                link TEXT UNIQUE NOT NULL,
                FOREIGN KEY (note_id) REFERENCES notes(id)
                FOREIGN KEY (owner_id) REFERENCES users(id)
            );
        """)


def check_existing_email(email: str) -> bool:
    """
    Checking if email is already registered
    """

    with get_cursor() as cursor:

        cursor.execute("""
            SELECT * FROM users WHERE email = ?
        """, (email, ))

        user = cursor.fetchone()
        if user:
            return True

    return False


def check_db_dir() -> None:
    if not os.path.exists("db"):
        os.mkdir("db")
