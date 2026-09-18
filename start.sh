#!/usr/bin/env bash
set -Eeuo pipefail

RSSHUB_PORT=1200
export PORT="$RSSHUB_PORT"
export BASE_URL="http://127.0.0.1:$RSSHUB_PORT"
export DB_PORT="${DB_PORT:-3306}"
export DB_NAME="${DB_NAME:-xbot}"
export DB_USER="${DB_USER:-xbot}"

pids=()

log() {
    printf '[start] %s\n' "$*"
}

fail() {
    printf '[start] ERROR: %s\n' "$*" >&2
    exit 1
}

shutdown() {
    trap - EXIT TERM INT
    if [ "${pids[*]:-}" != "" ]; then
        log "stopping services..."
        kill -TERM "${pids[@]}" 2>/dev/null || true
        wait || true
    fi
}

trap shutdown EXIT
trap 'exit 0' TERM INT

wait_for_port() {
    local host=$1 port=$2 seconds=$3 name=$4
    log "waiting for $name at $host:$port ..."
    for _ in $(seq "$seconds"); do
        if (exec 3<>"/dev/tcp/$host/$port") 2>/dev/null; then
            log "$name is ready"
            return 0
        fi
        sleep 1
    done
    fail "$name did not start within $seconds seconds"
}

sql_text() {
    local value=${1//\\/\\\\}
    printf '%s' "${value//\'/\'\'}"
}

create_tables() {
    local pass
    pass=$(sql_text "$DB_PASS")

    log "creating tables if not exist..."


    mariadb --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" --password="$DB_PASS" "$DB_NAME" <<SQL
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL UNIQUE,
    chat_id BIGINT NOT NULL,
    username VARCHAR(255) NULL,
    first_name VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS x_usernames (
    id INT AUTO_INCREMENT PRIMARY KEY,
    x_username VARCHAR(255) NOT NULL,
    user_id BIGINT NOT NULL,
    last_post_id VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP(),
    seen_ids TEXT DEFAULT NULL,
    UNIQUE KEY unique_user_username (user_id, x_username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
SQL

    if [ $? -eq 0 ]; then
        log "tables are ready"
    else
        fail "failed to create tables. check DB credentials and permissions"
    fi
}

start_embedded_db() {
    [[ "$DB_NAME" =~ ^[A-Za-z0-9_]+$ ]] || fail "DB_NAME may only contain letters, digits and _"
    [[ "$DB_USER" =~ ^[A-Za-z0-9_]+$ ]] || fail "DB_USER may only contain letters, digits and _"
    [ "$DB_USER" != "root" ] || fail "set DB_USER to something other than root"
    [ -n "${DB_PASS:-}" ] || fail "DB_PASS is not set"

    mkdir -p /run/mysqld /var/lib/mysql
    chown mysql:mysql /run/mysqld /var/lib/mysql

    if [ ! -d /var/lib/mysql/mysql ]; then
        log "initializing embedded database..."
        mariadb-install-db --user=mysql --datadir=/var/lib/mysql \
            --auth-root-authentication-method=socket --skip-test-db > /dev/null
    fi

    mariadbd --user=mysql --datadir=/var/lib/mysql \
        --bind-address=127.0.0.1 --port="$DB_PORT" &
    pids+=("$!")

    for _ in $(seq 60); do
        if mariadb-admin --protocol=socket ping --silent > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    mariadb-admin --protocol=socket ping --silent > /dev/null 2>&1 || fail "embedded database did not start"

    local pass
    pass=$(sql_text "$DB_PASS")

    mariadb --protocol=socket <<SQL
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$pass';
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$pass';
ALTER USER '$DB_USER'@'localhost' IDENTIFIED BY '$pass';
ALTER USER '$DB_USER'@'%' IDENTIFIED BY '$pass';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'%';
FLUSH PRIVILEGES;
SQL

    export DB_HOST=127.0.0.1
    create_tables
    log "embedded database is ready"
}


[ -n "${API_TOKEN:-}" ] || fail "API_TOKEN is not set"
[ -n "${DB_PASS:-}" ] || fail "DB_PASS is not set"
[ -n "${DB_NAME:-}" ] || fail "DB_NAME is not set"
[ -n "${DB_USER:-}" ] || fail "DB_USER is not set"

if [ -z "${TWITTER_AUTH_TOKEN:-}" ]; then
    log "WARNING: TWITTER_AUTH_TOKEN is not set → X routes in RSSHub will fail"
fi

if [ -z "${GOOGLE_API_KEY:-}" ]; then
    log "WARNING: GOOGLE_API_KEY is not set → translation will not work"
fi

case "${DB_HOST:-}" in
    ""|localhost|127.0.0.1)
        log "using EMBEDDED database"
        start_embedded_db
        ;;
    *)
        log "using EXTERNAL database at $DB_HOST:$DB_PORT"
        wait_for_port "$DB_HOST" "$DB_PORT" 60 "database"
        create_tables
        ;;
esac

log "starting RSSHub..."
(cd "${RSSHUB_DIR:-/app}" && exec npm run start) &
pids+=("$!")
wait_for_port 127.0.0.1 "$RSSHUB_PORT" 180 "RSSHub"

log "starting bot..."
(cd /bot && exec /opt/venv/bin/python server.py) &
pids+=("$!")

set +e
wait -n
status=$?
log "a service stopped with exit code $status"
exit "$status"