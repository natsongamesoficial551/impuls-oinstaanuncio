import sys, types
# Patch para "enganar" import de audioop (desativa voice/audio)
sys.modules['audioop'] = types.ModuleType('audioop')

import os
import discord
from discord.ext import commands
from flask import Flask, jsonify
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import aiohttp
from hypercorn.asyncio import serve
from hypercorn.config import Config

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
# 🤖 Bot Customizado
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
        print("=" * 50)
        print(f"✅ BOT ONLINE!")
        print(f"👤 Nome: {self.user}")
        print(f"🆔 ID: {self.user.id}")
        print(f"🌐 Servidores: {len(self.guilds)}")
        print("=" * 50)

    async def auto_ping(self):
        await asyncio.sleep(60)
        while True:
            try:
                if AUTOPING:
                    async with aiohttp.ClientSession() as session:
                        await session.get(AUTOPING)
                        print("🔄 [AutoPing] Ping enviado com sucesso.")
            except Exception as e:
                print(f"❌ [AutoPing] Erro ao enviar ping: {e}")
            await asyncio.sleep(300)

# ==========================
# 🚀 Inicialização
# ==========================

bot = CustomBot(command_prefix="!", intents=intents)
bot.remove_command("help")

async def run_bot():
    await bot.start(TOKEN)

async def run_flask():
    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 10000))}"]
    config.worker_class = "asyncio"
    await serve(app, config)

async def main():
    # roda Flask + Discord bot simultaneamente
    await asyncio.gather(run_bot(), run_flask())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Encerrando aplicação...")
