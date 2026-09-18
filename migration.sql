ALTER TABLE x_usernames
    MODIFY last_post_id VARCHAR(255) NULL,
    ADD COLUMN seen_ids TEXT NULL;

DELETE a FROM x_usernames a
JOIN x_usernames b
    ON a.user_id = b.user_id
    AND LOWER(a.x_username) = LOWER(b.x_username)
    AND a.id > b.id;