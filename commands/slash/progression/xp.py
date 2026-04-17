import discord
from discord import app_commands

from database.connection import create_connection
from commands.xp import MAX_LEVEL, POINTS_PER_LEVEL, xp_for_next_level

conn = create_connection()
c = conn.cursor()


def register_xp_slash_commands(bot):
    @bot.tree.command(name='xp', description='Admin: adiciona XP a um personagem')
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(character_name='Nome do personagem', xp_amount='Quantidade de XP')
    async def xp_slash(interaction: discord.Interaction, character_name: str, xp_amount: int):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("- > **Sem permissão de administrador.**", ephemeral=True)
            return

        c.execute("SELECT character_id FROM characters WHERE name=?", (character_name,))
        character = c.fetchone()
        if not character:
            await interaction.response.send_message(f"Personagem {character_name} não encontrado.", ephemeral=True)
            return

        character_id = character[0]
        c.execute(
            """
            SELECT experience, level, points_available, limit_break, xp_multiplier
            FROM character_progression
            WHERE character_id=?
            """,
            (character_id,),
        )
        progression = c.fetchone()
        if not progression:
            await interaction.response.send_message(f"Progressão de {character_name} não encontrada.", ephemeral=True)
            return

        experience, level, points, limit_break, xp_multiplier = progression
        gained_xp = int(xp_amount * (xp_multiplier or 1.0))
        new_experience = experience + gained_xp

        while level < MAX_LEVEL and new_experience >= xp_for_next_level(level):
            new_experience -= xp_for_next_level(level)
            level += 1
            points += POINTS_PER_LEVEL
            if level >= limit_break:
                new_experience = 0
                break

        c.execute(
            "UPDATE character_progression SET experience=?, level=?, points_available=?, updated_at=CURRENT_TIMESTAMP WHERE character_id=?",
            (new_experience, level, points, character_id),
        )
        conn.commit()
        await interaction.response.send_message(
            f"XP aplicado em **{character_name}**. Nível atual: **{level}**, XP atual: **{round(new_experience)}**, pontos: **{points}**.",
            ephemeral=True,
        )


async def setup(bot):
    register_xp_slash_commands(bot)
