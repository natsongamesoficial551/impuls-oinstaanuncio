import discord
from discord.ext import commands
import os

MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', 0))

class UtilsCog(commands.Cog):
    """Cog com comandos utilitários"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ajuda', aliases=['help', 'comandos'])
    async def ajuda(self, ctx):
        """Mostra todos os comandos disponíveis do bot"""
        
        # Verificar se é moderador
        is_mod = any(role.id == MOD_ROLE_ID for role in ctx.author.roles)
        
        embed = discord.Embed(
            title='📖 Central de Ajuda - Unibot Pagamentos',
            description='Lista completa de comandos disponíveis',
            color=discord.Color.blue()
        )
        
        # Comandos para TODOS os usuários
        embed.add_field(
            name='👥 Comandos para Clientes',
            value='`!pago <ID-pedido> <Plano>` - Enviar comprovante de pagamento\n'
                  '`!statuspag <ID-pedido>` - Verificar status do seu pedido\n'
                  '`!ajuda` - Mostrar esta mensagem de ajuda',
            inline=False
        )
        
        # Comandos apenas para MODERADORES
        if is_mod:
            embed.add_field(
                name='🛡️ Comandos para Moderadores',
                value='`!fecharpedido <ID-pedido>` - Fechar e arquivar um pedido\n'
                      '`!ultimonumero` - Ver último número sequencial usado\n'
                      '`!listarpedidos [status]` - Listar pedidos (aceito/reprovado/fechado)\n'
                      '**Obs:** Aprovação/reprovação é feita via botões no canal de moderação',
                inline=False
            )
        
        # Instruções detalhadas
        embed.add_field(
            name='📝 Como Enviar Comprovante',
            value='**1.** Use o comando no canal de comprovantes:\n'
                  '```!pago <ID-do-pedido> <Plano>```\n'
                  '**2.** Informe os dados na mensagem:\n'
                  '   • Valor: R$X,XX\n'
                  '   • PIX TXID (opcional)\n'
                  '**3.** Anexe o print do comprovante\n\n'
                  '**Planos disponíveis:** `Starter` ou `Profissional`',
            inline=False
        )
        
        # Exemplo prático
        embed.add_field(
            name='💡 Exemplo de Uso',
            value='```!pago 1234 Starter | Valor: R$150,00 | TXID: ABCD1234```\n'
                  '(anexe a imagem do comprovante)',
            inline=False
        )
        
        # Informações importantes
        embed.add_field(
            name='⚠️ Importante',
            value='• Após enviar, suas mensagens serão **removidas automaticamente** para segurança\n'
                  '• Aguarde de **10 minutos a 2 horas** para verificação\n'
                  '• Você receberá uma **DM** com a resposta da análise\n'
                  '• **Não finalize** o pedido até receber confirmação!',
            inline=False
        )
        
        embed.set_footer(
            text=f'Solicitado por {ctx.author}',
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilsCog(bot))