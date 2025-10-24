import os
import discord
from discord.ext import commands
from flask import Flask
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import threading
import aiohttp

# Carregar variáveis do .env
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
AUTOPING = os.getenv("AUTOPING")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Intents
intents = discord.Intents.all()

# Flask App para manter online no Render
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot de Pagamentos Unibot está rodando com sucesso!"

@app.route('/status')
def status():
    return {"status": "online", "bot": "Unibot Pagamentos", "version": "1.0"}

# Tarefa de auto-ping a cada 5 minutos
async def auto_ping():
    await asyncio.sleep(60)  # Aguarda 1 min antes do primeiro ping
    while True:
        try:
            if AUTOPING:
                async with aiohttp.ClientSession() as session:
                    await session.get(AUTOPING)
                    print("🔄 [AutoPing] Ping enviado com sucesso.")
        except Exception as e:
            print(f"❌ [AutoPing] Erro ao enviar ping: {e}")
        await asyncio.sleep(300)  # 5 minutos

# Bot customizado com conexão ao Supabase
class CustomBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.loop.create_task(auto_ping())
        print("✅ Sistema de auto-ping iniciado (5 em 5 minutos)")

    async def on_ready(self):
        print(f"\n✅ BOT ONLINE! Nome: {self.user} | Servidores: {len(self.guilds)}")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        print(f"❌ Erro não tratado: {type(error).__name__}: {error}")

# Instância do bot
bot = CustomBot(command_prefix="!", intents=intents)
bot.remove_command('help')

# Função para rodar o bot em uma thread separada
def start_bot():
    asyncio.run(bot.start(TOKEN))

# Iniciar Flask e bot (quando rodar localmente ou Render)
if __name__ == "__main__":
    threading.Thread(target=start_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
