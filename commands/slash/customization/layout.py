import discord
from discord import app_commands

from database.connection import create_connection

conn = create_connection()
c = conn.cursor()


def register_layout_slash_commands(bot):
    @bot.tree.command(name='settitle', description='Define seu layout de titulo personalizado')
    @app_commands.describe(layout='Template com {title}')
    async def set_title_layout_slash(interaction: discord.Interaction, layout: str):
        user_id = interaction.user.id
        c.execute(
            """
            INSERT INTO layout_settings (user_id, title_layout)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET title_layout=excluded.title_layout
            """,
            (user_id, layout),
        )
        conn.commit()
        embed = discord.Embed(
            title="**__```𝐋𝐀𝐘𝐎𝐔𝐓 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐎```__**",
            description=f"- > **Layout de título atualizado para:**\n```{layout}```",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name='setdesc', description='Define seu layout de descricao personalizado')
    @app_commands.describe(layout='Template com {description}')
    async def set_description_layout_slash(interaction: discord.Interaction, layout: str):
        user_id = interaction.user.id
        c.execute(
            """
            INSERT INTO layout_settings (user_id, description_layout)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET description_layout=excluded.description_layout
            """,
            (user_id, layout),
        )
        conn.commit()
        embed = discord.Embed(
            title="**__```𝐋𝐀𝐘𝐎𝐔𝐓 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐎```__**",
            description=f"- > **Layout de descrição atualizado para:**\n```{layout}```",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    register_layout_slash_commands(bot)
