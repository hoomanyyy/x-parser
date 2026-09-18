import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

con = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME"),
    autocommit=True,
)


def get_cursor(dictionary=False):
    con.ping(reconnect=True, attempts=3, delay=2)
    return con.cursor(buffered=True, dictionary=dictionary)