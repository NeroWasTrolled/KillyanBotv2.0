import discord
from discord.ext import commands
from logs import Logs
from discord.ui import Button, View, Modal, TextInput
import re
import sqlite3
import math
import datetime
from xp import xp_for_next_level

conn = sqlite3.connect('characters.db', check_same_thread=False)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")

def apply_layout(user_id, title, description):
    c.execute("SELECT title_layout, description_layout FROM layout_settings WHERE user_id=?", (user_id,))
    layout = c.fetchone()

    if layout:
        title_layout, description_layout = layout
    else:
        title_layout = "╚ **╚═══━═─ ✦ ─═━═══╗**\n**╚╡ ⬥ {title} ⬥ ╞**"
        description_layout = "╚───► *「{description}」*"

    formatted_title = title_layout.replace("{title}", title)
    formatted_description = description_layout.replace("{description}", description)

    return formatted_title, formatted_description


def to_bold_sans_serif(text):
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
    return ''.join(bold_sans_serif.get(c, c) for c in text.upper())

def parse_registration_args(args):
    pattern = r'\'(.*?)\'|(\S+)'
    matches = re.findall(pattern, args)
    tokens = [match[0] if match[0] else match[1] for match in matches]

    name = tokens[0] if len(tokens) > 0 else None
    return name

async def send_embed(ctx, title, description, color=discord.Color.blue(), image_url=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if image_url:
        embed.set_image(url=image_url)
    await ctx.send(embed=embed)

def register_commands(bot):
    @bot.command(name='register')
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
        registered_at = datetime.datetime.now().strftime("%Y-%m-%d")
        message_id = ctx.message.id if ctx.message.attachments else None

        c.execute(
            "INSERT INTO characters (name, image_url, user_id, registered_at, message_id) VALUES (?, ?, ?, ?, ?)",
            (name, image_url, ctx.author.id, registered_at, message_id)
        )
        conn.commit()
        await send_embed(ctx, "**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐃𝐎!!!```__**",
                         f'- > **Personagem __{name}__ registrado com sucesso!**',
                         discord.Color.green(), image_url)

    @bot.command(name='remove')
    async def remove(ctx, *, name: str):
        c.execute("DELETE FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (name, ctx.author.id))
        if c.rowcount == 0:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para removê-lo.**", discord.Color.red())
        else:
            conn.commit()
            await send_embed(ctx, "**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐎```__**", f'- > **Personagem __{name}__ removido com sucesso.**', discord.Color.green())

    @bot.command(name='details')
    async def details(ctx, *, name: str):
        c.execute("SELECT character_id, name, image_url, experience, level, points, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia, rank, message_count, registered_at FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (name, ctx.author.id))
        character = c.fetchone()

        if not character:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para visualizá-lo.**", discord.Color.red())
            return

        character_id, name, image_url, experience, level, points, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia, rank, message_count, registered_at = character

        c.execute("SELECT main_class, sub_class1, sub_class2 FROM characters_classes WHERE character_id=?", (character_id,))
        classes = c.fetchone()

        main_class = classes[0] if classes and classes[0] else "𝐍𝐎𝐍𝐄"
        sub_class1 = classes[1] if classes and classes[1] else "𝐍𝐎𝐍𝐄"
        sub_class2 = classes[2] if classes and classes[2] else "𝐍𝐎𝐍𝐄"

        points_info = f"{points}" if points > 0 else "𝐍𝐎𝐍𝐄"

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
                f"- 𝐒𝐓𝐑𝐄𝐍𝐆𝐓𝐇 ***[*** ` {forca} ` ***]***\n"
                f"- 𝐑𝐄𝐒𝐈𝐒𝐓𝐀𝐍𝐂𝐄 ***[*** ` {resistencia} ` ***]***\n"
                f"- 𝐀𝐆𝐈𝐋𝐈𝐓𝐘 ***[*** ` {agilidade} ` ***]***\n"
                f"- 𝐒𝐄𝐍𝐒𝐄𝐒 ***[*** ` {sentidos} ` ***]***\n"
                f"- 𝐕𝐈𝐓𝐀𝐋𝐈𝐓𝐘 ***[*** ` {vitalidade} ` ***]***\n"
                f"- 𝐈𝐍𝐓𝐄𝐋𝐋𝐈𝐆𝐄𝐍𝐂𝐄 ***[*** ` {inteligencia} ` ***]***\n"
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

    @bot.command(name='avatar')
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
                await send_embed(ctx, "**__```𝐀𝐕𝐀𝐓𝐀𝐑 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐎!!!```__**", f"- > **Avatar do personagem __{name}__ atualizado com sucesso.**", discord.Color.green(), image_url)
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

    @bot.command(name='rename')
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
                discord.Color.green()
            )

    @bot.command(name='list')
    async def list_characters(ctx, member: discord.Member = None):
        user_id = member.id if member else ctx.author.id
        display_name = member.display_name if member else ctx.author.display_name

        c.execute("SELECT private FROM characters WHERE user_id=? LIMIT 1", (user_id,))
        private_status = c.fetchone()
        if private_status and private_status[0] == 1 and ctx.author.id != user_id:
            await send_embed(ctx, "**__```𝐀𝐂𝐄𝐒𝐒𝐎 𝐍𝐄𝐆𝐀𝐃𝐎```__**", "- > **Os personagens deste usuário são privados.**", discord.Color.red())
            return

        c.execute("SELECT name, image_url, message_count, registered_at FROM characters WHERE user_id=?", (user_id,))
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
        embed = discord.Embed(title=f"{display_name}'𝐒 𝐑𝐄𝐆𝐈𝐒𝐓𝐄𝐑𝐄𝐃 𝐂𝐇𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐒 (𝐏𝐀𝐆𝐄 {page}/{total_pages})", color=discord.Color.dark_grey())
        result_list = [
            f"**{name}**\n[𝐀𝐕𝐀𝐓𝐀𝐑]({image_url if image_url else '𝐍𝐎 𝐀𝐕𝐀𝐓𝐀𝐑'})\n𝐓𝐎𝐓𝐀𝐋 𝐌𝐄𝐒𝐒𝐀𝐆𝐄𝐒 𝐒𝐄𝐍𝐓: {message_count}\n𝐑𝐄𝐆𝐈𝐒𝐓𝐄𝐑𝐄𝐃: {registered_at}\n"
            for name, image_url, message_count, registered_at in characters[start:end]
        ]
        embed.description = "\n".join(result_list)
        embed.set_footer(text=f"𝐏𝐀𝐆𝐄 {page}/{total_pages} • 𝐓𝐎𝐓𝐀𝐋 𝐂𝐇𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐒: {total_results}")
        return embed

    class GoToPageModal(Modal):
        def __init__(self, update_message, total_pages):
            super().__init__(title="𝐆𝐎 𝐓𝐎 𝐏𝐀𝐆𝐄")
            self.update_message = update_message
            self.total_pages = total_pages
            self.page_number = TextInput(label="𝐏𝐀𝐆𝐄 𝐍𝐔𝐌𝐁𝐄𝐑", style=discord.TextStyle.short)
            self.add_item(self.page_number)

        async def on_submit(self, interaction):
            try:
                page = int(self.page_number.value)
                if 1 <= page <= self.total_pages:
                    await self.update_message(interaction, page)
                else:
                    await interaction.response.send_message(f"Invalid page number. Please enter a number between 1 and {self.total_pages}.", ephemeral=True)
            except ValueError:
                await interaction.response.send_message("Invalid page number. Please enter a valid integer.", ephemeral=True)
