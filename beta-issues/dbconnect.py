import sqlite3
# from __init__ import app


def connection():
    conn = sqlite3.connect('mydb.db')
    c = conn.cursor()
    # rv.row_factory = sqlite3.Row
    return c, conn