import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import re
import sqlite3
import math
import datetime
from typing import Optional
from database.connection import create_connection
from utils.common import (
    apply_layout as shared_apply_layout,
    parse_quoted_args,
    send_embed,
    to_bold_sans_serif,
)
from commands.xp import xp_for_next_level
from services.characteristics_service import get_effective_attribute

conn = create_connection()
c = conn.cursor()

def parse_registration_args(args):
    tokens = parse_quoted_args(args)

    name = tokens[0] if len(tokens) > 0 else None
    return name


def get_inventory_capacity(rank):
    rank_capacities = {
        'F-': 4, 'F': 8, 'F+': 12, 'E-': 16, 'E': 20, 'E+': 24,
        'D-': 28, 'D': 32, 'D+': 36, 'C-': 40, 'C': 44, 'C+': 48,
        'B-': 52, 'B': 56, 'B+': 60, 'A-': 64, 'A': 68, 'A+': 72,
        'S': 76, 'S+': 80, 'SS': 84, 'SS+': 88, 'SSS': 92, 'SSS+': 96,
        'Z': 100
    }
    return rank_capacities.get(rank, 4)

def apply_layout(user_id, title, description):
    return shared_apply_layout(
        user_id,
        title,
        description,
        default_title="╚ **╚═══━═─ ✦ ─═━═══╗**\n**╚╡ ⬥ {title} ⬥ ╞**",
        default_description="╚───► *「{description}」*",
    )

def register_commands(bot):
    @bot.command(name='register', aliases=['reg', 'novo'])
    async def register(ctx, *, args: str):
        name = parse_registration_args(args)
        if not name:
            await send_embed(ctx, "**__```𝐅𝐎𝐑𝐌𝐀𝐓𝐎 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐎```__**", "- > **Use: kill!register 'Nome'**", discord.Color.red())
            return

        c.execute("SELECT 1 FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (name, ctx.author.id))
        if c.fetchone():
            await send_embed(ctx, "**__```𝐍𝐎𝐌𝐄 𝐄𝐌 𝐔𝐒𝐎```__**", "- > **Você já tem um personagem com esse nome.**", discord.Color.red())
            return

        image_url = ctx.message.attachments[0].url if ctx.message.attachments else None
        message_id = ctx.message.id if ctx.message.attachments else None
        user_id = ctx.author.id

        try:
            # 1. Insert into characters (identity only)
            c.execute(
                "INSERT INTO characters (name, image_url, user_id, soul_tier) VALUES (?, ?, ?, 'Unknown')",
                (name, image_url, user_id)
            )
            character_id = c.lastrowid
            
            # 2. Initialize progression
            c.execute(
                """INSERT INTO character_progression 
                   (character_id, experience, level, rank, points_available, message_count, message_id)
                   VALUES (?, 0, 1, 'F-', 0, 0, ?)""",
                (character_id, message_id)
            )
            
            # 3. Initialize race (Unknown)
            c.execute(
                """INSERT INTO character_race_progression 
                   (character_id, race_name)
                   VALUES (?, 'Unknown')""",
                (character_id,)
            )
            
            # 4. Initialize Reiryoku
            c.execute(
                """INSERT INTO character_reiryoku 
                   (character_id, core_color, core_stage, reiryoku_base_pool, reiryoku_current)
                   VALUES (?, 'Black', 'Dark Stage', 100, 100)""",
                (character_id,)
            )
            
            # 5. Initialize 10 Reiryoku skills
            base_skills = ['Ten', 'Zetsu', 'Ren', 'Hatsu', 'Gyo', 'Shu', 'Ko', 'Ken', 'En', 'Ryu']
            for skill in base_skills:
                c.execute(
                    """INSERT INTO character_reiryoku_skills 
                       (character_id, skill_name, mastery_level, control_level, is_awakened)
                       VALUES (?, ?, 0, 0, 0)""",
                    (character_id, skill)
                )
            
            conn.commit()
            
            await send_embed(ctx, "**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐃𝐎 ✨```__**",
                             f'- > **Personagem __{name}__ registrado com sucesso!**\n- > Soul tier: Unknown\n- > Reiryoku: Black Core (Dark Stage)\n- > Reiatsu: não definido (configure com /reiatsu)\n- > Reiryoku Skills: 10 técnicas-base desbloqueadas!',
                             discord.Color.green(), image_url,
                             "use `kill!details NomeDoPersonagem` para ver o perfil")
        except sqlite3.IntegrityError as e:
            conn.rollback()
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > Erro ao registrar: {e}", discord.Color.red())

    @bot.command(name='remove', aliases=['rm'])
    async def remove(ctx, *, name: str):
        c.execute("DELETE FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (name, ctx.author.id))
        if c.rowcount == 0:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para removê-lo.**", discord.Color.red())
        else:
            conn.commit()
            await send_embed(ctx, "**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐎```__**", f'- > **Personagem __{name}__ removido com sucesso.**', discord.Color.green(), next_step="use `kill!register 'Nome'` para criar outro")

    @bot.command(name='details', aliases=['det', 'perfil'])
    async def details(ctx, *, name: str):
        c.execute("""
             SELECT c.character_id, c.name, c.image_url,
                 p.experience, p.level, p.points_available,
                 p.forca, p.resistencia, p.agilidade, p.sentidos, p.vitalidade, p.inteligencia,
                 p.rank, p.message_count, COALESCE(c.registered_at, p.created_at),
                 r.race_name, r.race_stage, r.race_stage_level,
                 re.core_color, re.core_stage, re.reiryoku_base_pool, re.reiryoku_current,
                 ra.primary_category, ra.primary_category_level
            FROM characters c
            LEFT JOIN character_progression p ON c.character_id = p.character_id
             LEFT JOIN character_race_progression r ON c.character_id = r.character_id
             LEFT JOIN character_reiryoku re ON c.character_id = re.character_id
             LEFT JOIN character_reiatsu_affinities ra ON c.character_id = ra.character_id
            WHERE c.name COLLATE NOCASE=? AND c.user_id=?
        """, (name, ctx.author.id))
        character = c.fetchone()

        if not character:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para visualizá-lo.**", discord.Color.red())
            return

        (
            character_id,
            name,
            image_url,
            experience,
            level,
            points,
            forca,
            resistencia,
            agilidade,
            sentidos,
            vitalidade,
            inteligencia,
            rank,
            message_count,
            registered_at,
            race_name,
            race_stage,
            race_stage_level,
            core_color,
            core_stage,
            reiryoku_base_pool,
            reiryoku_current,
            reiatsu_category,
            reiatsu_level,
        ) = character

        effective_forca = get_effective_attribute(character_id, "forca", forca)
        effective_resistencia = get_effective_attribute(character_id, "resistencia", resistencia)
        effective_agilidade = get_effective_attribute(character_id, "agilidade", agilidade)
        effective_sentidos = get_effective_attribute(character_id, "sentidos", sentidos)
        effective_vitalidade = get_effective_attribute(character_id, "vitalidade", vitalidade)
        effective_inteligencia = get_effective_attribute(character_id, "inteligencia", inteligencia)

        c.execute("SELECT main_class, sub_class1, sub_class2 FROM characters_classes WHERE character_id=?", (character_id,))
        classes = c.fetchone()

        main_class = classes[0] if classes and classes[0] else "𝐍𝐎𝐍𝐄"
        sub_class1 = classes[1] if classes and classes[1] else "𝐍𝐎𝐍𝐄"
        sub_class2 = classes[2] if classes and classes[2] else "𝐍𝐎𝐍𝐄"

        points_info = f"{points}" if points > 0 else "𝐍𝐎𝐍𝐄"
        race_info = f"{race_name or '𝐍𝐎𝐍𝐄'} • {race_stage or '𝐁𝐀𝐒𝐄'} ({race_stage_level or 0}%)"
        core_info = f"{core_color or 'Black'} Core • {core_stage or 'Dark Stage'} ({reiryoku_current or 0}/{reiryoku_base_pool or 0})"
        reiatsu_info = f"{reiatsu_category or '𝐍𝐎𝐍𝐄'} (Nv. {reiatsu_level or 0})"

        c.execute("SELECT rebirth_count FROM rebirths WHERE character_name=? AND user_id=?", (name, ctx.author.id))
        rebirth_data = c.fetchone()
        rebirth_count = rebirth_data[0] if rebirth_data else 0  

        
        description = (
            f"``` 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍 ```- — ◇\n"
            f"> **__𝐍𝐀𝐌𝐄__**\n"
            f"● *{name}*\n"
            f"> **__𝐋𝐄𝐕𝐄𝐋__**\n"
            f"● *{level}*\n"
            f"> **__𝐄𝐗𝐏__**\n"
            f"○ *{experience}/{xp_for_next_level(level)}*\n"
            f"> **__𝐑𝐀𝐂𝐄__**\n"
            f"● *{race_info}*\n"
            f"> **__𝐑𝐄𝐈𝐀𝐓𝐒𝐔__**\n"
            f"○ *{reiatsu_info}*\n"
            f"> **__𝐂𝐎𝐑𝐄__**\n"
            f"● *{core_info}*\n"
            f"> **__𝐂𝐋𝐀𝐒𝐒__**\n"
            f"● *{main_class}*\n"
            f"> **__𝐒𝐔𝐁𝐂𝐋𝐀𝐒𝐒__**\n"
            f"○ *{sub_class1}, {sub_class2}*\n\n"
            f"- — *[* **𝐏𝐎𝐈𝐍𝐓𝐒: ** ` {points_info} ` *]* —\n"
            f"● ○ ***[*** `𝐑𝐀𝐍𝐊 {rank}` ***]*** ○ ●"
        )

        embed = discord.Embed(title="``` 𝔻𝔼𝕋𝔸𝕀𝕃𝕊 ```", description=description, color=discord.Color.dark_grey())
        if image_url:
            embed.set_image(url=image_url)

        button_status = Button(label="𝐒𝐓𝐀𝐓𝐔𝐒", style=discord.ButtonStyle.secondary, custom_id="show_status")
        button_inventory = Button(label="𝐈𝐍𝐕𝐄𝐍𝐓𝐎𝐑𝐘", style=discord.ButtonStyle.secondary, custom_id="show_inventory")
        button_techniques = Button(label="𝐓𝐄𝐂𝐇𝐍𝐈𝐐𝐔𝐄𝐒", style=discord.ButtonStyle.secondary, custom_id="show_techniques")

        async def button_status_callback(interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("- > **Você não tem permissão para ver os status deste personagem.**", ephemeral=True)
                return

            status_description = (
                f"# — • ***[*** __𝐀𝐓𝐓𝐑𝐈𝐁𝐔𝐓𝐄𝐒__ ***]*** • —\n"
                f"- ``` . . . ```\n"
                f"- 𝐒𝐓𝐑𝐄𝐍𝐆𝐓𝐇 ***[*** ` {effective_forca} ` ***]***\n"
                f"- 𝐑𝐄𝐒𝐈𝐒𝐓𝐀𝐍𝐂𝐄 ***[*** ` {effective_resistencia} ` ***]***\n"
                f"- 𝐀𝐆𝐈𝐋𝐈𝐓𝐘 ***[*** ` {effective_agilidade} ` ***]***\n"
                f"- 𝐒𝐄𝐍𝐒𝐄𝐒 ***[*** ` {effective_sentidos} ` ***]***\n"
                f"- 𝐕𝐈𝐓𝐀𝐋𝐈𝐓𝐘 ***[*** ` {effective_vitalidade} ` ***]***\n"
                f"- 𝐈𝐍𝐓𝐄𝐋𝐋𝐈𝐆𝐄𝐍𝐂𝐄 ***[*** ` {effective_inteligencia} ` ***]***\n"
                f"- 𝐏𝐎𝐈𝐍𝐓𝐒 ***[*** ` {points} ` ***]***\n"
                f"- ``` . . . ```\n"
                f"● **__𝐑𝐄𝐁𝐈𝐑𝐓𝐇𝐒__** ***[*** ` {rebirth_count} ` ***]***\n"
                f"- ``` . . . ```"
            )

            status_embed = discord.Embed(title="𝕊𝕋𝔸𝕋𝕌𝕊", description=status_description, color=discord.Color.dark_grey())
            button_details = Button(label="𝐃𝐄𝐓𝐀𝐈𝐋𝐒", style=discord.ButtonStyle.secondary, custom_id="show_details")

            async def button_details_callback(interaction):
                await interaction.response.edit_message(embed=embed, view=view)

            button_details.callback = button_details_callback
            status_view = View()
            status_view.add_item(button_details)
            await interaction.response.edit_message(embed=status_embed, view=status_view)

        async def button_inventory_callback(interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("- > **Você não tem permissão para ver o inventário deste personagem.**", ephemeral=True)
                return

            c.execute("SELECT item_name, description, image_url FROM inventory WHERE character_name COLLATE NOCASE=? AND user_id=?", (name, ctx.author.id))
            items = c.fetchall()
            per_page = 5
            total_pages = math.ceil(len(items) / per_page)
            current_page = 1

            async def update_inventory_message(interaction, page):
                if page < 1:
                    page = total_pages
                elif page > total_pages:
                    page = 1
                inventory_embed = await create_inventory_embed(items, page, per_page, total_pages, name)
                await interaction.response.edit_message(embed=inventory_embed, view=create_inventory_view(page))

            def create_inventory_view(page):
                view = View()
                buttons = [("⏪", 1), ("◀", page - 1), ("𝐃𝐄𝐓𝐀𝐈𝐋𝐒", None), ("▶", page + 1), ("⏩", total_pages)]
                for label, target_page in buttons:
                    button = Button(label=label, style=discord.ButtonStyle.secondary)
                    if target_page is not None:
                        button.callback = lambda interaction, tp=target_page: update_inventory_message(interaction, tp)
                    else:
                        button.callback = return_to_details
                    view.add_item(button)
                return view

            async def create_inventory_embed(items, page, per_page, total_pages, character_name):
                start = (page - 1) * per_page
                end = start + per_page
                item_list = items[start:end]

                formatted_name = to_bold_sans_serif(character_name)

                embed = discord.Embed(title=f"𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎 𝐃𝐄 {formatted_name} (página {page}/{total_pages})", color=discord.Color.dark_grey())

                description = "\n".join([
                    apply_layout(ctx.author.id, f"**{item_name}**", description)[0] + "\n" + apply_layout(ctx.author.id, f"**{item_name}**", description)[1]  
                    for item_name, description, image_url in item_list
                ])
                embed.description = description
                return embed

            async def return_to_details(interaction):
                await interaction.response.edit_message(embed=embed, view=view)

            inventory_embed = await create_inventory_embed(items, current_page, per_page, total_pages, name)
            await interaction.response.edit_message(embed=inventory_embed, view=create_inventory_view(current_page))


        async def button_techniques_callback(interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("- > **Você não tem permissão para ver as técnicas deste personagem.**", ephemeral=True)
                return

            c.execute("SELECT technique_name, description FROM techniques WHERE character_id=?", (character_id,))
            techniques = c.fetchall()
            per_page = 5
            total_pages = math.ceil(len(techniques) / per_page)
            current_page = 1

            async def update_techniques_message(interaction, page):
                if page < 1:
                    page = total_pages
                elif page > total_pages:
                    page = 1
                techniques_embed = await create_techniques_embed(techniques, page, per_page, total_pages, name)
                await interaction.response.edit_message(embed=techniques_embed, view=create_technique_view(page))

            def create_technique_view(page):
                view = View()
                buttons = [("⏪", 1), ("◀", page - 1), ("𝐃𝐄𝐓𝐀𝐈𝐋𝐒", None), ("▶", page + 1), ("⏩", total_pages)]
                for label, target_page in buttons:
                    button = Button(label=label, style=discord.ButtonStyle.secondary)
                    button.callback = lambda interaction, tp=target_page: update_techniques_message(interaction, tp) if tp else return_to_details(interaction)
                    view.add_item(button)
                return view

            async def create_techniques_embed(techniques, page, per_page, total_pages, character_name):
                start = (page - 1) * per_page
                end = start + per_page
                technique_list = techniques[start:end]

                formatted_name = to_bold_sans_serif(character_name)

                embed = discord.Embed(title=f"𝐓𝐄́𝐂𝐍𝐈𝐂𝐀𝐒 𝐃𝐄 {formatted_name} (página {page}/{total_pages})", color=discord.Color.dark_grey())

                description = "\n".join([
                    apply_layout(ctx.author.id, f"{technique_name}", description)[0] + "\n" + apply_layout(ctx.author.id, f"{technique_name}", description)[1]  
                    for technique_name, description in technique_list
                ])
                embed.description = description
                return embed

            async def return_to_details(interaction):
                await interaction.response.edit_message(embed=embed, view=view)

            techniques_embed = await create_techniques_embed(techniques, current_page, per_page, total_pages, name)
            await interaction.response.edit_message(embed=techniques_embed, view=create_technique_view(current_page))

        button_status.callback = button_status_callback
        button_inventory.callback = button_inventory_callback
        button_techniques.callback = button_techniques_callback

        view = View()
        view.add_item(button_status)
        view.add_item(button_inventory)
        view.add_item(button_techniques)

        await ctx.send(embed=embed, view=view)

    @bot.command(name='avatar', aliases=['av'])
    async def avatar(ctx, *, name: str):
        c.execute("SELECT image_url, message_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para visualizar ou atualizar o avatar.**", discord.Color.red())
        else:
            if ctx.message.attachments:
                image_url = ctx.message.attachments[0].url
                message_id = ctx.message.id
                c.execute("UPDATE characters SET image_url=?, message_id=? WHERE name COLLATE NOCASE=? AND user_id=?", (image_url, message_id, name, ctx.author.id))
                conn.commit()
                await send_embed(ctx, "**__```𝐀𝐕𝐀𝐓𝐀𝐑 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐎!!!```__**", f"- > **Avatar do personagem __{name}__ atualizado com sucesso.**", discord.Color.green(), image_url, "use `kill!details NomeDoPersonagem` para revisar")
            else:
                image_url, message_id = character
                if image_url:
                    try:
                        original_message = await ctx.channel.fetch_message(message_id)
                        if original_message:
                            await send_embed(ctx, f"**__```𝐀𝐕𝐀𝐓𝐀𝐑```__**", "", discord.Color.blue(), image_url)
                    except discord.errors.NotFound:
                        c.execute("UPDATE characters SET image_url=NULL, message_id=NULL WHERE name COLLATE NOCASE=? AND user_id=?", (name, ctx.author.id))
                        conn.commit()
                        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Nenhum avatar definido para o personagem {name}. Para definir um avatar, forneça um link direto para a imagem ou faça o upload como um anexo ao executar este comando.**", discord.Color.red())
                else:
                    await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Nenhum avatar definido para o personagem {name}. Para definir um avatar, forneça um link direto para a imagem ou faça o upload como um anexo ao executar este comando.**", discord.Color.red())

    @bot.command(name='rename', aliases=['ren'])
    async def rename(ctx, *, args: str):
        match = re.match(r"'(.+?)'\s*'(.+?)'", args)
        if not match:
            await send_embed(
                ctx,
                "**__```𝐅𝐎𝐑𝐌𝐀𝐓𝐎 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐎```__**",
                "- > **Use: kill!rename 'Nome Antigo' 'Nome Novo'**",
                discord.Color.red()
            )
            return

        old_name, new_name = match.groups()

        c.execute("SELECT 1 FROM characters WHERE name=? AND user_id=?", (new_name, ctx.author.id))
        existing_character = c.fetchone()

        if existing_character and old_name.lower() != new_name.lower():
            await send_embed(
                ctx,
                "**__```𝐍𝐎𝐌𝐄 𝐄𝐌 𝐔𝐒𝐎```__**",
                "- > **O nome já está em uso.**",
                discord.Color.red()
            )
            return

        c.execute("UPDATE characters SET name=? WHERE name=? AND user_id=?", (new_name, old_name, ctx.author.id))
        if c.rowcount == 0:
            await send_embed(
                ctx,
                "**__```𝐄𝐑𝐑𝐎```__**",
                '- > **Personagem não encontrado ou você não tem permissão para renomeá-lo.**',
                discord.Color.red()
            )
        else:
            conn.commit()
            await send_embed(
                ctx,
                "**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐑𝐄𝐍𝐎𝐌𝐄𝐀𝐃𝐎```__**",
                f'- > **Personagem __{old_name}__ renomeado para __{new_name}__ com sucesso.**',
                discord.Color.green(),
                next_step="use `kill!details NovoNome` para validar"
            )

    @bot.command(name='list', aliases=['chars', 'meus'])
    async def list_characters(ctx, member: Optional[discord.Member] = None):
        user_id = member.id if member else ctx.author.id
        display_name = member.display_name if member else ctx.author.display_name

        c.execute("SELECT private FROM characters WHERE user_id=? LIMIT 1", (user_id,))
        private_status = c.fetchone()
        if private_status and private_status[0] == 1 and ctx.author.id != user_id:
            await send_embed(ctx, "**__```𝐀𝐂𝐄𝐒𝐒𝐎 𝐍𝐄𝐆𝐀𝐃𝐎```__**", "- > **Os personagens deste usuário são privados.**", discord.Color.red())
            return

        c.execute("""
            SELECT c.name, c.image_url, p.message_count, COALESCE(c.registered_at, p.created_at)
            FROM characters c
            LEFT JOIN character_progression p ON c.character_id = p.character_id
            WHERE c.user_id=?
        """, (user_id,))
        characters = c.fetchall()
        if not characters:
            await send_embed(ctx, "**__```𝐍𝐄𝐍𝐇𝐔𝐌 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐄𝐍𝐂𝐎𝐍𝐓𝐑𝐀𝐃𝐎```__**", "- > **Nenhum personagem registrado.**", discord.Color.red())
            return

        per_page = 5
        total_results = len(characters)
        total_pages = math.ceil(total_results / per_page)
        current_page = 1

        async def update_message(interaction, page):
            if page < 1:
                page = total_pages
            elif page > total_pages:
                page = 1
            embed = await create_list_embed(characters, page, per_page, total_pages, total_results, display_name)
            await interaction.response.edit_message(embed=embed, view=create_list_view(page))

        def create_list_view(page):
            view = View()
            buttons = [
                ("⏪", 1), ("◀", page - 1), (". . .", None), ("▶", page + 1), ("⏩", total_pages)
            ]
            for label, target_page in buttons:
                button = Button(label=label, style=discord.ButtonStyle.secondary)
                if target_page is not None:
                    button.callback = lambda interaction, tp=target_page: update_message(interaction, tp)
                else:
                    button.callback = create_page_modal
                view.add_item(button)
            return view

        async def create_page_modal(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("- > **Você não pode usar este comando.**", ephemeral=True)
                return

            modal = GoToPageModal(update_message, total_pages)
            await interaction.response.send_modal(modal)

        embed = await create_list_embed(characters, current_page, per_page, total_pages, total_results, display_name)
        await ctx.send(embed=embed, view=create_list_view(current_page))
    
    async def create_list_embed(characters, page, per_page, total_pages, total_results, display_name):
        start = (page - 1) * per_page
        end = start + per_page
        formatted_name = to_bold_sans_serif(display_name)
        embed = discord.Embed(title=f"𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐍𝐒 𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐃𝐎𝐒 𝐃𝐄 {formatted_name} (𝐏𝐀́𝐆𝐈𝐍𝐀 {page}/{total_pages})", color=discord.Color.dark_grey())
        result_list = [
            f"**{name}**\n[𝐀𝐕𝐀𝐓𝐀𝐑]({image_url if image_url else '𝐍𝐎 𝐀𝐕𝐀𝐓𝐀𝐑'})\n𝐓𝐎𝐓𝐀𝐋 𝐌𝐄𝐒𝐒𝐀𝐆𝐄𝐒 𝐒𝐄𝐍𝐓: {message_count}\n𝐑𝐄𝐆𝐈𝐒𝐓𝐄𝐑𝐄𝐃: {registered_at}\n"
            for name, image_url, message_count, registered_at in characters[start:end]
        ]
        embed.description = "\n".join(result_list)
        embed.set_footer(text=f"𝐏𝐀́𝐆𝐈𝐍𝐀 {page}/{total_pages} • 𝐓𝐎𝐓𝐀𝐋 𝐃𝐄 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐍𝐒: {total_results}")
        return embed

    class GoToPageModal(Modal):
        def __init__(self, update_message, total_pages):
            super().__init__(title="𝐈𝐑 𝐏𝐀𝐑𝐀 𝐏𝐀́𝐆𝐈𝐍𝐀")
            self.update_message = update_message
            self.total_pages = total_pages
            self.page_number = TextInput(label="𝐍𝐔́𝐌𝐄𝐑𝐎 𝐃𝐀 𝐏𝐀́𝐆𝐈𝐍𝐀", style=discord.TextStyle.short)
            self.add_item(self.page_number)

        async def on_submit(self, interaction):
            try:
                page = int(self.page_number.value)
                if 1 <= page <= self.total_pages:
                    await self.update_message(interaction, page)
                else:
                    await interaction.response.send_message(f"Número de página inválido. Digite um número entre 1 e {self.total_pages}.", ephemeral=True)
            except ValueError:

                await interaction.response.send_message("Número de página inválido. Digite um inteiro válido.", ephemeral=True)


async def setup(bot):
    register_commands(bot)
