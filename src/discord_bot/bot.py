import os
import asyncio
from typing import Optional
import logging
from dotenv import load_dotenv
import aiohttp
import discord
from discord.ext import commands
import re

load_dotenv()

LOG = logging.getLogger("discord_bot")
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOG.setLevel(logging.INFO)

# Constants
API_TIMEOUT = 30
MAX_DISCORD_MESSAGE_LENGTH = 1900

# Environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RAG_API_URL = os.getenv("RAG_API_URL", "http://127.0.0.1:8000/api/v1/nlp/index/answer")
PROJECT_ID = os.getenv("RAG_PROJECT_ID", "15")
DEFAULT_LIMIT = int(os.getenv("RAG_DEFAULT_LIMIT", "3"))
COMMAND_PREFIX = os.getenv("DISCORD_PREFIX", "!")

async def fetch_rag_answer(question: str) -> Optional[dict]:
    """Fetch answer from RAG API with retries and exponential backoff."""
    url = f"{RAG_API_URL}/{PROJECT_ID}"
    payload = {"text": question, "limit": DEFAULT_LIMIT}
    
    attempts = 3
    backoff = 0.5
    
    for attempt in range(1, attempts + 1):
        try:
            timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        LOG.error(f"RAG API error {resp.status}: {error_text}")
                        return {"error": f"API error: {resp.status}", "status": resp.status}
                    
                    result = await resp.json()
                    return result
                    
        except asyncio.TimeoutError:
            LOG.warning("RAG API request timed out (attempt %d/%d)", attempt, attempts)
            if attempt == attempts:
                return {"error": "Request timed out", "timeout": True}
                
        except aiohttp.ClientConnectorError as e:
            LOG.error(f"Cannot connect to RAG API at {url}: {e}")
            if attempt == attempts:
                return {"error": f"Cannot connect to API. Is it running at {url}?"}
                
        except Exception as e:
            LOG.warning("RAG API request failed (attempt %d/%d): %s", attempt, attempts, e)
            if attempt == attempts:
                LOG.exception("Request to RAG API failed on final attempt")
                return {"error": str(e)}
        
        await asyncio.sleep(backoff)
        backoff *= 2
    
    return None

async def send_long_reply(ctx, text: str):
    """Send a long message split into multiple Discord replies if necessary."""
    if not text:
        return
    
    chunks = [text[i:i+MAX_DISCORD_MESSAGE_LENGTH] 
              for i in range(0, len(text), MAX_DISCORD_MESSAGE_LENGTH)]
    
    for chunk in chunks:
        await ctx.reply(chunk)
        await asyncio.sleep(0.1)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

def extract_smart_answer(answer_text: str, question: str) -> str:
    """
    SMART ANSWER EXTRACTION - The key function that makes answers concise!
    This analyzes the question type and extracts only the relevant sentence.
    """
    question_lower = question.lower().strip()
    
    # Remove all markdown headers (##, ###, etc.)
    cleaned_text = re.sub(r'^#{1,6}\s+.*$', '', answer_text, flags=re.MULTILINE)
    
    # Split into sentences (handle . ? !)
    sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    # === QUESTION TYPE DETECTION ===
    
    # "HOW MANY" questions - find the number
    if question_lower.startswith('how many'):
        keywords = question_lower.replace('how many', '').replace('?', '').strip().split()
        for sentence in sentences:
            # Look for numbers or number words
            has_number = re.search(r'\b\d+\b|\beleven\b|\btwelve\b', sentence.lower())
            # Check relevance to question
            has_keywords = any(kw in sentence.lower() for kw in keywords if len(kw) > 3)
            
            if has_number and has_keywords:
                return sentence
    
    # "WHERE" questions - find location
    elif question_lower.startswith('where'):
        keywords = question_lower.replace('where', '').replace('do', '').replace('does', '').replace('?', '').strip().split()
        
        for sentence in sentences:
            # Look for location indicators and check relevance
            has_location = re.search(r'\bat\s|in\s|near\s|meet\s+at\s', sentence.lower())
            has_keywords = any(kw in sentence.lower() for kw in keywords if len(kw) > 3)
            
            if has_location and has_keywords:
                return sentence
    
    # "WHAT IS/ARE" questions
    elif question_lower.startswith(('what is', 'what are', 'what')):
        # Usually first 1-2 sentences contain the definition
        relevant = '. '.join(sentences[:2])
        return relevant
    
    # "WHICH" questions
    elif question_lower.startswith('which'):
        keywords = question_lower.replace('which', '').replace('?', '').strip().split()
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in keywords if len(kw) > 3):
                return sentence
    
    # "WHEN" questions
    elif question_lower.startswith('when'):
        keywords = question_lower.replace('when', '').replace('?', '').strip().split()
        for sentence in sentences:
            # Look for dates/times
            has_time = re.search(r'\b\d{4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b', sentence)
            has_keywords = any(kw in sentence.lower() for kw in keywords if len(kw) > 3)
            
            if has_time and has_keywords:
                return sentence
    
    # DEFAULT: Find most relevant sentence
    keywords = [w for w in question_lower.replace('?', '').split() if len(w) > 3]
    
    for sentence in sentences:
        if any(kw in sentence.lower() for kw in keywords):
            return sentence
    
    # FALLBACK: First substantial sentence
    if sentences:
        return sentences[0]
    
    return cleaned_text[:300].strip()

async def handle_question(ctx, question: str, show_full: bool = False):
    """Handle question with smart extraction."""
    async with ctx.channel.typing():
        data = await fetch_rag_answer(question)
    
    if not data:
        await ctx.reply("❌ Failed to get a response from the RAG API.")
        return
    
    if "error" in data:
        if data.get("timeout"):
            await ctx.reply("⏱️ Request timed out. Please try again.")
        else:
            await ctx.reply(f"❌ Error: {data.get('error', 'Unknown error')}")
        return
    
    answer_text = data.get("answer", "")
    
    if not answer_text or "Could not generate" in answer_text:
        await ctx.reply("❓ I couldn't find an answer in the available documents.")
        return
    
    if show_full:
        # Show full answer for debugging
        await send_long_reply(ctx, f"**Full Answer:**\n{answer_text}")
    else:
        # Extract smart, concise answer
        smart_answer = extract_smart_answer(answer_text, question)
        await send_long_reply(ctx, f"**💡 Answer:**\n{smart_answer}")

@bot.event
async def on_ready():
    LOG.info(f"✅ Bot logged in as {bot.user} (id: {bot.user.id})")
    LOG.info(f"Command prefix: {COMMAND_PREFIX}")
    LOG.info(f"RAG API URL: {RAG_API_URL}/{PROJECT_ID}")
    LOG.info("Bot is ready!")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    LOG.error(f"Command error: {error}", exc_info=error)
    await ctx.reply(f"❌ An error occurred: {str(error)}")

@bot.event
async def on_message(message):
    """Handle both commands and mentions."""
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)
    
    # If bot is mentioned (not a command), treat as question
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        question = message.content.replace(f'<@{bot.user.id}>', '').strip()
        question = question.replace(f'<@!{bot.user.id}>', '').strip()
        
        if question:
            await handle_question(message, question)

@bot.command(name="ask", help="Ask a question with concise answer")
async def ask(ctx, *, question: str):
    """Get a smart, concise answer."""
    await handle_question(ctx, question, show_full=False)

@bot.command(name="ask_full", help="Ask a question with full context")
async def ask_full(ctx, *, question: str):
    """Get the full RAG answer with all context."""
    await handle_question(ctx, question, show_full=True)

@bot.command(name="ping", help="Check bot latency")
async def ping(ctx):
    """Check if bot is responsive."""
    await ctx.reply(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")

@bot.command(name="help_bot", help="Show bot usage")
async def help_bot(ctx):
    """Show usage instructions."""
    help_text = f"""
**🤖 RAG FAQ Bot - Usage Guide**

**Commands:**
• `{COMMAND_PREFIX}ask <question>` - Get concise answer
• `{COMMAND_PREFIX}ask_full <question>` - Get full context
• `{COMMAND_PREFIX}ping` - Check bot status
• `{COMMAND_PREFIX}debug <question>` - See raw API response

**Mention Bot:**
• `@{bot.user.name} <question>` - Ask without command

**Examples:**
```
{COMMAND_PREFIX}ask Where do the White Nile and Blue Nile meet?
{COMMAND_PREFIX}ask How many countries does the Nile cover?
@{bot.user.name} What is the length of the Nile River?
```

**Settings:**
• API: {RAG_API_URL}/{PROJECT_ID}
• Limit: {DEFAULT_LIMIT} documents
"""
    await ctx.reply(help_text)

@bot.command(name="debug", help="Show raw API response")
async def debug(ctx, *, question: str):
    """Debug command to see raw API data."""
    async with ctx.channel.typing():
        data = await fetch_rag_answer(question)
    
    if not data:
        await ctx.reply("Failed to get API response.")
        return
    
    import json
    response_json = json.dumps(data, indent=2, ensure_ascii=False)
    
    if len(response_json) > 1800:
        response_json = response_json[:1800] + "\n... (truncated)"
    
    await ctx.reply(f"```json\n{response_json}\n```")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        LOG.error("❌ DISCORD_TOKEN not set in environment")
        raise SystemExit(1)
    
    LOG.info("Starting bot...")
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        LOG.exception(f"Failed to start bot: {e}")