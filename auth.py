import logging
from database.mysql import get_cursor

logger = logging.getLogger(__name__)

class Auth:
    def __init__(
        self,
        telegram_user_id,
        user_chat_id,
        username=None,
        first_name=None
    ):
        self.telegram_user_id = telegram_user_id
        self.user_chat_id = user_chat_id
        self.username = username
        self.first_name = first_name

    def user_exists(self):
        cursor = None

        try:
            cursor = get_cursor()
            cursor.execute(
                "SELECT id FROM users WHERE telegram_user_id = %s LIMIT 1",
                (self.telegram_user_id,),
            )
            return cursor.fetchone() is not None

        except Exception as e:
            logger.error("Check user error: %s", e)
            return False

        finally:
            if cursor:
                cursor.close()

    def add_user(self):
        cursor = None

        try:
            cursor = get_cursor()
            cursor.execute(
                """
                INSERT INTO users (telegram_user_id, chat_id, username, first_name)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    self.telegram_user_id,
                    self.user_chat_id,
                    self.username,
                    self.first_name,
                ),
            )
            logger.info("User registered: %s", self.telegram_user_id)
            return True

        except Exception as e:
            logger.error("Add user error: %s", e)
            return False

        finally:
            if cursor:
                cursor.close()