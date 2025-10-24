import discord
from discord.ext import commands
from datetime import datetime
import os

MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', 0))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', 0))

class PedidosCog(commands.Cog):
    """Cog para gerenciar pedidos (comandos extras)"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='statuspag', aliases=['status'])
    async def statuspag(self, ctx, pedido_id: str = None):
        """Verifica o status de um pedido pelo ID"""
        
        if not pedido_id:
            embed = discord.Embed(
                title="❌ Erro",
                description='**Uso correto:**\n```!statuspag <ID-pedido>```\n\n**Exemplo:**\n```!statuspag 1234```',
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        try:
            supabase = self.bot.supabase
            
            # Buscar pedido no Supabase
            result = supabase.table('pedidos').select('*').eq('pedido_id', pedido_id).execute()
            
            if not result.data:
                embed = discord.Embed(
                    title="❌ Pedido Não Encontrado",
                    description=f'Nenhum pedido encontrado com ID: `{pedido_id}`',
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            pedido = result.data[0]
            
            # Definir cor baseada no status
            cores = {
                'aceito': discord.Color.green(),
                'reprovado': discord.Color.red(),
                'fechado': discord.Color.orange()
            }
            cor = cores.get(pedido['status'], discord.Color.blue())
            
            # Criar embed com informações
            embed = discord.Embed(
                title=f'📊 Status do Pedido {pedido_id}',
                color=cor,
                timestamp=datetime.fromisoformat(pedido['timestamp'])
            )
            
            # Emoji baseado no status
            status_emoji = {
                'aceito': '✅',
                'reprovado': '❌',
                'fechado': '🔒'
            }
            emoji = status_emoji.get(pedido['status'], '❓')
            
            embed.add_field(name='Status', value=f"{emoji} **{pedido['status'].upper()}**", inline=True)
            embed.add_field(name='Plano', value=f"**{pedido['plano']}**", inline=True)
            
            # Se foi aprovado
            if pedido['pedido_number']:
                embed.add_field(name='Número', value=f"**#{pedido['pedido_number']}**", inline=True)
                
                # Se tem canal criado
                if pedido['canal_id']:
                    canal = ctx.guild.get_channel(pedido['canal_id'])
                    if canal:
                        embed.add_field(name='Canal', value=canal.mention, inline=True)
            
            # Se foi reprovado
            if pedido['status'] == 'reprovado' and pedido.get('motivo_reprovacao'):
                embed.add_field(name='Motivo da Reprovação', value=pedido['motivo_reprovacao'], inline=False)
            
            # Moderador responsável
            if pedido.get('moderador_nome'):
                embed.add_field(name='Moderador Responsável', value=pedido['moderador_nome'], inline=True)
            
            embed.set_footer(text=f"Consultado por {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description=f'Erro ao buscar status: {str(e)}',
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            print(f"❌ Erro no comando statuspag: {e}")

    @commands.command(name='fecharpedido', aliases=['fechar'])
    @commands.has_permissions(administrator=True)
    async def fecharpedido(self, ctx, pedido_id: str = None):
        """Fecha um pedido e arquiva o canal (somente moderadores)"""
        
        if not pedido_id:
            embed = discord.Embed(
                title="❌ Erro",
                description='**Uso correto:**\n```!fecharpedido <ID-pedido>```\n\n**Exemplo:**\n```!fecharpedido 1234```',
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        try:
            supabase = self.bot.supabase
            
            # Buscar pedido
            result = supabase.table('pedidos').select('*').eq('pedido_id', pedido_id).execute()
            
            if not result.data:
                embed = discord.Embed(
                    title="❌ Pedido Não Encontrado",
                    description=f'Nenhum pedido encontrado com ID: `{pedido_id}`',
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            pedido = result.data[0]
            
            # Verificar se o pedido está aceito
            if pedido['status'] != 'aceito':
                embed = discord.Embed(
                    title="❌ Erro",
                    description=f'Apenas pedidos **aceitos** podem ser fechados.\n\nStatus atual: **{pedido["status"].upper()}**',
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Atualizar status no Supabase
            supabase.table('pedidos').update({
                'status': 'fechado',
                'fechado_em': datetime.utcnow().isoformat(),
                'fechado_por': ctx.author.id
            }).eq('pedido_id', pedido_id).execute()

            # Arquivar canal
            if pedido['canal_id']:
                canal = ctx.guild.get_channel(pedido['canal_id'])
                if canal:
                    try:
                        # Renomear canal para indicar arquivamento
                        await canal.edit(name=f"arquivado-{canal.name}")
                        
                        # Enviar mensagem de encerramento no canal
                        embed_canal = discord.Embed(
                            title='🔒 Pedido Fechado',
                            description=f'Este pedido foi fechado por {ctx.author.mention}.\n\n'
                                       f'O canal ficará arquivado para registro.',
                            color=discord.Color.orange(),
                            timestamp=datetime.utcnow()
                        )
                        await canal.send(embed=embed_canal)
                        print(f"📦 Canal arquivado: {canal.name}")
                    except Exception as e:
                        print(f"❌ Erro ao arquivar canal: {e}")

            # Log no canal de logs
            if LOG_CHANNEL_ID:
                log_channel = ctx.guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    embed_log = discord.Embed(
                        title='🔒 Pedido Fechado',
                        color=discord.Color.orange(),
                        timestamp=datetime.utcnow()
                    )
                    embed_log.add_field(name='Pedido ID', value=pedido_id, inline=True)
                    embed_log.add_field(name='Número', value=f"#{pedido['pedido_number']}", inline=True)
                    embed_log.add_field(name='Plano', value=pedido['plano'], inline=True)
                    embed_log.add_field(name='Fechado por', value=ctx.author.mention, inline=True)
                    await log_channel.send(embed=embed_log)

            # Resposta de sucesso
            embed = discord.Embed(
                title='✅ Pedido Fechado',
                description=f'Pedido `{pedido_id}` fechado com sucesso!',
                color=discord.Color.green()
            )
            embed.add_field(name='Número', value=f"#{pedido['pedido_number']}", inline=True)
            embed.add_field(name='Plano', value=pedido['plano'], inline=True)
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description=f'Erro ao fechar pedido: {str(e)}',
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            print(f"❌ Erro no comando fecharpedido: {e}")

    @commands.command(name='ultimonumero')
    @commands.has_permissions(administrator=True)
    async def ultimonumero(self, ctx):
        """Mostra o último número sequencial usado (somente moderadores)"""
        
        try:
            supabase = self.bot.supabase
            result = supabase.table('contador').select('ultimo_numero').execute()
            
            embed = discord.Embed(
                title='🔢 Contador de Pedidos',
                color=discord.Color.blue()
            )
            
            if result.data:
                numero = result.data[0]['ultimo_numero']
                embed.description = f'**Último número usado:** {numero}\n**Próximo pedido será:** #{numero + 1}'
            else:
                embed.description = 'Nenhum pedido aprovado ainda.\n**Próximo pedido será:** #1'
            
            embed.set_footer(text=f"Consultado por {ctx.author}")
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description=f'Erro ao buscar número: {str(e)}',
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            print(f"❌ Erro no comando ultimonumero: {e}")

    @commands.command(name='listarpedidos', aliases=['pedidos', 'listar'])
    @commands.has_permissions(administrator=True)
    async def listarpedidos(self, ctx, status: str = None):
        """Lista pedidos por status (somente moderadores)"""
        
        try:
            supabase = self.bot.supabase
            
            # Buscar pedidos
            if status:
                status = status.lower()
                if status not in ['aceito', 'reprovado', 'fechado']:
                    embed = discord.Embed(
                        title="❌ Status Inválido",
                        description='Status válidos: **aceito**, **reprovado**, **fechado**',
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return
                
                result = supabase.table('pedidos').select('*').eq('status', status).order('timestamp', desc=True).limit(10).execute()
            else:
                result = supabase.table('pedidos').select('*').order('timestamp', desc=True).limit(10).execute()
            
            if not result.data:
                embed = discord.Embed(
                    title='📋 Lista de Pedidos',
                    description='Nenhum pedido encontrado.',
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            # Criar embed
            embed = discord.Embed(
                title=f'📋 Lista de Pedidos ({len(result.data)})',
                color=discord.Color.blue()
            )
            
            if status:
                embed.description = f'Filtro: **{status.upper()}**'
            
            # Adicionar pedidos ao embed
            for pedido in result.data[:10]:
                status_emoji = {
                    'aceito': '✅',
                    'reprovado': '❌',
                    'fechado': '🔒'
                }
                emoji = status_emoji.get(pedido['status'], '❓')
                
                numero_str = f"#{pedido['pedido_number']}" if pedido['pedido_number'] else "N/A"
                
                user = ctx.guild.get_member(pedido['user_id'])
                user_str = user.mention if user else f"ID: {pedido['user_id']}"
                
                valor = f"{emoji} **{pedido['status'].upper()}** | {numero_str}\n"
                valor += f"Cliente: {user_str}\n"
                valor += f"Plano: **{pedido['plano']}**\n"
                
                if pedido['canal_id']:
                    canal = ctx.guild.get_channel(pedido['canal_id'])
                    if canal:
                        valor += f"Canal: {canal.mention}\n"
                
                data = datetime.fromisoformat(pedido['timestamp']).strftime('%d/%m/%Y %H:%M')
                valor += f"Data: {data}"
                
                embed.add_field(
                    name=f"Pedido {pedido['pedido_id']}",
                    value=valor,
                    inline=False
                )
            
            embed.set_footer(text=f"Consultado por {ctx.author} | Mostrando últimos 10 pedidos")
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description=f'Erro ao listar pedidos: {str(e)}',
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            print(f"❌ Erro no comando listarpedidos: {e}")

async def setup(bot):
    await bot.add_cog(PedidosCog(bot))