import sys
import types

# ⚡ Evita erro de áudio no Render
sys.modules['audioop'] = types.ModuleType('audioop')

import os
import discord
from discord.ext import commands
from flask import Flask, jsonify
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import aiohttp

# ==========================
# Configurações
# ==========================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
AUTOPING = os.getenv("AUTOPING")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

intents = discord.Intents.all()

# ==========================
# Flask
# ==========================

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot de Pagamentos Unibot rodando!"

@app.route("/status")
def status():
    return jsonify({"status": "online", "bot": "Unibot Pagamentos", "version": "1.0"})


# ==========================
# Discord Bot
# ==========================

class CustomBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✅ Conectado ao Supabase!")
        except Exception as e:
            print(f"❌ Erro no Supabase: {e}")
            self.supabase = None

    async def setup_hook(self):
        os.makedirs("comprovantes", exist_ok=True)
        print("📁 Diretório 'comprovantes' criado/verificado")

        # Carrega cogs
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ Cog {filename[:-3]} carregado")
                except Exception as e:
                    print(f"❌ Erro ao carregar cog {filename}: {e}")

        asyncio.create_task(self.auto_ping())

    async def on_ready(self):
        print("="*50)
        print(f"✅ BOT ONLINE! {self.user} | ID: {self.user.id}")
        print(f"🌐 Servidores: {len(self.guilds)}")
        print("="*50)

    async def auto_ping(self):
        await asyncio.sleep(60)
        while True:
            if AUTOPING:
                try:
                    async with aiohttp.ClientSession() as session:
                        await session.get(AUTOPING)
                        print("🔄 AutoPing enviado")
                except Exception as e:
                    print(f"❌ Erro no AutoPing: {e}")
            await asyncio.sleep(300)


bot = CustomBot(command_prefix="!", intents=intents)
bot.remove_command("help")


# ==========================
# Run Flask + Discord juntos
# ==========================

async def start_bot():
    await bot.start(TOKEN)

async def start_flask():
    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 10000))}"]
    await serve(app, config)

async def main():
    await asyncio.gather(start_bot(), start_flask())

if __name__ == "__main__":
    asyncio.run(main())
