import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
import sqlite3
import aiohttp
import math
import os
import asyncio
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

def apply_layout(user_id, title, description):
    """Aplica o layout personalizado do usuário ao título e descrição"""
    c.execute("SELECT title_layout, description_layout FROM layout_settings WHERE user_id=?", (user_id,))
    layout = c.fetchone()

    if layout:
        title_layout, description_layout = layout
    else:
        title_layout = "╚╡ ⬥ {title} ⬥ ╞"
        description_layout = "╚───► *「{description}」*"

    formatted_title = title_layout.replace("{title}", title)
    formatted_description = description_layout.replace("{description}", description)

    return formatted_title, formatted_description

def to_bold_sans_serif(text):
    """Converte texto para bold sans-serif Unicode"""
    bold_sans_serif = {
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆',
        'H': '𝐇', 'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍',
        'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓', 'U': '𝐔',
        'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠',
        'h': '𝐡', 'i': '𝐢', 'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧',
        'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫', 's': '𝐬', 't': '𝐭', 'u': '𝐮',
        'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳'
    }
    return ''.join(bold_sans_serif[ch] if ch in bold_sans_serif else ch for ch in text.upper())

async def send_embed(ctx, title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


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


@bot.tree.command(name='pendencias', description='Mostra pendências do personagem')
@app_commands.describe(name='Nome do personagem (opcional)')
async def pendencias_slash(interaction: discord.Interaction, name: str | None = None):
    if not name:
        c.execute(
            """
            SELECT c.character_id, c.name, p.points_available, p.level, p.limit_break, p.rank
            FROM characters c
            LEFT JOIN character_progression p ON c.character_id = p.character_id
            WHERE c.user_id=?
            ORDER BY c.character_id DESC
            LIMIT 1
            """,
            (interaction.user.id,),
        )
    else:
        c.execute(
            """
            SELECT c.character_id, c.name, p.points_available, p.level, p.limit_break, p.rank
            FROM characters c
            LEFT JOIN character_progression p ON c.character_id = p.character_id
            WHERE c.name COLLATE NOCASE=? AND c.user_id=?
            """,
            (name, interaction.user.id),
        )

    character = c.fetchone()
    if not character:
        embed = discord.Embed(
            title="**__```𝐄𝐑𝐑𝐎```__**",
            description="- > **Personagem não encontrado.**",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    character_id, char_name, points, level, limit_break, rank = character
    pendencias_lista = []

    if points > 0:
        pendencias_lista.append(f"- Você tem **{points}** pontos para distribuir. (`kill!points {char_name} forca 1`)")

    c.execute("SELECT COUNT(*) FROM techniques WHERE character_id=? AND category_id IS NULL", (character_id,))
    sem_habilidade = c.fetchone()[0]
    if sem_habilidade > 0:
        pendencias_lista.append(f"- Você tem **{sem_habilidade}** técnica(s) sem habilidade. (`kill!assignability '{char_name}' 'Tecnica' 'Habilidade'`)")

    c.execute("SELECT COUNT(*) FROM inventory WHERE character_name COLLATE NOCASE=? AND user_id=?", (char_name, interaction.user.id))
    itens = c.fetchone()[0]
    rank_capacities = {
        'F-': 4, 'F': 8, 'F+': 12, 'E-': 16, 'E': 20, 'E+': 24,
        'D-': 28, 'D': 32, 'D+': 36, 'C-': 40, 'C': 44, 'C+': 48,
        'B-': 52, 'B': 56, 'B+': 60, 'A-': 64, 'A': 68, 'A+': 72,
        'S': 76, 'S+': 80, 'SS': 84, 'SS+': 88, 'SSS': 92, 'SSS+': 96, 'Z': 100,
    }
    cap = rank_capacities.get(rank, 4)
    if cap - itens <= 2:
        pendencias_lista.append(f"- Inventário quase cheio: **{itens}/{cap}**.")

    if level >= limit_break:
        pendencias_lista.append(f"- Você atingiu o limitador de nível (**{limit_break}**). Use `kill!evolve {char_name}`.")

    if not pendencias_lista:
        embed = discord.Embed(
            title="**__```𝐀𝐑𝐄𝐍𝐀𝐃𝐎```__**",
            description=f"- > **{char_name} está em dia.**",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(
        title=f"**__```𝐏𝐄𝐍𝐃𝐄̂𝐍𝐂𝐈𝐀𝐒 𝐃𝐄 {char_name.upper()}```__**",
        description="\n".join(pendencias_lista),
        color=discord.Color.orange(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='inv', description='Mostra o inventário do personagem')
@app_commands.describe(character_name='Nome do personagem')
async def inv_slash(interaction: discord.Interaction, character_name: str):
    c.execute("SELECT item_name, description FROM inventory WHERE character_name COLLATE NOCASE=? AND user_id=?", (character_name, interaction.user.id))
    items = c.fetchall()
    if not items:
        embed = discord.Embed(
            title="**__```𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎 𝐕𝐀𝐙𝐈𝐎```__**",
            description=f"- > **O inventário de {character_name} está vazio.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    c.execute("""
        SELECT p.rank
        FROM characters c
        JOIN character_progression p ON c.character_id = p.character_id
        WHERE c.name COLLATE NOCASE=? AND c.user_id=?
    """, (character_name, interaction.user.id))
    character_rank = c.fetchone()
    if not character_rank:
        embed = discord.Embed(
            title="**__```𝐄𝐑𝐑𝐎```__**",
            description=f"- > **Personagem {character_name} não encontrado.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    rank = character_rank[0]
    rank_capacities = {
        'F-': 4, 'F': 8, 'F+': 12, 'E-': 16, 'E': 20, 'E+': 24,
        'D-': 28, 'D': 32, 'D+': 36, 'C-': 40, 'C': 44, 'C+': 48,
        'B-': 52, 'B': 56, 'B+': 60, 'A-': 64, 'A': 68, 'A+': 72,
        'S': 76, 'S+': 80, 'SS': 84, 'SS+': 88, 'SSS': 92, 'SSS+': 96, 'Z': 100
    }
    capacity = rank_capacities.get(rank, 4)
    
    item_list = "\n".join([f"- {item[0]}: {item[1]}" for item in items])
    formatted_character_name = to_bold_sans_serif(character_name)
    
    embed = discord.Embed(
        title=f"𝐈𝐧𝐯𝐞𝐧𝐭𝐚́𝐫𝐢𝐨 𝐝𝐞 {formatted_character_name}",
        description=f"{item_list}\n\n𝐂𝐚𝐩𝐚𝐜𝐢𝐝𝐚𝐝𝐞: {len(items)}/{capacity} itens",
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='showitem', description='Mostra detalhes de um item do inventário')
@app_commands.describe(character_name='Nome do personagem', item_name='Nome do item')
async def showitem_slash(interaction: discord.Interaction, character_name: str, item_name: str):
    c.execute(
        "SELECT item_name, description, image_url FROM inventory WHERE character_name COLLATE NOCASE=? AND item_name COLLATE NOCASE=? AND user_id=?",
        (character_name, item_name, interaction.user.id)
    )
    item = c.fetchone()
    if not item:
        embed = discord.Embed(
            title="**__```𝐄𝐑𝐑𝐎```__**",
            description=f"- > **Item {item_name} não encontrado no inventário de {character_name}.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    found_name, description, image_url = item
    formatted_title, formatted_description = apply_layout(interaction.user.id, found_name, description)
    embed = discord.Embed(title=formatted_title, description=formatted_description, color=discord.Color.blue())
    if image_url:
        embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='xp', description='Admin: adiciona XP a um personagem')
@app_commands.default_permissions(administrator=True)
@app_commands.describe(character_name='Nome do personagem', xp_amount='Quantidade de XP')
async def xp_slash(interaction: discord.Interaction, character_name: str, xp_amount: int):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sem permissão de administrador.", ephemeral=True)
        return

    c.execute("SELECT character_id FROM characters WHERE name=?", (character_name,))
    character = c.fetchone()
    if not character:
        await interaction.response.send_message(f"Personagem {character_name} não encontrado.", ephemeral=True)
        return

    character_id = character[0]

    c.execute("""
        SELECT experience, level, points_available, limit_break, xp_multiplier
        FROM character_progression
        WHERE character_id=?
    """, (character_id,))
    character = c.fetchone()
    if not character:
        await interaction.response.send_message(f"Progressão de {character_name} não encontrada.", ephemeral=True)
        return

    experience, level, points, limit_break, xp_multiplier = character
    gained_xp = int(xp_amount * (xp_multiplier or 1.0))
    new_experience = experience + gained_xp

    def xp_for_next_level(local_level: int):
        return int(100 * local_level * math.log(local_level + 1))

    while level < 1000 and new_experience >= xp_for_next_level(level):
        new_experience -= xp_for_next_level(level)
        level += 1
        points += 3
        if level >= limit_break:
            new_experience = 0
            break

    c.execute(
        "UPDATE character_progression SET experience=?, level=?, points_available=?, updated_at=CURRENT_TIMESTAMP WHERE character_id=?",
        (new_experience, level, points, character_id)
    )
    conn.commit()
    await interaction.response.send_message(
        f"XP aplicado em **{character_name}**. Nível atual: **{level}**, XP atual: **{round(new_experience)}**, pontos: **{points}**.",
        ephemeral=True,
    )


@bot.command(name='syncslash')
@commands.has_permissions(administrator=True)
async def syncslash(ctx):
    """Força sincronização manual de comandos slash globalmente."""
    await sync_slash_commands()
    await ctx.send('- > **Slash commands sincronizados globalmente para todos os servidores.**')

async def setup_hook():
    """Carrega extensões e sincroniza comandos slash globalmente."""
    await bot.load_extension('commands.register')
    await bot.load_extension('commands.characteristics')
    await bot.load_extension('commands.discovery')
    await bot.load_extension('commands.layout')
    await bot.load_extension('commands.help_menu')
    await bot.load_extension('commands.inventory')
    await bot.load_extension('commands.xp')
    await bot.load_extension('commands.classes')
    await bot.load_extension('commands.tecnicas')
    await bot.load_extension('commands.logs')
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