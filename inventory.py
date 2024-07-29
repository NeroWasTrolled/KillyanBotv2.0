import sqlite3
from discord.ext import commands
import discord
import asyncio

conn = sqlite3.connect('characters.db')
c = conn.cursor()

def create_inventory_table():
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_name TEXT COLLATE NOCASE,
            item_name TEXT COLLATE NOCASE,
            description TEXT,
            image_url TEXT,
            user_id INTEGER,
            message_id INTEGER
        )
    ''')
    conn.commit()

    try:
        c.execute('ALTER TABLE inventory ADD COLUMN message_id INTEGER')
        conn.commit()
    except sqlite3.OperationalError:
        pass 

create_inventory_table()

def get_inventory_capacity(rank):
    rank_capacities = {
        'F-': 4, 'F': 8, 'F+': 12, 'E-': 16, 'E': 20, 'E+': 24,
        'D-': 28, 'D': 32, 'D+': 36, 'C-': 40, 'C': 44, 'C+': 48,
        'B-': 52, 'B': 56, 'B+': 60, 'A-': 64, 'A': 68, 'A+': 72,
        'S': 76, 'S+': 80, 'SS': 84, 'SS+': 88, 'SSS': 92, 'SSS+': 96,
        'Z': 100
    }
    return rank_capacities.get(rank, 4)

async def send_embed(ctx, title, description, color=discord.Color.blue(), image_url=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if image_url:
        embed.set_image(url=image_url)
    await ctx.send(embed=embed)

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='additem')
    async def additem(self, ctx, character_name: str, *, item_name: str):
        c.execute("SELECT rank FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Personagem** **__`{character_name}`__** **não encontrado ou você não tem permissão para adicionar itens.**", discord.Color.red())
            return

        rank = character[0]
        capacity = get_inventory_capacity(rank)

        c.execute("SELECT COUNT(*) FROM inventory WHERE character_name COLLATE NOCASE=?", (character_name,))
        item_count = c.fetchone()[0]

        if item_count >= capacity:
            await send_embed(ctx, "**__```𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎 𝐂𝐇𝐄𝐈𝐎```__**", f"- > **Inventário de** **__`{character_name}`__** **está cheio. Capacidade máxima: `{capacity}` itens.**", discord.Color.red())
            return

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await send_embed(ctx, "**__```𝐃𝐄𝐒𝐂𝐑𝐈𝐂̧𝐀̃𝐎 𝐃𝐎 𝐈𝐓𝐄𝐌```__**", "- > **Por favor, forneça a descrição do item.**")
        try:
            description_message = await self.bot.wait_for('message', check=check, timeout=60.0)
            description = description_message.content

            image_url = description_message.attachments[0].url if description_message.attachments else None
            message_id = description_message.id if description_message.attachments else None

            c.execute("INSERT INTO inventory (character_name, item_name, description, image_url, user_id, message_id) VALUES (?, ?, ?, ?, ?, ?)",
                      (character_name, item_name, description, image_url, ctx.author.id, message_id))
            conn.commit()
            await send_embed(ctx, "**__```𝐈𝐓𝐄𝐌 𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐃𝐎```__**", f"- > **Item** **__`{item_name}`__** **adicionado ao inventário de** **__`{character_name}`__**.", discord.Color.green(), image_url)
        except asyncio.TimeoutError:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Tempo esgotado. Por favor, tente novamente.**", discord.Color.red())

    @commands.command(name='removeitem')
    async def removeitem(self, ctx, character_name: str, *, item_name: str):
        c.execute("SELECT id FROM inventory WHERE character_name COLLATE NOCASE=? AND item_name COLLATE NOCASE=? AND user_id=?", (character_name, item_name, ctx.author.id))
        item = c.fetchone()
        if not item:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Item** **__`{item_name}`__** **não encontrado no inventário de** **__`{character_name}`__**.", discord.Color.red())
            return

        c.execute("DELETE FROM inventory WHERE id=?", (item[0],))
        conn.commit()
        await send_embed(ctx, "**__```𝐈𝐓𝐄𝐌 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐎```__**", f"- > **Item** **__`{item_name}`__** **removido do inventário de** **__`{character_name}`__**.", discord.Color.green())

    @commands.command(name='inventory')
    async def inventory(self, ctx, character_name: str):
        c.execute("SELECT item_name FROM inventory WHERE character_name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        items = c.fetchall()
        if not items:
            await send_embed(ctx, "**__```𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎 𝐕𝐀𝐙𝐈𝐎```__**", f"- > **Inventário de** **__`{character_name}`__** **está vazio.**", discord.Color.red())
            return

        item_list = "\n".join([f"- {item[0]}" for item in items])
        c.execute("SELECT rank FROM characters WHERE name COLLATE NOCASE=?", (character_name,))
        rank = c.fetchone()[0]
        capacity = get_inventory_capacity(rank)
        embed = discord.Embed(
            title=f"**__```𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎 𝐃𝐄 {character_name}```__**",
            description=f"{item_list}\n\n**Capacidade:** `{len(items)}/{capacity}` itens",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name='itemdetails')
    async def itemdetails(self, ctx, character_name: str, *, item_name: str):
        c.execute("SELECT item_name, description, image_url, message_id FROM inventory WHERE character_name COLLATE NOCASE=? AND item_name COLLATE NOCASE=? AND user_id=?", (character_name, item_name, ctx.author.id))
        item = c.fetchone()
        if not item:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Item** **__`{item_name}`__** **não encontrado no inventário de** **__`{character_name}`__**.", discord.Color.red())
            return

        item_name, description, image_url, message_id = item
        if image_url:
            try:
                original_message = await ctx.channel.fetch_message(message_id)
                if not original_message:
                    image_url = None
            except discord.errors.NotFound:
                image_url = None

        await send_embed(ctx, f"**__```𝐃𝐄𝐓𝐀𝐋𝐇𝐄𝐒 𝐃𝐎 𝐈𝐓𝐄𝐌```__**", f"- > **Item:** **__`{item_name}`__**\n- > **Descrição:** **{description}**", discord.Color.blue(), image_url)

    @commands.command(name='pfpitem')
    async def pfpitem(self, ctx, character_name: str, *, item_name: str):
        c.execute("SELECT id FROM inventory WHERE character_name COLLATE NOCASE=? AND item_name COLLATE NOCASE=? AND user_id=?", (character_name, item_name, ctx.author.id))
        item = c.fetchone()
        if not item:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Item** **__`{item_name}`__** **não encontrado no inventário de** **__`{character_name}`__**.", discord.Color.red())
            return

        if ctx.message.attachments:
            image_url = ctx.message.attachments[0].url
            message_id = ctx.message.id
            c.execute("UPDATE inventory SET image_url=?, message_id=? WHERE id=?", (image_url, message_id, item[0]))
            conn.commit()
            await send_embed(ctx, "**__```𝐈𝐌𝐀𝐆𝐄𝐌 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐀```__**", f"- > **Imagem do item** **__`{item_name}`__** **atualizada com sucesso para** **__`{character_name}`__**.", discord.Color.green(), image_url)
        else:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Por favor, anexe uma imagem ao usar este comando para definir o avatar do item.**", discord.Color.red())

async def setup(bot):
    await bot.add_cog(Inventory(bot))
