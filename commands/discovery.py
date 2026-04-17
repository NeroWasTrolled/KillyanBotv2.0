import math

import discord
from discord.ext import commands
from discord.ui import Button, View

from database.connection import create_connection
from utils.common import send_embed

conn = create_connection()
c = conn.cursor()


def register_discovery_commands(bot):
    @bot.command(name='showrankings', aliases=['ranking', 'top10'])
    async def show_rankings(ctx):
        c.execute(
            """
            SELECT c.name, p.level
            FROM characters c
            JOIN character_progression p ON c.character_id = p.character_id
            ORDER BY p.level DESC
            LIMIT 10
            """
        )
        rankings = c.fetchall()

        if not rankings:
            await send_embed(ctx, "**__𝐄𝐑𝐑𝐎__**", "- > **Nenhum ranking encontrado no momento.**", discord.Color.red())
            return

        ranking_message = "\n".join([f"**{i+1}.** __{rank[0]}__ - Nível: **{rank[1]}**" for i, rank in enumerate(rankings)])

        title = "**__𝐓𝐎𝐏 𝟏𝟎 𝐉𝐎𝐆𝐀𝐃𝐎𝐑𝐄𝐒__**"
        description = f"- > **Aqui estão os 10 melhores jogadores por nível:**\n\n{ranking_message}"

        await send_embed(ctx, title, description, discord.Color.blue())

    @bot.command(name='find', aliases=['buscar'])
    async def find(ctx, *, name: str):
        per_page = 10
        c.execute(
            """
            SELECT c.character_id, c.name, c.user_id, c.image_url,
                   p.message_count, COALESCE(c.registered_at, p.created_at)
            FROM characters c
            LEFT JOIN character_progression p ON c.character_id = p.character_id
            WHERE c.name LIKE ?
            """,
            (f'%{name}%',),
        )
        results = c.fetchall()
        filtered_results = [
            result for result in results
            if not c.execute("SELECT private FROM characters WHERE user_id=? LIMIT 1", (result[2],)).fetchone()[0]
            or ctx.author.id == result[2]
        ]
        total_results = len(filtered_results)
        total_pages = math.ceil(total_results / per_page)
        if total_results == 0:
            await ctx.send(f'- > **Nenhum personagem encontrado com o nome __"{name}"__.**')
            return
        current_page = 1

        async def update_message(interaction, page):
            if page < 1:
                page = total_pages
            elif page > total_pages:
                page = 1
            embed = await create_results_embed(filtered_results, page, per_page, total_pages, ctx)
            await interaction.response.edit_message(embed=embed, view=create_view(page))

        def create_view(page):
            view = View()
            buttons = [("<<", 1), ("<", page - 1), (">", page + 1), (">>", total_pages)]
            for label, target_page in buttons:
                button = Button(label=label, style=discord.ButtonStyle.primary)
                button.callback = lambda interaction, tp=target_page: update_message(interaction, tp)
                view.add_item(button)
            return view

        embed = await create_results_embed(filtered_results, current_page, per_page, total_pages, ctx)
        await ctx.send(embed=embed, view=create_view(current_page))

    @bot.command(name='private', aliases=['privado'])
    async def private(ctx):
        user_id = ctx.author.id
        c.execute("SELECT private FROM characters WHERE user_id=?", (user_id,))
        private_status = c.fetchone()
        if private_status:
            new_status = 1 - private_status[0]
            c.execute("UPDATE characters SET private=? WHERE user_id=?", (new_status, user_id))
            conn.commit()
            status_text = "𝐏𝐑𝐈𝐕𝐀𝐃𝐎𝐒" if new_status == 1 else "𝐏𝐔́𝐁𝐋𝐈𝐂𝐎𝐒"
            await ctx.send(f'- > **Seus personagens agora estão __{status_text}__.**')
        else:
            await ctx.send(f'- > **__𝐒𝐄𝐌 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐍𝐒 𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐃𝐎𝐒__**')

    async def create_results_embed(results, page, per_page, total_pages, ctx):
        start = (page - 1) * per_page
        end = start + per_page
        embed = discord.Embed(title="**__```𝐑𝐄𝐒𝐔𝐋𝐓𝐀𝐃𝐎𝐒```__**", color=discord.Color.dark_grey())
        result_list = []
        for character_id, name, user_id, image_url, message_count, registered_at in results[start:end]:
            user_display_name = f"𝐔𝐒𝐄𝐑 𝐈𝐃: {user_id}"
            user = bot.get_user(user_id) or await bot.fetch_user(user_id)
            if user:
                user_display_name = user.name
            avatar_link = image_url if image_url else "𝐍𝐎 𝐀𝐕𝐀𝐓𝐀𝐑"
            result = (
                f"**{name}**\n"
                f"𝐔𝐒𝐄𝐑: {user_display_name}\n"
                f"[𝐀𝐕𝐀𝐓𝐀𝐑]({avatar_link})\n"
                f"𝐌𝐄𝐒𝐒𝐀𝐆𝐄𝐒 𝐒𝐄𝐍𝐓: {message_count}\n"
                f"𝐑𝐄𝐆𝐈𝐒𝐓𝐄𝐑𝐄𝐃: {registered_at}\n"
            )
            result_list.append(result)

        embed.description = "\n".join(result_list)
        embed.set_footer(text=f"Page {page} of {total_pages}")
        return embed


async def setup(bot):
    register_discovery_commands(bot)
