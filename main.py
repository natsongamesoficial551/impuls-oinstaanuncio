import sys, types
# ⚡ Patch para "enganar" import de audioop e desativar voice/audio
sys.modules['audioop'] = types.ModuleType('audioop')

import os, asyncio
import discord
from discord.ext import commands
from flask import Flask, jsonify
from dotenv import load_dotenv
from supabase import create_client, Client
import aiohttp
from starlette.middleware.wsgi import WSGIMiddleware

# ==========================
# 🔧 Configurações Iniciais
# ==========================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
AUTOPING = os.getenv("AUTOPING")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

intents = discord.Intents.all()

# ==========================
# 🌐 Flask App
# ==========================

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot de Pagamentos Unibot está rodando com sucesso!"

@app.route("/status")
def status():
    return jsonify({"status": "online", "bot": "Unibot Pagamentos", "version": "1.0"})

# ==========================
# 🤖 Discord Bot
# ==========================

class CustomBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        try:
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✅ Conectado ao Supabase com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao conectar no Supabase: {e}")
            self.supabase = None

    async def setup_hook(self):
        os.makedirs("comprovantes", exist_ok=True)
        print("📁 Diretório 'comprovantes' verificado/criado")

        # Carrega cogs automaticamente
        cogs_carregados = 0
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ [COG] {filename[:-3]} carregado")
                    cogs_carregados += 1
                except Exception as e:
                    print(f"❌ [ERRO] Falha ao carregar {filename}: {e}")

        print(f"📊 Total de cogs carregados: {cogs_carregados}")
        asyncio.create_task(self.auto_ping())

    async def on_ready(self):
        print("="*50)
        print(f"✅ BOT ONLINE! {self.user} ({self.user.id})")
        print(f"🌐 Servidores: {len(self.guilds)}")
        print("="*50)

    async def auto_ping(self):
        await asyncio.sleep(60)
        while True:
            if AUTOPING:
                try:
                    async with aiohttp.ClientSession() as session:
                        await session.get(AUTOPING)
                        print("🔄 [AutoPing] Ping enviado")
                except Exception as e:
                    print(f"❌ [AutoPing] Erro: {e}")
            await asyncio.sleep(300)

bot = CustomBot(command_prefix="!", intents=intents)
bot.remove_command("help")

# ==========================
# ⚡ ASGI para Gunicorn
# ==========================

# Flask via Starlette WSGIMiddleware
application = WSGIMiddleware(app)

# Inicia bot no background
asyncio.get_event_loop().create_task(bot.start(TOKEN))
asyncio.get_event_loop().create_task(bot.auto_ping())
