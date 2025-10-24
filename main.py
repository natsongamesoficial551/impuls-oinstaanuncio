import os
import discord
from discord.ext import commands
from flask import Flask
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

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

# Tarefa de auto-ping a cada 5 minutos para manter o bot online no Render
async def auto_ping():
    import aiohttp
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
        
        # Conexão com Supabase (PostgreSQL)
        try:
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✅ Conectado ao Supabase com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao conectar no Supabase: {e}")
            self.supabase = None

    async def setup_hook(self):
        """Carrega todos os cogs automaticamente"""
        print("\n" + "="*50)
        print("🔄 Iniciando carregamento de cogs...")
        print("="*50)
        
        # Criar diretório de comprovantes se não existir
        os.makedirs("comprovantes", exist_ok=True)
        print("📁 Diretório 'comprovantes' verificado/criado")
        
        # Carregar todos os cogs da pasta cogs/
        cogs_carregados = 0
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ [COG] {filename[:-3]} carregado")
                    cogs_carregados += 1
                except Exception as e:
                    print(f"❌ [ERRO] Falha ao carregar {filename}: {e}")
        
        print(f"\n📊 Total de cogs carregados: {cogs_carregados}")
        
        # Iniciar auto-ping
        self.loop.create_task(auto_ping())
        print("✅ Sistema de auto-ping iniciado (5 em 5 minutos)")
        print("="*50 + "\n")

    async def on_ready(self):
        """Executado quando o bot está pronto e online"""
        print("\n" + "="*50)
        print(f"✅ BOT ONLINE!")
        print(f"👤 Nome: {self.user}")
        print(f"🆔 ID: {self.user.id}")
        print(f"🌐 Servidores: {len(self.guilds)}")
        
        total_usuarios = sum(guild.member_count for guild in self.guilds)
        print(f"👥 Usuários: {total_usuarios}")
        print("="*50 + "\n")

    async def on_command_error(self, ctx, error):
        """Tratamento global de erros"""
        
        # Ignorar comando não encontrado
        if isinstance(error, commands.CommandNotFound):
            return
        
        # Sem permissão
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você não tem permissão para usar este comando!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        # Argumento faltando
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Argumento Faltando",
                description=f"Você esqueceu de fornecer: `{error.param.name}`\n\nUse `!ajuda` para ver os comandos.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        # Argumento inválido
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Argumento Inválido",
                description="Verifique os argumentos do comando!\n\nUse `!ajuda` para ver os comandos.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        # Erro genérico
        else:
            print(f"❌ Erro não tratado: {type(error).__name__}: {error}")
            
            # Não mostrar erros técnicos ao usuário
            embed = discord.Embed(
                title="❌ Erro",
                description="Ocorreu um erro ao executar o comando. Tente novamente.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)

# Instância do bot
bot = CustomBot(command_prefix="!", intents=intents)

# Remover comando de ajuda padrão (vamos criar o nosso)
bot.remove_command('help')

# Iniciar Flask + Bot
if __name__ == "__main__":
    import threading
    
    print("="*50)
    print("🚀 Iniciando Unibot Pagamentos...")
    print("="*50)
    
    # Iniciar Flask em thread separada (para o Render manter o bot online)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    print("✅ Flask iniciado na porta 10000\n")
    
    # Iniciar bot
    try:
        asyncio.run(bot.start(TOKEN))
    except KeyboardInterrupt:
        print("\n👋 Bot desligado manualmente!")
    except Exception as e:
        print(f"❌ Erro crítico ao iniciar bot: {e}")