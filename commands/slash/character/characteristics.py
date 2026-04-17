import discord
from discord import app_commands

from commands.characteristics import _find_character_id_by_name, _find_characteristic_definition_by_name, c, conn


def register_characteristics_slash_commands(bot):
    @bot.tree.command(name='charadd', description='Adiciona uma característica a um personagem (admin)')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(nome_personagem='Nome exato do personagem', caracteristica='Nome exato da característica')
    async def char_add_slash(interaction: discord.Interaction, nome_personagem: str, caracteristica: str):
        character = _find_character_id_by_name(nome_personagem)
        if not character:
            await interaction.response.send_message("- > **Personagem não encontrado.**", ephemeral=True)
            return

        definition = _find_characteristic_definition_by_name(caracteristica)
        if not definition:
            await interaction.response.send_message("- > **Característica não encontrada em characteristic_definitions.**", ephemeral=True)
            return

        character_id, canonical_name = character
        characteristic_id, canonical_trait_name, _, _ = definition
        c.execute(
            "INSERT OR IGNORE INTO character_characteristics (character_id, characteristic_id) VALUES (?, ?)",
            (character_id, characteristic_id),
        )
        conn.commit()

        if c.rowcount == 0:
            await interaction.response.send_message(f"- > **{canonical_name} já possui {canonical_trait_name}.**", ephemeral=True)
            return

        await interaction.response.send_message(
            f"- > **{canonical_trait_name} foi aplicada em {canonical_name}.**",
            ephemeral=True,
        )

    @bot.tree.command(name='charremove', description='Remove uma característica de um personagem (admin)')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(nome_personagem='Nome exato do personagem', caracteristica='Nome exato da característica')
    async def char_remove_slash(interaction: discord.Interaction, nome_personagem: str, caracteristica: str):
        character = _find_character_id_by_name(nome_personagem)
        if not character:
            await interaction.response.send_message("- > **Personagem não encontrado.**", ephemeral=True)
            return

        definition = _find_characteristic_definition_by_name(caracteristica)
        if not definition:
            await interaction.response.send_message("- > **Característica não encontrada em characteristic_definitions.**", ephemeral=True)
            return

        character_id, canonical_name = character
        characteristic_id, canonical_trait_name, _, _ = definition
        c.execute(
            "DELETE FROM character_characteristics WHERE character_id = ? AND characteristic_id = ?",
            (character_id, characteristic_id),
        )
        conn.commit()

        if c.rowcount == 0:
            await interaction.response.send_message(f"- > **{canonical_name} não possui {canonical_trait_name}.**", ephemeral=True)
            return

        await interaction.response.send_message(
            f"- > **{canonical_trait_name} foi removida de {canonical_name}.**",
            ephemeral=True,
        )

    @bot.tree.command(name='charlist', description='Mostra as características aplicadas a um personagem')
    @app_commands.describe(nome_personagem='Nome exato do personagem')
    async def char_list_slash(interaction: discord.Interaction, nome_personagem: str):
        character = _find_character_id_by_name(nome_personagem)
        if not character:
            await interaction.response.send_message("- > **Personagem não encontrado.**", ephemeral=True)
            return

        character_id, canonical_name = character
        c.execute(
            """
            SELECT d.name, d.type, d.rarity
            FROM character_characteristics cc
            JOIN characteristic_definitions d ON d.id = cc.characteristic_id
            WHERE cc.character_id = ?
            ORDER BY d.name COLLATE NOCASE
            """,
            (character_id,),
        )
        rows = c.fetchall()

        if not rows:
            await interaction.response.send_message(f"- > **{canonical_name} não possui características aplicadas.**", ephemeral=True)
            return

        lines = [f"- **{name}** ({ctype} | {rarity})" for name, ctype, rarity in rows]
        await interaction.response.send_message(
            f"- > **Personagem:** {canonical_name}\n\n" + "\n".join(lines),
            ephemeral=True,
        )


async def setup(bot):
    register_characteristics_slash_commands(bot)
