import asyncio
import shlex

import discord
from discord.ext import commands

from database.connection import create_connection
from utils.common import send_embed

conn = create_connection()
c = conn.cursor()


def _parse_two_quoted_tokens(raw: str) -> tuple[str, str] | tuple[None, None]:
    try:
        parts = shlex.split(raw)
    except ValueError:
        return None, None

    if len(parts) != 2:
        return None, None
    return parts[0], parts[1]


def _find_character_id_by_name(character_name: str):
    c.execute(
        "SELECT character_id, name FROM characters WHERE name COLLATE NOCASE = ?",
        (character_name,),
    )
    return c.fetchone()


def _find_characteristic_definition_by_name(characteristic_name: str):
    c.execute(
        "SELECT id, name, type, rarity FROM characteristic_definitions WHERE name COLLATE NOCASE = ?",
        (characteristic_name,),
    )
    return c.fetchone()


def register_characteristics_commands(bot):
    @bot.command(name='charlistdefs', aliases=['characteristicsdefs', 'listchardefs'])
    async def char_list_definitions(ctx):
        c.execute(
            """
            SELECT name, type, rarity, COALESCE(description, '')
            FROM characteristic_definitions
            ORDER BY name COLLATE NOCASE
            """
        )
        rows = c.fetchall()

        if not rows:
            await send_embed(ctx, "**__```𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀𝐒```__**", "- > **Nenhuma característica cadastrada no sistema.**", discord.Color.red())
            return

        lines = [f"- **{name}** ({ctype} | {rarity})\n  - {desc or 'Sem descrição.'}" for name, ctype, rarity, desc in rows]
        await send_embed(
            ctx,
            "**__```𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀𝐒 𝐃𝐄𝐅𝐈𝐍𝐈𝐃𝐀𝐒```__**",
            "\n".join(lines),
            discord.Color.blue(),
        )

    @bot.command(name='charlist', aliases=['characteristics'])
    async def char_list(ctx, *, character_name: str):
        character = _find_character_id_by_name(character_name)
        if not character:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado.**", discord.Color.red())
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
            await send_embed(
                ctx,
                "**__```𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀𝐒```__**",
                f"- > **{canonical_name} não possui características aplicadas.**",
                discord.Color.orange(),
            )
            return

        lines = [f"- **{name}** ({ctype} | {rarity})" for name, ctype, rarity in rows]
        await send_embed(
            ctx,
            "**__```𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀𝐒 𝐀𝐓𝐈𝐕𝐀𝐒```__**",
            f"- > **Personagem:** {canonical_name}\n\n" + "\n".join(lines),
            discord.Color.blue(),
        )

    @bot.command(name='charadd', aliases=['addchar', 'givechar'])
    @commands.has_permissions(administrator=True)
    async def char_add(ctx, *, character_name: str):
        character = _find_character_id_by_name(character_name)
        if not character:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado.**", discord.Color.red())
            return

        character_id, canonical_name = character

        c.execute(
            """
            SELECT id, name, type, rarity
            FROM characteristic_definitions
            ORDER BY name COLLATE NOCASE
            """
        )
        characteristics = c.fetchall()

        if not characteristics:
            await send_embed(
                ctx,
                "**__```𝐄𝐑𝐑𝐎```__**",
                "- > **Nenhuma característica disponível no sistema.**",
                discord.Color.red(),
            )
            return

        char_list = "\n".join(
            [f"**{i+1}.** {name} ({ctype} | {rarity})" for i, (char_id, name, ctype, rarity) in enumerate(characteristics)]
        )
        await send_embed(
            ctx,
            "**__```𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀𝐒 𝐃𝐈𝐒𝐏𝐎𝐍𝐈́𝐕𝐄𝐈𝐒```__**",
            f"- > **Escolha uma para {canonical_name}:\n{char_list}**\n\n- > **Responda com o número.**",
            discord.Color.blue(),
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            response = await ctx.bot.wait_for('message', check=check, timeout=60.0)
            try:
                char_idx = int(response.content.strip()) - 1
                if 0 <= char_idx < len(characteristics):
                    characteristic_id, canonical_trait_name, _, _ = characteristics[char_idx]
                    c.execute(
                        "INSERT OR IGNORE INTO character_characteristics (character_id, characteristic_id) VALUES (?, ?)",
                        (character_id, characteristic_id),
                    )
                    conn.commit()

                    if c.rowcount == 0:
                        await send_embed(
                            ctx,
                            "**__```𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀 𝐉𝐀́ 𝐄𝐗𝐈𝐒𝐓𝐄```__**",
                            f"- > **{canonical_name} já possui {canonical_trait_name}.**",
                            discord.Color.orange(),
                        )
                    else:
                        await send_embed(
                            ctx,
                            "**__```𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀 𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐃𝐀```__**",
                            f"- > **{canonical_trait_name} foi aplicada em {canonical_name}.**",
                            discord.Color.green(),
                        )
                else:
                    await send_embed(
                        ctx,
                        "**__```𝐄𝐑𝐑𝐎```__**",
                        "- > **Número inválido.**",
                        discord.Color.red(),
                    )
            except ValueError:
                await send_embed(
                    ctx,
                    "**__```𝐄𝐑𝐑𝐎```__**",
                    "- > **Resposta inválida. Digite um número.**",
                    discord.Color.red(),
                )
        except asyncio.TimeoutError:
            await send_embed(
                ctx,
                "**__```𝐓𝐈𝐌𝐄𝐎𝐔𝐓```__**",
                "- > **Tempo esgotado.**",
                discord.Color.red(),
            )

    @bot.command(name='charremove', aliases=['removechar', 'takechar'])
    @commands.has_permissions(administrator=True)
    async def char_remove(ctx, *, args: str):
        character_name, characteristic_name = _parse_two_quoted_tokens(args)
        if not character_name or not characteristic_name:
            await send_embed(
                ctx,
                "**__```𝐅𝐎𝐑𝐌𝐀𝐓𝐎 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐎```__**",
                "- > **Use:** `kill!charremove 'Nome do Personagem' 'Nome da Característica'`",
                discord.Color.red(),
            )
            return

        character = _find_character_id_by_name(character_name)
        if not character:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado.**", discord.Color.red())
            return

        definition = _find_characteristic_definition_by_name(characteristic_name)
        if not definition:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Característica não encontrada em characteristic_definitions.**", discord.Color.red())
            return

        character_id, canonical_name = character
        characteristic_id, canonical_trait_name, _, _ = definition

        c.execute(
            "DELETE FROM character_characteristics WHERE character_id = ? AND characteristic_id = ?",
            (character_id, characteristic_id),
        )
        conn.commit()

        if c.rowcount == 0:
            await send_embed(
                ctx,
                "**__```𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀 𝐍𝐀̃𝐎 𝐄𝐍𝐂𝐎𝐍𝐓𝐑𝐀𝐃𝐀```__**",
                f"- > **{canonical_name} não possui {canonical_trait_name}.**",
                discord.Color.orange(),
            )
            return

        await send_embed(
            ctx,
            "**__```𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐀```__**",
            f"- > **{canonical_trait_name} foi removida de {canonical_name}.**",
            discord.Color.green(),
        )

async def setup(bot):
    register_characteristics_commands(bot)
