import os
import discord
from discord.ext import commands, tasks
from flask import Flask, jsonify
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import aiohttp

# Carregar variáveis do .env
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
AUTOPING = os.getenv("AUTOPING")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Intents do bot
intents = discord.Intents.all()

# Instância Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot de Pagamentos Unibot está rodando com sucesso!"

@app.route("/status")
def status():
    return jsonify({"status": "online", "bot": "Unibot Pagamentos", "version": "1.0"})


# Bot customizado
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
        # Criar diretório de comprovantes
        os.makedirs("comprovantes", exist_ok=True)
        print("📁 Diretório 'comprovantes' verificado/criado")
        
        # Carregar cogs automaticamente
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
        
        # Iniciar auto-ping como task assíncrona
        self.loop.create_task(self.auto_ping())

    async def on_ready(self):
        print(f"✅ BOT ONLINE! Nome: {self.user} | Servidores: {len(self.guilds)}")

    async def auto_ping(self):
        await asyncio.sleep(60)  # aguarda 1 min antes do primeiro ping
        while True:
            try:
                if AUTOPING:
                    async with aiohttp.ClientSession() as session:
                        await session.get(AUTOPING)
                        print("🔄 [AutoPing] Ping enviado com sucesso.")
            except Exception as e:
                print(f"❌ [AutoPing] Erro ao enviar ping: {e}")
            await asyncio.sleep(300)  # 5 min

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        print(f"❌ Erro não tratado: {type(error).__name__}: {error}")


# Instância do bot
bot = CustomBot(command_prefix="!", intents=intents)
bot.remove_command("help")


# Função para rodar o bot + Flask juntos
async def main():
    # Iniciar bot em background
    bot_task = asyncio.create_task(bot.start(TOKEN))

    # Rodar Flask no mesmo loop
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 10000))}"]
    
    await serve(app, config)

    # Aguarda o bot terminar se o Flask parar (não deve ocorrer)
    await bot_task


if __name__ == "__main__":
    asyncio.run(main())
