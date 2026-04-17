import asyncio
import os
import traceback
from typing import Any, cast

import discord
from discord import app_commands
from discord.ext import commands

from database.connection import create_connection
from database.schema import create_tables as bootstrap_schema
from database.schema import migrate_abilities_schema as migrate_abilities_schema_impl
from database.migrations import ensure_column as ensure_column_impl
from database.migrations import ensure_soul_runtime_schema as ensure_soul_runtime_schema_impl

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix=['kill!', 'Kill!'], intents=intents, help_command=None)

conn = create_connection()
c = conn.cursor()

SCHEMA_VERSION = 2

def create_tables():
    bootstrap_schema(conn, c, schema_version=SCHEMA_VERSION)


def ensure_column(table_name: str, column_name: str, ddl: str):
    ensure_column_impl(c, table_name, column_name, ddl)


def ensure_soul_runtime_schema():
    ensure_soul_runtime_schema_impl(conn, c, schema_version=SCHEMA_VERSION)


def migrate_abilities_schema():
    migrate_abilities_schema_impl(c)

create_tables()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


def _is_user_input_error(error: BaseException) -> bool:
    return isinstance(
        error,
        (
            commands.UserInputError,
            commands.CheckFailure,
            commands.CommandNotFound,
            commands.CommandOnCooldown,
            app_commands.CheckFailure,
            app_commands.CommandOnCooldown,
        ),
    )


async def _log_technical_error(
    *,
    source: str,
    error: BaseException,
    guild_id: int | None = None,
    user_id: int | None = None,
    command_name: str | None = None,
    extra_context: str | None = None,
):
    logs_cog = bot.get_cog('Logs')
    if logs_cog is None:
        return

    log_handler = cast(Any, getattr(logs_cog, 'log_technical_error', None))
    if log_handler is None:
        return

    try:
        await log_handler(
            source=source,
            error=error,
            guild_id=guild_id,
            user_id=user_id,
            command_name=command_name,
            extra_context=extra_context,
        )
    except Exception:
        print('Falha ao enviar erro tecnico para o canal de logs:')
        print(traceback.format_exc())


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    original_error = getattr(error, 'original', error)
    if _is_user_input_error(original_error):
        return

    guild_id = ctx.guild.id if ctx.guild else None
    command_name = ctx.command.qualified_name if ctx.command else None
    await _log_technical_error(
        source='prefix_command',
        error=original_error,
        guild_id=guild_id,
        user_id=ctx.author.id if ctx.author else None,
        command_name=command_name,
    )


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    original_error = getattr(error, 'original', error)
    if _is_user_input_error(original_error):
        return

    guild_id = interaction.guild.id if interaction.guild else None
    command_name = interaction.command.qualified_name if interaction.command else None
    await _log_technical_error(
        source='slash_command',
        error=original_error,
        guild_id=guild_id,
        user_id=interaction.user.id if interaction.user else None,
        command_name=command_name,
    )


@bot.event
async def on_error(event_method: str, *args, **kwargs):
    error = kwargs.get('error')
    if not isinstance(error, BaseException):
        error = Exception(traceback.format_exc())

    guild_id = None
    user_id = None
    if args:
        first = args[0]
        if isinstance(first, commands.Context):
            guild_id = first.guild.id if first.guild else None
            user_id = first.author.id if first.author else None
        elif isinstance(first, discord.Interaction):
            guild_id = first.guild.id if first.guild else None
            user_id = first.user.id if first.user else None

    await _log_technical_error(
        source=f'event:{event_method}',
        error=error,
        guild_id=guild_id,
        user_id=user_id,
    )


def _loop_exception_handler(loop: asyncio.AbstractEventLoop, context: dict):
    error = context.get('exception')
    if not isinstance(error, BaseException):
        message = context.get('message', 'Erro desconhecido no loop asyncio')
        error = RuntimeError(str(message))

    loop.create_task(
        _log_technical_error(
            source='asyncio_loop',
            error=error,
            extra_context=context.get('message'),
        )
    )


async def sync_slash_commands():
    """Sincroniza comandos slash GLOBALMENTE para todos os servidores."""
    # Limpa qualquer comando duplicado na árvore antes de sincronizar
    all_commands = await bot.tree.fetch_commands()
    print(f"Comandos atuais antes de sincronizar: {len(all_commands)}")
    for cmd in all_commands:
        print(f"  - {cmd.name}")
    
    synced_global = await bot.tree.sync()
    print(f"\n✅ Slash global sincronizados: {len(synced_global)}")
    for cmd in synced_global:
        print(f"  - {cmd.name}")


async def clear_all_commands():
    """NUCLEAR OPTION: Deleta TODOS os comandos slash globais. Use com cuidado!"""
    try:
        all_commands = await bot.tree.fetch_commands()
        print(f"🗑️ Deletando {len(all_commands)} comandos globais...")

        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print(f"✅ Todos os comandos foram deletados e sincronizados (árvore vazia)")
        return True
    except Exception as e:
        print(f"❌ Erro ao deletar comandos: {e}")
        return False

async def setup_hook():
    """Carrega extensões e sincroniza comandos slash globalmente."""
    asyncio.get_running_loop().set_exception_handler(_loop_exception_handler)

    await bot.load_extension('commands.logs')
    await bot.load_extension('commands.register')
    await bot.load_extension('commands.slash.character.register')
    await bot.load_extension('commands.characteristics')
    await bot.load_extension('commands.slash.character.characteristics')
    await bot.load_extension('commands.discovery')
    await bot.load_extension('commands.slash.character.discovery')
    await bot.load_extension('commands.layout')
    await bot.load_extension('commands.slash.customization.layout')
    await bot.load_extension('commands.help_menu')
    await bot.load_extension('commands.slash.ui.help_menu')
    await bot.load_extension('commands.inventory')
    await bot.load_extension('commands.slash.items.inventory')
    await bot.load_extension('commands.xp')
    await bot.load_extension('commands.slash.progression.xp')
    await bot.load_extension('commands.classes')
    await bot.load_extension('commands.tecnicas')
    await bot.load_extension('commands.admin')
    await bot.load_extension('commands.category')
    await bot.load_extension('commands.image_skill')
    await bot.load_extension('commands.soul_commands')
    await bot.load_extension('commands.soul_details')

    await sync_slash_commands()

bot.setup_hook = setup_hook

def load_bot_token():
    token = os.getenv('DISCORD_TOKEN')
    if token:
        return token

    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                if key.strip() == 'DISCORD_TOKEN':
                    return value.strip().strip('"').strip("'")

    raise RuntimeError('Token nao encontrado. Defina DISCORD_TOKEN no ambiente ou no arquivo .env')


bot.run(load_bot_token())

conn.close()