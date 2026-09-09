"""
Authentication Module
----------------------
Simple email + password based authentication using SQLite (Python's
built-in database, no extra setup needed).

SECURITY NOTE: Passwords are never stored in plain text. We use
PBKDF2-HMAC-SHA256 with a random salt per user (Python's built-in
`hashlib` - no extra dependency needed) to hash passwords before
storing them. This is a standard, industry-recognized approach for
password storage.
"""

import sqlite3
import hashlib
import os
import re

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")


def init_db():
    """Users table banata hai agar exist nahi karti."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def is_valid_email(email):
    """Basic email format validation."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


def hash_password(password, salt=None):
    """
    Password ko PBKDF2-HMAC-SHA256 se hash karta hai (100,000 iterations,
    ek standard security practice). Salt random hota hai har user ke liye,
    isse same password wale do users ka hash bhi alag-alag hoga.
    """
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000
    )
    return hashed.hex(), salt


def signup(email, password):
    """
    Naya user register karta hai.
    Returns: (success: bool, message: str)
    """
    email = email.strip().lower()

    if not is_valid_email(email):
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return False, "An account with this email already exists. Please log in instead."

    password_hash, salt = hash_password(password)
    cursor.execute(
        "INSERT INTO users (email, password_hash, salt) VALUES (?, ?, ?)",
        (email, password_hash, salt)
    )
    conn.commit()
    conn.close()
    return True, "Account created successfully!"


def login(email, password):
    """
    User credentials verify karta hai.
    Returns: (success: bool, message: str)
    """
    email = email.strip().lower()

    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, salt FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False, "No account found with this email. Please sign up first."

    stored_hash, salt = row
    attempted_hash, _ = hash_password(password, salt)

    if attempted_hash == stored_hash:
        return True, "Login successful!"
    else:
        return False, "Incorrect password. Please try again."