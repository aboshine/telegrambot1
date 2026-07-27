# telegrambot1

Production-oriented Telegram bot built with [aiogram 3.x](https://docs.aiogram.dev/) (async Python). Configuration comes from environment variables so secrets never belong in source control.

## Quick start

1. **Python 3.10+** is required (aiogram 3 uses modern typing and asyncio).

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example env file and set your token from [@BotFather](https://t.me/BotFather):

   ```bash
   copy .env.example .env
   ```

   Edit `.env` and set `BOT_TOKEN`.

5. Run the bot:

   ```bash
   python main.py
   ```

## Project layout

| Path | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `config.py` | Settings from env / `.env` |
| `handlers/` | Telegram update handlers |
| `requirements.txt` | Pinned Python dependencies |
| `.env.example` | Template for required env vars |
| `.gitignore` | Files Git should not track |

### `main.py`

Bootstraps the process:

- Loads settings via `get_settings()`.
- Configures structured logging to stdout (level from `LOG_LEVEL`).
- Creates `Bot` with HTML as the default parse mode.
- Creates `Dispatcher`, attaches the root router from `handlers`.
- Runs **long polling** (`dp.start_polling`), suitable for development and small deployments behind no fixed URL.
- Closes the HTTP session in a `finally` block so shutdown is clean.

For high-traffic production on a public HTTPS endpoint, you would switch to webhook mode; this skeleton keeps polling for simplicity.

### `config.py`

Defines a `Settings` class using **pydantic-settings**:

- Reads `BOT_TOKEN` and optional `LOG_LEVEL` from the environment.
- Also loads a local `.env` file if present (same variable names).
- `bot_token` is a `SecretStr` so logs and reprs do not accidentally print the token.
- `extra="ignore"` ignores unknown env keys so hosting platforms can inject unrelated variables safely.

If `BOT_TOKEN` is missing, startup fails immediately with a clear validation error.

### `handlers/` package

Telegram logic lives here, split by feature instead of one giant file.

- **`handlers/__init__.py`** — Defines a root `Router` and includes sub-routers (currently `commands`). Add new modules (e.g. `callbacks.py`, `admin.py`) and `include_router` them here.
- **`handlers/commands.py`** — Handles `/start` and `/help` using aiogram 3 filters (`CommandStart`, `Command`). Each handler is an `async def` receiving `Message`.

This matches aiogram 3’s recommended pattern: nested routers, filter-based routing, async handlers.

### `requirements.txt`

- **`aiogram`** — Telegram Bot API framework (3.x, asyncio, routers, filters).
- **`pydantic-settings`** — Typed configuration from environment and `.env` files.

Install with `pip install -r requirements.txt` for reproducible environments.

### `.env.example`

Documents required variables without real secrets. Copy to `.env` locally; **never commit `.env`**. CI and servers should inject `BOT_TOKEN` via the host’s secret store or environment configuration.

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Token from BotFather |
| `LOG_LEVEL` | No | Default `INFO`; use `DEBUG` when troubleshooting |

### `.gitignore`

Keeps virtualenvs, bytecode, IDE files, and especially **`.env`** out of Git so tokens are not pushed by mistake.

## Extending the bot

1. Add a new file under `handlers/` (e.g. `handlers/messages.py`) with its own `Router`.
2. Register it in `handlers/__init__.py` with `router.include_router(...)`.
3. Use aiogram filters (`F.text`, `Command`, callbacks, etc.) on handler functions.

## License

Use and modify as you like for your project.
