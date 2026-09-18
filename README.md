# X (Twitter) Monitor — Telegram Bot

A Telegram bot that watches X (Twitter) accounts and sends you a message the moment they publish a new post. It reads each account through a self-hosted [RSSHub](https://github.com/DIYgod/RSSHub) feed, tracks what every user has already seen in MySQL, and pushes only genuinely new posts.

The whole stack — RSSHub, the database, and the bot — runs in a single Docker container.

---

## Features

- **Per-user watch lists** — each Telegram user manages their own set of X accounts.
- **Reliable new-post detection** — compares numeric status IDs and tracks the last 200 seen posts per account, so it handles pinned tweets, several posts between checks, deleted posts, and retweets of old posts without missing or duplicating notifications.
- **Shared fetching** — when several users watch the same account, it is fetched once per cycle.
- **Resilient delivery** — a post that fails to send (network error) is retried on the next check; a user who blocked the bot is skipped; over-long posts are trimmed.
- **Inline keyboard** — add, remove, and list accounts with buttons or slash commands.
- **Auto-recovering database connection** — reconnects transparently if MySQL drops the connection.
- **Zero cache by default** — RSSHub caching is disabled so posts surface as fast as X allows.

---

## How it works

```
Telegram  ◄──►  Bot (python-telegram-bot)  ──►  RSSHub  ──►  X (Twitter)
                        │
                        ▼
                     MySQL  (users, watch lists, seen post IDs)
```

1. A scheduled job runs every `CHECK_INTERVAL` seconds.
2. For each watched account, the bot requests the RSSHub feed and parses it with `feedparser`.
3. It compares the feed against the `seen_ids` stored for that user and account.
4. Any post that is new (unseen and either above the last known post in the feed, or with a higher status ID) is sent to the user, oldest first.
5. The seen list is updated only after a successful send.

---

## Tech stack

| Layer            | Technology                                   |
| ---------------- | -------------------------------------------- |
| Bot framework    | python-telegram-bot (v22, with JobQueue)     |
| Feed source      | RSSHub (self-hosted)                          |
| Feed parsing     | feedparser                                    |
| HTTP             | requests                                       |
| Database         | MySQL / MariaDB (`mysql-connector-python`)    |
| Runtime          | Python 3.11+                                   |
| Packaging        | Docker (single container via `start.sh`)      |

---

## Project structure

```
.
├── server.py          # Bot entry point: handlers, scheduled check loop, delivery
├── posts.py           # RSSHub fetch + new-post detection logic
├── sqlCommand.py      # Database queries (watch lists, seen IDs)
├── auth.py            # User registration
├── database/
│   └── mysql.py       # Connection + auto-reconnect
├── migration.sql      # Schema migration for existing databases
├── requirements.txt
├── Dockerfile         # RSSHub image + Python + MariaDB + bot
├── start.sh           # Orchestrates RSSHub, DB, and bot in one container
└── .dockerignore
```

---

## Prerequisites

- A **Telegram bot token** from [@BotFather](https://t.me/BotFather).
- An **X (Twitter) auth token** for RSSHub. RSSHub needs a valid `auth_token` cookie to read X; without it, X routes fail. See the [RSSHub X/Twitter docs](https://docs.rsshub.app/routes/social-media#twitter).
- **Docker** (recommended), or Python 3.11+ and a running MySQL/MariaDB plus RSSHub if you run it manually.

---

## Configuration

Create a `.env` file. Do **not** wrap values in quotes — Docker treats quotes as part of the value.

| Variable             | Required | Default       | Description                                                        |
| -------------------- | -------- | ------------- | ------------------------------------------------------------------ |
| `API_TOKEN`          | yes      | —             | Telegram bot token from BotFather.                                 |
| `TWITTER_AUTH_TOKEN` | yes\*    | —             | X `auth_token` cookie used by RSSHub. \*X routes fail without it.  |
| `DB_NAME`            | no       | `xbot`        | Database name.                                                     |
| `DB_USER`            | no       | `xbot`        | Database user (must not be `root`).                                |
| `DB_PASS`            | yes      | —             | Database password.                                                 |
| `CHECK_INTERVAL`     | no       | `30`          | Seconds between checks. Lower values hit X harder — see below.     |
| `FETCH_CONCURRENCY`  | no       | `3`           | How many accounts to fetch in parallel per cycle.                  |
| `DB_HOST`            | no       | auto          | Set automatically in Docker. Point to an external DB if needed.    |
| `DB_PORT`            | no       | `3306`        | Database port.                                                     |
| `BASE_URL`           | no       | auto          | RSSHub base URL. Set automatically in Docker.                     |

In Docker, `BASE_URL` and `DB_HOST` are configured for you. Add any RSSHub variables you use (e.g. `PROXY_URI`) to the same `.env`.

---

## Run with Docker (recommended)

```bash
# 1. Build the image
docker build -t x-monitor .

# 2. Run it (data persists in a named volume)
docker run -d \
  --name x-monitor \
  --restart unless-stopped \
  --env-file .env \
  -v x-monitor-db:/var/lib/mysql \
  x-monitor

# 3. Follow the logs
docker logs -f x-monitor
```

To update after a code change:

```bash
docker build -t x-monitor .
docker rm -f x-monitor
docker run -d --name x-monitor --restart unless-stopped --env-file .env -v x-monitor-db:/var/lib/mysql x-monitor
```

The database lives in the `x-monitor-db` volume and survives rebuilds.

**Using an external MySQL** (for example one on the host): set `DB_HOST=host.docker.internal` in `.env`. The embedded database will then not start, and the external user must be allowed to connect from outside `localhost`.

To browse feeds in your own browser, add `-p 1200:1200` to the `run` command.

---

## Run without Docker

1. Start RSSHub separately and set `BASE_URL` to its address (e.g. `http://127.0.0.1:1200`). Disable caching with `CACHE_TYPE=` in RSSHub's environment.
2. Create a MySQL/MariaDB database and user.
3. Apply `migration.sql` **only if** you are upgrading an existing database (it adds the `seen_ids` column and removes duplicate rows).
4. Install dependencies and run:

```bash
pip install -r requirements.txt
python server.py
```

---

## Bot commands

| Command           | Action                                      |
| ----------------- | ------------------------------------------- |
| `/start`          | Register and show the main menu.            |
| `/addusername`    | Add an X account to your watch list.        |
| `/removeusername` | Remove an account (choose from a keyboard). |
| `/myusernames`    | List the accounts you are watching.         |
| `/help`           | Show the command list.                      |

You can also paste a full profile URL (e.g. `https://x.com/username`) when adding an account.

---

## Troubleshooting

**New posts arrive with a delay.** This is almost always RSSHub caching, not the bot. RSSHub caches responses for 5 minutes by default, so lowering `CHECK_INTERVAL` alone changes nothing. This project disables the cache (`CACHE_TYPE=`) so posts surface as fast as X returns them. If you run RSSHub yourself elsewhere, set `CACHE_TYPE=` (no cache) or `CACHE_EXPIRE=60` there.

**No posts at all / `RSS error` in the logs.** Check that `TWITTER_AUTH_TOKEN` is valid. Also open the feed URL in a browser: if the new post is not there, the problem is the feed source, not the bot.

**Rate limiting.** Every check with caching off is a live request to X. A very low `CHECK_INTERVAL` combined with many accounts can get the account behind `TWITTER_AUTH_TOKEN` throttled or locked. Values below 30 seconds are not recommended; raise the interval as you add more accounts.

---

## Notes & limitations

- Detection speed is ultimately bounded by RSSHub and X, not by the bot.
- The embedded database starts empty; watch lists are added through the bot.
- Runs a single bot instance — running two at once causes a Telegram polling conflict.

---

## License

No license file is included yet. Add one (for example MIT) if you intend others to reuse this code.
---

## install in linux server

```bash
git clone https://github.com/hoomanyyy/x-parser.git
cd x-parser

chmod +x install.sh start.sh

./install.sh
