import discord
from discord.ext import commands
from datetime import datetime

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = None 

    @commands.command(name='setlogchannel')
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Define o canal de logs onde todas as ações serão registradas."""
        self.log_channel_id = channel.id
        await ctx.send(embed=discord.Embed(
            title="**__```CANAL DE LOGS DEFINIDO```__**",
            description=f"- > **O canal de logs foi definido para: {channel.mention}**",
            color=discord.Color.green()))

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Intercepta todos os comandos executados no bot e registra no canal de logs."""
        if not self.log_channel_id:
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel is None:
            return

        command_name = ctx.command.qualified_name
        character_name = ctx.kwargs.get('character_name', 'N/A') 
        user = ctx.author
        avatar_url = user.avatar.url if user.avatar else None

        embed = discord.Embed(
            title="**__```REGISTRO DE COMANDO```__**",
            description=f"- > **Comando executado:** `{command_name}`\n"
                        f"- > **Usuário:** {user.mention} (`{user}`)\n"
                        f"- > **ID do Usuário:** {user.id}\n"
                        f"- > **Data e Hora:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            color=discord.Color.blue()
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
