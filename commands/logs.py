import traceback
from datetime import datetime

import discord
from discord.ext import commands

from database.connection import create_connection

conn = create_connection()
c = conn.cursor()


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channels: dict[int, int] = {}
        self._load_log_channels_from_db()

    def _load_log_channels_from_db(self):
        c.execute("SELECT guild_id, channel_id FROM log_channel_settings")
        rows = c.fetchall()
        self.log_channels = {int(guild_id): int(channel_id) for guild_id, channel_id in rows}

    def get_log_channel_id(self, guild_id: int | None) -> int | None:
        if guild_id is None:
            return None
        return self.log_channels.get(guild_id)

    async def _resolve_log_targets(self, guild_id: int | None) -> list[discord.TextChannel]:
        channel_ids: list[int] = []
        if guild_id is not None and guild_id in self.log_channels:
            channel_ids = [self.log_channels[guild_id]]
        else:
            channel_ids = list(dict.fromkeys(self.log_channels.values()))

        targets: list[discord.TextChannel] = []
        for channel_id in channel_ids:
            channel = self.bot.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                targets.append(channel)
        return targets

    @commands.command(name='setlogchannel')
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Define o canal de logs onde todas as ações e erros técnicos serão registrados."""
        if ctx.guild is None:
            await ctx.send("- > **Esse comando só pode ser usado em servidor.**")
            return

        guild_id = ctx.guild.id
        self.log_channels[guild_id] = channel.id
        c.execute(
            """
            INSERT INTO log_channel_settings (guild_id, channel_id, updated_by, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id)
            DO UPDATE SET
                channel_id=excluded.channel_id,
                updated_by=excluded.updated_by,
                updated_at=CURRENT_TIMESTAMP
            """,
            (guild_id, channel.id, ctx.author.id),
        )
        conn.commit()

        await ctx.send(embed=discord.Embed(
            title="**__```CANAL DE LOGS DEFINIDO```__**",
            description=f"- > **O canal de logs foi definido para: {channel.mention}**",
            color=discord.Color.green()))

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Intercepta comandos executados e registra no canal de logs do servidor."""
        if ctx.guild is None:
            return

        log_channel_id = self.get_log_channel_id(ctx.guild.id)
        if not log_channel_id:
            return

        log_channel = self.bot.get_channel(log_channel_id)
        if not isinstance(log_channel, discord.TextChannel):
            return

        command_name = ctx.command.qualified_name if ctx.command else 'desconhecido'
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

    async def log_technical_error(
        self,
        *,
        source: str,
        error: BaseException,
        guild_id: int | None = None,
        user_id: int | None = None,
        command_name: str | None = None,
        extra_context: str | None = None,
    ):
        targets = await self._resolve_log_targets(guild_id)
        if not targets:
            return

        trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        trace = trace[-3500:] if len(trace) > 3500 else trace

        context_lines = [
            f"- > **Fonte:** `{source}`",
            f"- > **Erro:** `{type(error).__name__}`",
            f"- > **Mensagem:** `{str(error)[:300]}`",
        ]
        if command_name:
            context_lines.append(f"- > **Comando:** `{command_name}`")
        if guild_id:
            context_lines.append(f"- > **Guild ID:** `{guild_id}`")
        if user_id:
            context_lines.append(f"- > **User ID:** `{user_id}`")
        if extra_context:
            context_lines.append(f"- > **Contexto:** {extra_context}")

        embed = discord.Embed(
            title="**__```ERRO TÉCNICO DO BOT```__**",
            description='\n'.join(context_lines),
            color=discord.Color.red(),
            timestamp=datetime.now(),
        )

        # Traceback pode exceder o limite de campos de embed; enviamos em mensagens fragmentadas.
        trace_chunks = [trace[i:i + 1800] for i in range(0, len(trace), 1800)]

        for channel in targets:
            try:
                await channel.send(embed=embed)
                for idx, chunk in enumerate(trace_chunks, start=1):
                    header = f"Traceback ({idx}/{len(trace_chunks)}):"
                    await channel.send(f"{header}\n```py\n{chunk}\n```")
            except discord.DiscordException:
                continue


async def setup(bot):
    await bot.add_cog(Logs(bot))
