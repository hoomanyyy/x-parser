import json

from database.mysql import get_cursor
from posts import newest_id


class SqlCommand:

    def __init__(self, userId=None):
        self.user_id = userId

    def _fetch(self, query, params=()):
        cursor = get_cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    def _run(self, query, params=()):
        cursor = get_cursor()
        try:
            cursor.execute(query, params)
            return cursor.rowcount
        finally:
            cursor.close()

    def select_all(self):
        return self._fetch(
            "SELECT id, x_username, user_id, last_post_id, seen_ids FROM x_usernames ORDER BY id"
        )

    def select_usernames(self):
        rows = self._fetch(
            "SELECT x_username FROM x_usernames WHERE user_id = %s ORDER BY x_username",
            (self.user_id,),
        )
        return [row["x_username"] for row in rows]

    def username_exists(self, username):
        rows = self._fetch(
            "SELECT id FROM x_usernames WHERE user_id = %s AND LOWER(x_username) = LOWER(%s) LIMIT 1",
            (self.user_id, username),
        )
        return bool(rows)

    def add_username(self, username, seen_ids):
        self._run(
            "INSERT INTO x_usernames (x_username, user_id, last_post_id, seen_ids) VALUES (%s, %s, %s, %s)",
            (username, self.user_id, newest_id(seen_ids), json.dumps(seen_ids)),
        )

    def remove_username(self, username):
        return self._run(
            "DELETE FROM x_usernames WHERE user_id = %s AND LOWER(x_username) = LOWER(%s)",
            (self.user_id, username),
        ) > 0

    def update_seen(self, row_id, seen_ids):
        self._run(
            "UPDATE x_usernames SET last_post_id = %s, seen_ids = %s WHERE id = %s",
            (newest_id(seen_ids), json.dumps(seen_ids), row_id),
        )