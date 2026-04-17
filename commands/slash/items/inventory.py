import discord
from discord import app_commands

from database.connection import create_connection
from utils.common import apply_layout as shared_apply_layout, to_bold_sans_serif

conn = create_connection()
c = conn.cursor()


def get_inventory_capacity(rank):
    rank_capacities = {
        'F-': 4, 'F': 8, 'F+': 12, 'E-': 16, 'E': 20, 'E+': 24,
        'D-': 28, 'D': 32, 'D+': 36, 'C-': 40, 'C': 44, 'C+': 48,
        'B-': 52, 'B': 56, 'B+': 60, 'A-': 64, 'A': 68, 'A+': 72,
        'S': 76, 'S+': 80, 'SS': 84, 'SS+': 88, 'SSS': 92, 'SSS+': 96,
        'Z': 100,
    }
    return rank_capacities.get(rank, 4)


def register_inventory_slash_commands(bot):
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
        cap = get_inventory_capacity(rank)
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
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        c.execute(
            """
            SELECT p.rank
            FROM characters c
            JOIN character_progression p ON c.character_id = p.character_id
            WHERE c.name COLLATE NOCASE=? AND c.user_id=?
            """,
            (character_name, interaction.user.id),
        )
        character_rank = c.fetchone()
        if not character_rank:
            embed = discord.Embed(
                title="**__```𝐄𝐑𝐑𝐎```__**",
                description=f"- > **Personagem {character_name} não encontrado.**",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        rank = character_rank[0]
        capacity = get_inventory_capacity(rank)
        item_list = "\n".join([f"- {item[0]}: {item[1]}" for item in items])
        formatted_character_name = to_bold_sans_serif(character_name)

        embed = discord.Embed(
            title=f"𝐈𝐧𝐯𝐞𝐧𝐭𝐚́𝐫𝐢𝐨 𝐝𝐞 {formatted_character_name}",
            description=f"{item_list}\n\n𝐂𝐚𝐩𝐚𝐜𝐢𝐝𝐚𝐝𝐞: {len(items)}/{capacity} itens",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name='showitem', description='Mostra detalhes de um item do inventário')
    @app_commands.describe(character_name='Nome do personagem', item_name='Nome do item')
    async def showitem_slash(interaction: discord.Interaction, character_name: str, item_name: str):
        c.execute(
            "SELECT item_name, description, image_url FROM inventory WHERE character_name COLLATE NOCASE=? AND item_name COLLATE NOCASE=? AND user_id=?",
            (character_name, item_name, interaction.user.id),
        )
        item = c.fetchone()
        if not item:
            embed = discord.Embed(
                title="**__```𝐄𝐑𝐑𝐎```__**",
                description=f"- > **Item {item_name} não encontrado no inventário de {character_name}.**",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        found_name, description, image_url = item
        formatted_title, formatted_description = shared_apply_layout(
            interaction.user.id,
            found_name,
            description,
            default_title="╚╡ ⬥ {title} ⬥ ╞",
            default_description="╚───► *「{description}」*",
        )
        embed = discord.Embed(title=formatted_title, description=formatted_description, color=discord.Color.blue())
        if image_url:
            embed.set_image(url=image_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    register_inventory_slash_commands(bot)
