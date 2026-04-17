import discord

from database.connection import create_connection
from services.characteristics_service import get_effective_attribute
from commands.register import get_inventory_capacity

conn = create_connection()
c = conn.cursor()


def register_register_slash_commands(bot):
    @bot.tree.command(name='register', description='Registra um novo personagem')
    async def register_slash(interaction: discord.Interaction, name: str, image_url: str | None = None):
        c.execute("SELECT 1 FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (name, interaction.user.id))
        if c.fetchone():
            embed = discord.Embed(
                title="**__```𝐍𝐎𝐌𝐄 𝐄𝐌 𝐔𝐒𝐎```__**",
                description="- > **Você já tem um personagem com esse nome.**",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        c.execute(
            "INSERT INTO characters (name, image_url, user_id) VALUES (?, ?, ?)",
            (name, image_url, interaction.user.id),
        )
        conn.commit()

        embed = discord.Embed(
            title="**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐃𝐎!!!```__**",
            description=f'- > **Personagem __{name}__ registrado com sucesso!**\n\n- > **Próximo passo:** use `kill!details {name}` para ver o perfil',
            color=discord.Color.green(),
        )
        if image_url:
            embed.set_image(url=image_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name='remove', description='Remove um personagem seu')
    async def remove_slash(interaction: discord.Interaction, name: str):
        c.execute("DELETE FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (name, interaction.user.id))
        if c.rowcount == 0:
            embed = discord.Embed(
                title="**__```𝐄𝐑𝐑𝐎```__**",
                description="- > **Personagem não encontrado ou você não tem permissão para removê-lo.**",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        conn.commit()
        embed = discord.Embed(
            title="**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐀```__**",
            description=f'- > **Personagem __{name}__ removido com sucesso.**\n\n- > **Próximo passo:** use `kill!register` para criar outro',
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name='details', description='Mostra detalhes do personagem')
    async def details_slash(interaction: discord.Interaction, name: str):
        c.execute(
            """
         SELECT c.character_id, c.name, c.image_url,
             p.experience, p.level, p.points_available, p.rank,
             p.forca, p.resistencia, p.agilidade, p.sentidos, p.vitalidade, p.inteligencia,
             r.race_name, r.race_stage, r.race_stage_level,
             re.core_color, re.core_stage, re.reiryoku_base_pool, re.reiryoku_current,
             ra.primary_category, ra.primary_category_level
            FROM characters c
            LEFT JOIN character_progression p ON c.character_id = p.character_id
         LEFT JOIN character_race_progression r ON c.character_id = r.character_id
         LEFT JOIN character_reiryoku re ON c.character_id = re.character_id
         LEFT JOIN character_reiatsu_affinities ra ON c.character_id = ra.character_id
            WHERE c.name COLLATE NOCASE=? AND c.user_id=?
            """,
            (name, interaction.user.id),
        )
        row = c.fetchone()
        if not row:
            embed = discord.Embed(
                title="**__```𝐄𝐑𝐑𝐎```__**",
                description="- > **Personagem não encontrado ou você não tem permissão para visualizá-lo.**",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        (
            character_id,
            char_name,
            image_url,
            experience,
            level,
            points,
            rank,
            forca,
            resistencia,
            agilidade,
            sentidos,
            vitalidade,
            inteligencia,
            race_name,
            race_stage,
            race_stage_level,
            core_color,
            core_stage,
            reiryoku_base_pool,
            reiryoku_current,
            reiatsu_category,
            reiatsu_level,
        ) = row

        effective_forca = get_effective_attribute(character_id, "forca", forca)
        effective_resistencia = get_effective_attribute(character_id, "resistencia", resistencia)
        effective_agilidade = get_effective_attribute(character_id, "agilidade", agilidade)
        effective_sentidos = get_effective_attribute(character_id, "sentidos", sentidos)
        effective_vitalidade = get_effective_attribute(character_id, "vitalidade", vitalidade)
        effective_inteligencia = get_effective_attribute(character_id, "inteligencia", inteligencia)
        c.execute("SELECT main_class, sub_class1, sub_class2 FROM characters_classes WHERE character_id=?", (character_id,))
        classes = c.fetchone() or (None, None, None)
        main_class, sub_class1, sub_class2 = classes

        points_info = f"{points}" if points > 0 else "𝐍𝐎𝐍𝐄"
        race_info = f"{race_name or '𝐍𝐎𝐍𝐄'} • {race_stage or '𝐁𝐀𝐒𝐄'} ({race_stage_level or 0}%)"
        core_info = f"{core_color or 'Black'} Core • {core_stage or 'Dark Stage'} ({reiryoku_current or 0}/{reiryoku_base_pool or 0})"
        reiatsu_info = f"{reiatsu_category or '𝐍𝐎𝐍𝐄'} (Nv. {reiatsu_level or 0})"

        description = (
            f"``` 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍 ```- — ◇\n"
            f"> **__𝐍𝐀𝐌𝐄__**\n"
            f"● *{char_name}*\n"
            f"> **__𝐋𝐄𝐕𝐄𝐋__**\n"
            f"● *{level}*\n"
            f"> **__𝐄𝐗𝐏__**\n"
            f"○ *{experience}*\n"
            f"> **__𝐑𝐀𝐂𝐄__**\n"
            f"● *{race_info}*\n"
            f"> **__𝐑𝐄𝐈𝐀𝐓𝐒𝐔__**\n"
            f"○ *{reiatsu_info}*\n"
            f"> **__𝐂𝐎𝐑𝐄__**\n"
            f"● *{core_info}*\n"
            f"> **__𝐂𝐋𝐀𝐒𝐒__**\n"
            f"● *{main_class or '𝐍𝐎𝐍𝐄'}*\n"
            f"> **__𝐒𝐔𝐁𝐂𝐋𝐀𝐒𝐒__**\n"
            f"○ *{sub_class1 or '𝐍𝐎𝐍𝐄'}, {sub_class2 or '𝐍𝐎𝐍𝐄'}*\n\n"
            f"- — *[* **𝐏𝐎𝐈𝐍𝐓𝐒: ** ` {points_info} ` *]* —\n"
            f"● ○ ***[*** `𝐑𝐀𝐍𝐊 {rank}` ***]*** ○ ●"
        )

        embed = discord.Embed(title="``` 𝔻𝔼𝕿𝔸𝕴𝕷𝕾 ```", description=description, color=discord.Color.dark_grey())
        if image_url:
            embed.set_image(url=image_url)

        owner_id = interaction.user.id
        view = discord.ui.View()

        button_status = discord.ui.Button(label="𝐒𝐓𝐀𝐓𝐔𝐒", style=discord.ButtonStyle.secondary, custom_id=f"status_{interaction.user.id}")
        button_inventory = discord.ui.Button(label="𝐈𝐍𝐕𝐄𝐍𝐓𝐎𝐑𝐘", style=discord.ButtonStyle.secondary, custom_id=f"inventory_{interaction.user.id}")
        button_techniques = discord.ui.Button(label="𝐓𝐄𝐂𝐇𝐍𝐈𝐐𝐔𝐄𝐒", style=discord.ButtonStyle.secondary, custom_id=f"techniques_{interaction.user.id}")

        async def button_status_callback(interaction: discord.Interaction):
            if interaction.user.id != owner_id:
                await interaction.response.send_message("- > **Você não tem permissão.**", ephemeral=True)
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
                f"- ``` . . . ```"
            )

            status_embed = discord.Embed(title="𝕾𝖙𝖆𝖋𝖚𝖘", description=status_description, color=discord.Color.dark_grey())

            button_back = discord.ui.Button(label="𝐃𝐄𝐓𝐀𝐈𝐋𝐒", style=discord.ButtonStyle.secondary)

            async def button_back_callback(interaction: discord.Interaction):
                if interaction.user.id != owner_id:
                    await interaction.response.send_message("- > **Você não tem permissão.**", ephemeral=True)
                    return
                await interaction.response.edit_message(embed=embed, view=view)

            button_back.callback = button_back_callback
            back_view = discord.ui.View()
            back_view.add_item(button_back)

            await interaction.response.edit_message(embed=status_embed, view=back_view)

        async def button_inventory_callback(interaction: discord.Interaction):
            if interaction.user.id != owner_id:
                await interaction.response.send_message("- > **Você não tem permissão.**", ephemeral=True)
                return

            c.execute("SELECT item_name, description FROM inventory WHERE character_name COLLATE NOCASE=? AND user_id=?", (char_name, owner_id))
            items = c.fetchall()
            if not items:
                inventory_embed = discord.Embed(
                    title="**__```𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎 𝐕𝐀𝐙𝐈𝐎```__**",
                    description=f"- > **O inventário de {char_name} está vazio.**",
                    color=discord.Color.red(),
                )
                await interaction.response.edit_message(embed=inventory_embed, view=view)
                return

            capacity = get_inventory_capacity(rank)
            item_list = "\n".join([f"- {item[0]}: {item[1]}" for item in items])
            inventory_embed = discord.Embed(
                title=f"𝐈𝐧𝐯𝐞𝐧𝐭𝐚́𝐫𝐢𝐨 𝐝𝐞 {char_name}",
                description=f"{item_list}\n\n𝐂𝐚𝐩𝐚𝐜𝐢𝐝𝐚𝐝𝐞: {len(items)}/{capacity} itens",
                color=discord.Color.blue(),
            )
            await interaction.response.edit_message(embed=inventory_embed, view=view)

        async def button_techniques_callback(interaction: discord.Interaction):
            if interaction.user.id != owner_id:
                await interaction.response.send_message("- > **Você não tem permissão.**", ephemeral=True)
                return

            c.execute(
                "SELECT technique_name, description FROM techniques WHERE character_id=? ORDER BY technique_name COLLATE NOCASE",
                (character_id,),
            )
            techniques = c.fetchall()
            if not techniques:
                techniques_embed = discord.Embed(
                    title="**__```𝐓𝐄́𝐂𝐍𝐈𝐂𝐀𝐒 𝐕𝐀𝐙𝐈𝐀𝐒```__**",
                    description=f"- > **{char_name} não possui técnicas cadastradas.**",
                    color=discord.Color.red(),
                )
                await interaction.response.edit_message(embed=techniques_embed, view=view)
                return

            lines = [f"- **{tech_name}**: {tech_desc}" for tech_name, tech_desc in techniques[:15]]
            techniques_embed = discord.Embed(
                title=f"**__```𝐓𝐄́𝐂𝐍𝐈𝐂𝐀𝐒 𝐃𝐄 {char_name.upper()}```__**",
                description="\n".join(lines),
                color=discord.Color.blue(),
            )
            if len(techniques) > 15:
                techniques_embed.set_footer(text=f"Mostrando 15 de {len(techniques)} técnicas.")
            await interaction.response.edit_message(embed=techniques_embed, view=view)

        button_status.callback = button_status_callback
        button_inventory.callback = button_inventory_callback
        button_techniques.callback = button_techniques_callback

        view.add_item(button_status)
        view.add_item(button_inventory)
        view.add_item(button_techniques)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    register_register_slash_commands(bot)
