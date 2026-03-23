import sqlite3
from discord.ext import commands
from logs import Logs
import discord
import asyncio
import re

conn = sqlite3.connect('characters.db')
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")

def sanitize_input(input_str):
    if not re.match(r"^[a-zA-Z0-9\s]*$", input_str):
        return False
    return True

def apply_layout(user_id, title, description):
    c.execute("SELECT title_layout, description_layout FROM layout_settings WHERE user_id=?", (user_id,))
    layout = c.fetchone()

    if layout:
        title_layout, description_layout = layout
    else:
        title_layout = "**╚╡ ⬥ {title} ⬥ ╞**"
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

def get_inventory_capacity(rank):
    rank_capacities = {
        'F-': 4, 'F': 8, 'F+': 12, 'E-': 16, 'E': 20, 'E+': 24,
        'D-': 28, 'D': 32, 'D+': 36, 'C-': 40, 'C': 44, 'C+': 48,
        'B-': 52, 'B': 56, 'B+': 60, 'A-': 64, 'A': 68, 'A+': 72,
        'S': 76, 'S+': 80, 'SS': 84, 'SS+': 88, 'SSS': 92, 'SSS+': 96,
        'Z': 100
    }
    return rank_capacities.get(rank, 4)

async def send_embed(ctx, title, description, color=discord.Color.blue(), image_url=None, next_step=None):
    if next_step:
        description = f"{description}\n\n- > **Próximo passo:** {next_step}"
    embed = discord.Embed(title=title, description=description, color=color)
    if image_url:
        embed.set_image(url=image_url)
    await ctx.send(embed=embed)

def parse_command_args(args):
    pattern = r"'(.*?)'|(\S+)"
    matches = re.findall(pattern, args)
    return [match[0] if match[0] else match[1] for match in matches]

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def validate_inputs(self, character_name, item_name):
        if not character_name or not item_name:
            return False, "- > **Nome de personagem e item são obrigatórios.**"
        return True, None

    @commands.command(name='additem', aliases=['addi', 'itemadd'])
    async def additem(self, ctx, *, args: str):
        args = parse_command_args(args)
        if len(args) < 2:
            await send_embed(ctx, "**__```𝐅𝐎𝐑𝐌𝐀𝐓𝐎 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐎```__**", "- > **Uso correto: kill!additem 'Nome do Personagem' 'Nome do Item'**", discord.Color.red())
            return

        character_name, item_name = args[0], ' '.join(args[1:])
        valid, error_msg = self.validate_inputs(character_name, item_name)
        if not valid:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", error_msg, discord.Color.red())
            return

        c.execute("SELECT rank FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f'- > **Personagem {character_name} não encontrado.**', discord.Color.red())
            return

        rank = character[0]
        capacity = get_inventory_capacity(rank)

        c.execute("SELECT COUNT(*) FROM inventory WHERE character_name COLLATE NOCASE=?", (character_name,))
        item_count = c.fetchone()[0]

        if item_count >= capacity:
            await send_embed(ctx, "**__```𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎 𝐂𝐇𝐄𝐈𝐎```__**", f'- > **O inventário de {character_name} está cheio. Capacidade máxima: {capacity} itens.**', discord.Color.red())
            return

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await send_embed(ctx, "**__```𝐃𝐄𝐒𝐂𝐑𝐈𝐂̧𝐀̃𝐎 𝐃𝐄 𝐈𝐓𝐄𝐌```__**", "- > **Forneça a descrição do item.**", discord.Color.blue())
        try:
            description_message = await self.bot.wait_for('message', check=check, timeout=60.0)
            description = description_message.content
            image_url = description_message.attachments[0].url if description_message.attachments else None

            c.execute("INSERT INTO inventory (character_name, item_name, description, image_url, user_id) VALUES (?, ?, ?, ?, ?)",
                      (character_name, item_name, description, image_url, ctx.author.id))
            conn.commit()

            await send_embed(
                ctx,
                "**__```𝐈𝐓𝐄𝐌 𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐃𝐎```__**",
                f"- > **Item {item_name} foi adicionado ao inventário de {character_name}.**",
                discord.Color.green(),
                image_url,
                "use `kill!inv NomeDoPersonagem` para revisar"
            )
        except asyncio.TimeoutError:
            await send_embed(ctx, "**__```𝐓𝐄𝐌𝐏𝐎 𝐄𝐒𝐆𝐎𝐓𝐀𝐃𝐎```__**", "- > **Tente novamente.**", discord.Color.red())

    @commands.command(name='delitem', aliases=['deli', 'itemdel'])
    async def delitem(self, ctx, *, args: str):
        args = parse_command_args(args)
        if len(args) < 2:
            await send_embed(ctx, "**__```𝐅𝐎𝐑𝐌𝐀𝐓𝐎 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐎```__**", "- > **Uso correto: kill!delitem 'Nome do Personagem' 'Nome do Item'**", discord.Color.red())
            return

        character_name, item_name = args[0], ' '.join(args[1:])
        valid, error_msg = self.validate_inputs(character_name, item_name)
        if not valid:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", error_msg, discord.Color.red())
            return

        c.execute("SELECT id FROM inventory WHERE character_name COLLATE NOCASE=? AND item_name COLLATE NOCASE=? AND user_id=?", (character_name, item_name, ctx.author.id))
        item = c.fetchone()
        if not item:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Item {item_name} não encontrado no inventário de {character_name}.**", discord.Color.red())
            return

        c.execute("DELETE FROM inventory WHERE id=?", (item[0],))
        conn.commit()

        await send_embed(ctx, "**__```𝐈𝐓𝐄𝐌 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐎```__**", f"- > **Item {item_name} foi removido do inventário de {character_name}.**", discord.Color.green(), next_step="use `kill!inv NomeDoPersonagem` para revisar")

    @commands.command(name='inv', aliases=['bag', 'inventario'])
    async def inv(self, ctx, *, args: str):
        args = parse_command_args(args)
        if len(args) < 1:
            await send_embed(ctx, "**__```𝐅𝐎𝐑𝐌𝐀𝐓𝐎 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐎```__**", "- > **Uso correto: kill!inv 'Nome do Personagem'**", discord.Color.red())
            return

        character_name = args[0]

        c.execute("SELECT item_name, description FROM inventory WHERE character_name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        items = c.fetchall()
        if not items:
            await send_embed(ctx, "**__```𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎 𝐕𝐀𝐙𝐈𝐎```__**", f"- > **O inventário de {character_name} está vazio.**", discord.Color.red())
            return

        item_list = "\n".join([f"- {item[0]}: {item[1]}" for item in items])
        c.execute("SELECT rank FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character_rank = c.fetchone()
        if not character_rank:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Personagem {character_name} não encontrado.**", discord.Color.red())
            return

        rank = character_rank[0]
        capacity = get_inventory_capacity(rank)

        formatted_name = to_bold_sans_serif(character_name)
        embed = discord.Embed(
            title=f"𝐈𝐧𝐯𝐞𝐧𝐭𝐚́𝐫𝐢𝐨 𝐝𝐞 {formatted_name}",
            description=f"{item_list}\n\n𝐂𝐚𝐩𝐚𝐜𝐢𝐝𝐚𝐝𝐞: {len(items)}/{capacity} itens",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name='showitem', aliases=['item'])
    async def show_item(self, ctx, *, args: str):
        """Comando para exibir um item do inventário"""
        parsed_args = parse_command_args(args)
        if len(parsed_args) < 2:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso correto: kill!showitem 'Nome do Personagem' 'Nome do Item'**", discord.Color.red())
            return

        character_name, item_name = parsed_args[0], ' '.join(parsed_args[1:])
        valid, error_msg = self.validate_inputs(character_name, item_name)
        if not valid:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", error_msg, discord.Color.red())
            return

        c.execute("SELECT item_name, description, image_url FROM inventory WHERE character_name COLLATE NOCASE=? AND item_name COLLATE NOCASE=? AND user_id=?", (character_name, item_name, ctx.author.id))
        item = c.fetchone()
        if not item:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Item {item_name} não encontrado no inventário de {character_name}.**", discord.Color.red())
            return

        item_name, description, image_url = item

        formatted_title, formatted_description = apply_layout(ctx.author.id, item_name, description)

        await send_embed(ctx, formatted_title, formatted_description, discord.Color.blue(), image_url)

    @commands.command(name='consumeitem', aliases=['useitem', 'usaritem'])
    async def consumeitem(self, ctx, *, args: str):
        args = parse_command_args(args)
        if len(args) < 2:
            await send_embed(ctx, "**__```𝐅𝐎𝐑𝐌𝐀𝐓𝐎 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐎```__**", "- > **Uso correto: kill!consumeitem 'Nome do Personagem' 'Nome do Item'**", discord.Color.red())
            return

        character_name, item_name = args[0], ' '.join(args[1:])
        valid, error_msg = self.validate_inputs(character_name, item_name)
        if not valid:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", error_msg, discord.Color.red())
            return

        c.execute("SELECT id, description FROM inventory WHERE character_name COLLATE NOCASE=? AND item_name COLLATE NOCASE=? AND user_id=?", (character_name, item_name, ctx.author.id))
        item = c.fetchone()
        if not item:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Item {item_name} não encontrado no inventário de {character_name}.**", discord.Color.red())
            return

        item_id, description = item

        await send_embed(ctx, "**__```𝐈𝐓𝐄𝐌 𝐂𝐎𝐍𝐒𝐔𝐌𝐈𝐃𝐎```__**", f"- > **Item {item_name} consumido!** \n**__𝐃𝐄𝐒𝐂𝐑𝐈𝐂̧𝐀̃𝐎__: {description}.**", discord.Color.green(), next_step="use `kill!inv NomeDoPersonagem` para ver saldo")

        c.execute("DELETE FROM inventory WHERE id=?", (item_id,))
        conn.commit()

    @commands.command(name='pfpitem', aliases=['itemimg'])
    async def pfpitem(self, ctx, *, args: str):
        args = parse_command_args(args)
        if len(args) < 2:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso correto: `kill!pfpitem [nome personagem] [nome item]`**", discord.Color.red())
            return

        character_name, item_name = args[0], ' '.join(args[1:])

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
