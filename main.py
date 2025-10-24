import sys, types
# Patch para "enganar" import de audioop em ambientes sem audioop (ex: Python 3.13 no Render).
# IMPORTANTE: isso desativa recursos de áudio/voice — use apenas se não precisar de voz.
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
        """Carrega cogs e inicia auto-ping"""
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
        asyncio.create_task(self.auto_ping())  # usa create_task direto

    async def on_ready(self):
        print("=" * 50)
        print(f"✅ BOT ONLINE!")
        print(f"👤 Nome: {self.user}")
        print(f"🆔 ID: {self.user.id}")
        print(f"🌐 Servidores: {len(self.guilds)}")
        print("=" * 50)

    async def auto_ping(self):
        """Mantém o Render ativo"""
        await asyncio.sleep(60)
        while True:
            try:
                if AUTOPING:
                    async with aiohttp.ClientSession() as session:
                        await session.get(AUTOPING)
                        print("🔄 [AutoPing] Ping enviado com sucesso.")
            except Exception as e:
                print(f"❌ [AutoPing] Erro ao enviar ping: {e}")
            await asyncio.sleep(300)  # 5 minutos


# ==========================
# 🚀 Inicialização
# ==========================

bot = CustomBot(command_prefix="!", intents=intents)
bot.remove_command("help")


async def main():
    """Executa Flask + Bot simultaneamente"""
    bot_task = asyncio.create_task(bot.start(TOKEN))

    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 10000))}"]
    config.worker_class = "asyncio"  # garante compatibilidade com bot

    await serve(app, config)
    await bot_task  # aguarda bot terminar (se Flask cair)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Encerrando aplicação...")
