import discord
from discord import app_commands

from commands.help_menu import HELP_TOPIC_CHOICES, _send_assist_slash, build_menu_embed_and_view


def register_help_menu_slash_commands(bot):
    @bot.tree.command(name='help', description='Mostra a ajuda geral ou por tema')
    @app_commands.choices(tema=HELP_TOPIC_CHOICES)
    @app_commands.describe(tema='personagens, habilidades, xp, inventario, classes, caracteristicas, tecnicas, soul ou layout')
    async def help_slash(interaction: discord.Interaction, tema: str | None = None):
        await _send_assist_slash(interaction, tema=tema)

    @bot.tree.command(name='menu', description='Mostra o menu rápido de atalhos do RP')
    async def menu_slash(interaction: discord.Interaction):
        embed, view = build_menu_embed_and_view()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    register_help_menu_slash_commands(bot)
