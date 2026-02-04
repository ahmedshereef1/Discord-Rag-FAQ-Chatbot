Discord RAG FAQ Bot

Overview
- Minimal Discord bot that forwards questions to your local mini-RAG API and returns answers.

Setup
1. Create a Discord application and bot in the Discord Developer Portal.
   - Enable the "Message Content Intent" under Bot -> Privileged Gateway Intents if you use prefix commands.
   - Invite the bot to your server with required scopes (bot + applications.commands if using slash commands).

2. Create a `.env` file in `src/discord_bot/` with:

```
DISCORD_TOKEN=your_bot_token_here
RAG_API_URL=http://127.0.0.1:8000/api/v1/nlp/index/answer
RAG_PROJECT_ID=13  # set this to the project id you want the bot to query (any integer)
RAG_DEFAULT_LIMIT=5
DISCORD_PREFIX=!
```

3. Install dependencies (prefer a virtualenv):

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r src/discord_bot/requirements.txt
```

Run

```bash
cd src/discord_bot
python bot.py
```

Usage
- In Discord, send:
  - `!ask How can datasheets help with responsible AI?`
- The bot will reply with the answer from your running mini-RAG API.

Notes
- The bot uses `message_content` intent to read prefix commands. For production, consider using slash commands.
- If your mini-RAG app runs on a different host/port, update `RAG_API_URL` accordingly.
- Adjust `RAG_PROJECT_ID` to target the correct project index in your RAG service.
  - `RAG_PROJECT_ID`: set this to any integer representing the project you want the bot to query (for example `13`).
