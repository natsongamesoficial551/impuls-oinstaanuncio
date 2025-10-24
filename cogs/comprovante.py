import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime

# Carregar IDs das variáveis de ambiente
COMPROVANTES_CHANNEL_ID = int(os.getenv('COMPROVANTES_CHANNEL_ID', 0))
MOD_CHANNEL_ID = int(os.getenv('MOD_CHANNEL_ID', 0))
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', 0))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', 0))
CATEGORY_PEDIDOS_ID = int(os.getenv('CATEGORY_PEDIDOS_ID', 0))

class VerificationButtons(discord.ui.View):
    """Botões de Aceitar/Recusar para moderadores"""
    def __init__(self, bot, pedido_id: str, user_id: int, plano: str, comprovante_path: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.pedido_id = pedido_id
        self.user_id = user_id
        self.plano = plano
        self.comprovante_path = comprovante_path

    @discord.ui.button(label='✅ Aceitar', style=discord.ButtonStyle.green, custom_id='aceito')
    async def aceito_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para aprovar o pedido"""
        
        # Verificar se é moderador
        if not any(role.id == MOD_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message('❌ Apenas moderadores podem aprovar pedidos.', ephemeral=True)
            return

        await interaction.response.defer()

        try:
            supabase = self.bot.supabase
            
            # 1. Obter próximo número sequencial do contador
            result = supabase.table('contador').select('ultimo_numero').execute()
            
            if result.data:
                proximo_numero = result.data[0]['ultimo_numero'] + 1
                supabase.table('contador').update({'ultimo_numero': proximo_numero}).eq('id', 1).execute()
            else:
                # Primeira vez - criar contador
                proximo_numero = 1
                supabase.table('contador').insert({'id': 1, 'ultimo_numero': 1}).execute()

            # 2. Criar canal privado
            guild = interaction.guild
            category = discord.utils.get(guild.categories, id=CATEGORY_PEDIDOS_ID)
            
            canal_nome = f'pedido-cliente-{proximo_numero}'
            
            # Permissões do canal
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            
            # Adicionar moderadores
            mod_role = guild.get_role(MOD_ROLE_ID)
            if mod_role:
                overwrites[mod_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            # Adicionar cliente
            user = guild.get_member(self.user_id)
            if user:
                overwrites[user] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            # Criar canal
            canal_pedido = await guild.create_text_channel(
                name=canal_nome,
                category=category,
                overwrites=overwrites
            )

            # 3. Salvar no banco Supabase
            supabase.table('pedidos').insert({
                'pedido_id': self.pedido_id,
                'user_id': self.user_id,
                'pedido_number': proximo_numero,
                'plano': self.plano,
                'status': 'aceito',
                'moderador_id': interaction.user.id,
                'moderador_nome': str(interaction.user),
                'canal_id': canal_pedido.id,
                'comprovante_path': self.comprovante_path,
                'timestamp': datetime.utcnow().isoformat()
            }).execute()

            # 4. Mensagem inicial no canal do pedido
            embed_canal = discord.Embed(
                title=f'🎯 Pedido #{proximo_numero} - {self.plano}',
                description=f'Bem-vindo(a) ao seu pedido, {user.mention}!\n\n'
                           f'**Plano:** {self.plano}\n'
                           f'**ID do Pedido:** {self.pedido_id}\n'
                           f'**Status:** ✅ Aprovado\n\n'
                           f'Os moderadores irão orientá-lo sobre os próximos passos.',
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed_canal.set_footer(text=f'Aprovado por {interaction.user}')
            await canal_pedido.send(embed=embed_canal)

            # 5. DM ao cliente
            try:
                embed_dm = discord.Embed(
                    title='✅ Pedido Aprovado!',
                    description=f'Seu pedido ({self.plano}) foi aprovado!\n\n'
                               f'**Canal privado criado:** {canal_pedido.mention}\n'
                               f'**Número do Pedido:** #{proximo_numero}\n\n'
                               f'Entre no canal privado para combinar os próximos passos.',
                    color=discord.Color.green()
                )
                await user.send(embed=embed_dm)
            except:
                # Usuário com DM fechada
                pass

            # 6. Log no canal de logs
            if LOG_CHANNEL_ID:
                log_channel = guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    embed_log = discord.Embed(
                        title='✅ Pedido Aprovado',
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    embed_log.add_field(name='Pedido ID', value=self.pedido_id, inline=True)
                    embed_log.add_field(name='Número', value=f'#{proximo_numero}', inline=True)
                    embed_log.add_field(name='Cliente', value=f'{user.mention}', inline=True)
                    embed_log.add_field(name='Plano', value=self.plano, inline=True)
                    embed_log.add_field(name='Moderador', value=interaction.user.mention, inline=True)
                    embed_log.add_field(name='Canal', value=canal_pedido.mention, inline=True)
                    await log_channel.send(embed=embed_log)

            # 7. Atualizar mensagem original dos moderadores
            embed_atualizado = interaction.message.embeds[0]
            embed_atualizado.color = discord.Color.green()
            embed_atualizado.title = f'✅ APROVADO - Pedido #{proximo_numero}'
            embed_atualizado.add_field(name='Status', value=f'Aprovado por {interaction.user.mention}', inline=False)
            embed_atualizado.add_field(name='Canal', value=canal_pedido.mention, inline=False)
            
            await interaction.message.edit(embed=embed_atualizado, view=None)
            await interaction.followup.send(f'✅ Pedido aprovado! Canal {canal_pedido.mention} criado.', ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f'❌ Erro ao processar aprovação: {str(e)}', ephemeral=True)
            print(f"❌ Erro na aprovação: {e}")

    @discord.ui.button(label='❌ Recusar', style=discord.ButtonStyle.red, custom_id='negada')
    async def negada_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para recusar o pedido"""
        
        # Verificar se é moderador
        if not any(role.id == MOD_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message('❌ Apenas moderadores podem reprovar pedidos.', ephemeral=True)
            return

        # Abrir modal para pedir o motivo
        modal = MotivoModal(self.bot, self.pedido_id, self.user_id, self.plano, self.comprovante_path, interaction.message)
        await interaction.response.send_modal(modal)

class MotivoModal(discord.ui.Modal, title='Motivo da Reprovação'):
    """Modal para moderador informar motivo da reprovação"""
    
    def __init__(self, bot, pedido_id: str, user_id: int, plano: str, comprovante_path: str, original_message):
        super().__init__()
        self.bot = bot
        self.pedido_id = pedido_id
        self.user_id = user_id
        self.plano = plano
        self.comprovante_path = comprovante_path
        self.original_message = original_message

    motivo = discord.ui.TextInput(
        label='Motivo da Reprovação',
        style=discord.TextStyle.paragraph,
        placeholder='Explique o motivo da reprovação...',
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            guild = interaction.guild
            user = guild.get_member(self.user_id)
            supabase = self.bot.supabase

            # 1. Salvar no banco Supabase
            supabase.table('pedidos').insert({
                'pedido_id': self.pedido_id,
                'user_id': self.user_id,
                'pedido_number': None,
                'plano': self.plano,
                'status': 'reprovado',
                'moderador_id': interaction.user.id,
                'moderador_nome': str(interaction.user),
                'motivo_reprovacao': self.motivo.value,
                'comprovante_path': self.comprovante_path,
                'timestamp': datetime.utcnow().isoformat()
            }).execute()

            # 2. DM ao cliente
            try:
                embed_dm = discord.Embed(
                    title='❌ Pedido Não Aprovado',
                    description=f'Seu pedido ({self.plano}) não foi aprovado.\n\n'
                               f'**Motivo:** {self.motivo.value}\n\n'
                               f'Se achar que houve erro, contate os moderadores.',
                    color=discord.Color.red()
                )
                await user.send(embed=embed_dm)
            except:
                pass

            # 3. Log no canal de logs
            if LOG_CHANNEL_ID:
                log_channel = guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    embed_log = discord.Embed(
                        title='❌ Pedido Reprovado',
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow()
                    )
                    embed_log.add_field(name='Pedido ID', value=self.pedido_id, inline=True)
                    embed_log.add_field(name='Cliente', value=f'{user.mention}', inline=True)
                    embed_log.add_field(name='Plano', value=self.plano, inline=True)
                    embed_log.add_field(name='Moderador', value=interaction.user.mention, inline=True)
                    embed_log.add_field(name='Motivo', value=self.motivo.value, inline=False)
                    await log_channel.send(embed=embed_log)

            # 4. Atualizar mensagem original
            embed_atualizado = self.original_message.embeds[0]
            embed_atualizado.color = discord.Color.red()
            embed_atualizado.title = '❌ REPROVADO'
            embed_atualizado.add_field(name='Status', value=f'Reprovado por {interaction.user.mention}', inline=False)
            embed_atualizado.add_field(name='Motivo', value=self.motivo.value, inline=False)
            
            await self.original_message.edit(embed=embed_atualizado, view=None)
            await interaction.followup.send('❌ Pedido reprovado e cliente notificado.', ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f'❌ Erro ao processar reprovação: {str(e)}', ephemeral=True)
            print(f"❌ Erro na reprovação: {e}")

class ComprovanteCog(commands.Cog):
    """Cog responsável pelo sistema de comprovantes"""
    
    def __init__(self, bot):
        self.bot = bot
        self.comprovantes_dir = "comprovantes"

    @commands.Cog.listener()
    async def on_ready(self):
        """Envia mensagem fixa no canal de comprovantes quando bot inicia"""
        try:
            if COMPROVANTES_CHANNEL_ID:
                canal_comprovantes = self.bot.get_channel(COMPROVANTES_CHANNEL_ID)
                if canal_comprovantes:
                    # Limpar mensagens antigas do bot (últimas 100)
                    async for msg in canal_comprovantes.history(limit=100):
                        if msg.author == self.bot.user:
                            try:
                                await msg.delete()
                            except:
                                pass
                    
                    # Enviar mensagem fixa com instruções
                    embed = discord.Embed(
                        title='📋 Como Enviar Comprovante (OBRIGATÓRIO)',
                        description='**1) Use o comando:**\n'
                                   '```!pago <ID-do-pedido> <Plano>```\n'
                                   '   - Plano: **Starter** ou **Profissional**\n\n'
                                   '**2) Valor:** R$X,XX\n\n'
                                   '**3) PIX TXID** (se houver)\n\n'
                                   '**4) Anexe o print do comprovante**\n\n'
                                   '**Exemplo:**\n'
                                   '```!pago 1234 Starter | Valor: R$150,00 | TXID: ABCD1234```\n'
                                   '(anexe imagem)\n\n'
                                   '⏱️ Após enviar, aguarde confirmação. Sua mensagem será removida para segurança.',
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text='Em até 10 min–2h iremos verificar. Não finalize o pedido até receber confirmação.')
                    await canal_comprovantes.send(embed=embed)
                    print("✅ Mensagem fixa enviada no canal de comprovantes!")
        except Exception as e:
            print(f'❌ Erro ao enviar mensagem fixa: {e}')

    @commands.command(name='pago')
    async def pago(self, ctx, pedido_id: str = None, plano: str = None, *, mensagem: str = ''):
        """Comando para usuário enviar comprovante de pagamento"""
        
        # 1. Verificar se está no canal correto
        if COMPROVANTES_CHANNEL_ID and ctx.channel.id != COMPROVANTES_CHANNEL_ID:
            await ctx.send('❌ Use este comando apenas no canal de comprovantes.', delete_after=5)
            return

        # 2. Verificar argumentos obrigatórios
        if not pedido_id or not plano:
            await ctx.send('❌ Uso correto: `!pago <ID-pedido> <Plano>`\nPlano: **Starter** ou **Profissional**', delete_after=10)
            return

        # 3. Validar plano
        plano = plano.capitalize()
        if plano not in ['Starter', 'Profissional']:
            await ctx.send('❌ Plano inválido. Use: **Starter** ou **Profissional**', delete_after=10)
            return

        # 4. Verificar se tem anexo (imagem do comprovante)
        if not ctx.message.attachments:
            await ctx.send('❌ Você precisa anexar o comprovante (imagem).', delete_after=10)
            return

        # 5. Resposta inicial ao usuário
        msg_resposta = await ctx.send('📥 Comprovante recebido! Aguardando verificação dos moderadores. Em até 10 min–2h vamos checar. Não finalize o pedido até receber confirmação.')

        try:
            # 6. Salvar comprovante localmente
            attachment = ctx.message.attachments[0]
            extensao = attachment.filename.split('.')[-1]
            timestamp = datetime.utcnow().timestamp()
            nome_arquivo = f'{pedido_id}_{ctx.author.id}_{timestamp}.{extensao}'
            caminho_arquivo = os.path.join(self.comprovantes_dir, nome_arquivo)
            
            await attachment.save(caminho_arquivo)
            print(f"📁 Comprovante salvo: {nome_arquivo}")

            # 7. Enviar para canal de moderadores
            if MOD_CHANNEL_ID:
                mod_channel = self.bot.get_channel(MOD_CHANNEL_ID)
                if mod_channel:
                    embed = discord.Embed(
                        title='🔔 Novo Comprovante Recebido',
                        color=discord.Color.gold(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name='Pedido ID', value=pedido_id, inline=True)
                    embed.add_field(name='Usuário', value=f'{ctx.author.mention} ({ctx.author.id})', inline=True)
                    embed.add_field(name='Serviço', value=plano, inline=True)
                    
                    if mensagem:
                        embed.add_field(name='Mensagem', value=mensagem, inline=False)
                    
                    embed.set_image(url=attachment.url)
                    embed.set_footer(text=f'Enviado por {ctx.author}', icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

                    # Adicionar botões de aprovação/reprovação
                    view = VerificationButtons(self.bot, pedido_id, ctx.author.id, plano, caminho_arquivo)
                    await mod_channel.send(embed=embed, view=view)

            # 8. Apagar mensagens após 3 segundos (sigilo)
            await asyncio.sleep(3)
            try:
                await ctx.message.delete()
                await msg_resposta.delete()
                print(f"🗑️ Mensagens apagadas para sigilo (Pedido: {pedido_id})")
            except:
                pass

        except Exception as e:
            await ctx.send(f'❌ Erro ao processar comprovante: {str(e)}', delete_after=10)
            print(f"❌ Erro no comando pago: {e}")

async def setup(bot):
    await bot.add_cog(ComprovanteCog(bot))