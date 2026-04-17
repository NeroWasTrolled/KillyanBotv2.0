import discord

from database.connection import create_connection

conn = create_connection()
c = conn.cursor()


def register_layout_commands(bot):
    @bot.command(name='settitle', aliases=['titlelayout'])
    async def set_title_layout(ctx, *, layout: str):
        user_id = ctx.author.id
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
        await ctx.send(f"- > **Layout de título atualizado para:**\n{layout}")

    @bot.command(name='setdesc', aliases=['desclayout'])
    async def set_description_layout(ctx, *, layout: str):
        user_id = ctx.author.id
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
        await ctx.send(f"- > **Layout de descrição atualizado para:**\n{layout}")


async def setup(bot):
    register_layout_commands(bot)
