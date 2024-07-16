import discord
from discord.ext import commands
import sqlite3
import aiohttp
import random
import re

conn = sqlite3.connect('characters.db')
c = conn.cursor()

RANKS = {
    'F-': 1, 'F': 3, 'F+': 10, 'E-': 25, 'E': 50, 'E+': 75,
    'D-': 100, 'D': 150, 'D+': 200, 'C-': 250, 'C': 300, 'C+': 350,
    'B-': 400, 'B': 450, 'B+': 500, 'A-': 550, 'A': 600, 'A+': 650,
    'S': 700, 'S+': 750, 'SS': 800, 'SS+': 850, 'SSS': 900, 'SSS+': 950, 'Z': 1000
}

class Techniques(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = False

    async def send_embed(self, ctx, title, description, color=discord.Color.blue(), image_url=None):
        embed = discord.Embed(title=title, description=description, color=color)
        if image_url:
            embed.set_image(url=image_url)
        await ctx.send(embed=embed)

    def calculate_new_mastery(self, xp, mastery):
        xp_needed = 100 + (mastery * 20)
        if xp >= xp_needed:
            mastery += 1
            xp -= xp_needed
        return xp, mastery

    def get_xp_gain(self, mastery):
        if mastery < 50:
            return random.randint(1, 10)
        elif mastery < 100:
            return random.randint(1, 20)
        elif mastery < 200:
            return random.randint(1, 30)
        elif mastery < 300:
            return random.randint(1, 40)
        elif mastery < 400:
            return random.randint(1, 50)
        elif mastery < 500:
            return random.randint(1, 60)
        elif mastery < 600:
            return random.randint(1, 70)
        elif mastery < 700:
            return random.randint(1, 80)
        elif mastery < 800:
            return random.randint(1, 90)
        else:
            return random.randint(1, 100)

    def update_rank(self, mastery):
        for rank, mastery_required in RANKS.items():
            if mastery < mastery_required:
                return rank
        return 'Z'

    @commands.command(name='addtechnique')
    async def add_technique(self, ctx, character_name: str, technique_name: str):
        c.execute("SELECT 1 FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        if not c.fetchone():
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para adicionar técnicas a ele.**", discord.Color.red())
            return

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await self.send_embed(ctx, "𝐃𝐄𝐒𝐂𝐑𝐈𝐂̧𝐀̃𝐎 𝐃𝐀 𝐓𝐄́𝐂𝐍𝐈𝐂𝐀", "- > **Por favor, forneça a descrição da técnica.**")
        try:
            description_message = await self.bot.wait_for('message', check=check, timeout=60.0)
            description = description_message.content
            image_url = description_message.attachments[0].url if description_message.attachments else None

            c.execute("INSERT INTO techniques (character_name, technique_name, user_id, image_url, description) VALUES (?, ?, ?, ?, ?)",
                      (character_name, technique_name, ctx.author.id, image_url, description))
            conn.commit()
            await self.send_embed(ctx, "**__```𝐓𝐄́𝐂𝐍𝐈𝐂𝐀 𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐃𝐀```__**", f"- > **Técnica** **__`{technique_name}`__** **adicionada ao personagem** **__`{character_name}`__**.", discord.Color.green(), image_url)
        except asyncio.TimeoutError:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Tempo esgotado. Por favor, tente novamente.**", discord.Color.red())

    @commands.command(name='removetechnique')
    async def remove_technique(self, ctx, character_name: str, technique_name: str):
        c.execute("DELETE FROM techniques WHERE character_name COLLATE NOCASE=? AND technique_name COLLATE NOCASE=? AND user_id=?", 
                  (character_name, technique_name, ctx.author.id))
        if c.rowcount == 0:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada ou você não tem permissão para removê-la.**", discord.Color.red())
        else:
            conn.commit()
            await self.send_embed(ctx, "**__```𝐓𝐄́𝐂𝐍𝐈𝐂𝐀 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐀```__**", f"- > **Técnica** **__`{technique_name}`__** **removida do personagem** **__`{character_name}`__**.", discord.Color.green())

    @commands.command(name='showtechnique')
    async def show_technique(self, ctx, character_name: str, technique_name: str):
        c.execute("SELECT technique_name, description, image_url, xp, mastery FROM techniques WHERE character_name COLLATE NOCASE=? AND technique_name COLLATE NOCASE=? AND user_id=?", 
                  (character_name, technique_name, ctx.author.id))
        technique = c.fetchone()
        if not technique:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada ou você não tem permissão para visualizá-la.**", discord.Color.red())
        else:
            technique_name, description, image_url, xp, mastery = technique
            xp_needed = 100 + (mastery * 20)
            xp_percentage = (xp / xp_needed) * 100

            description += (
                f"\n\n**𝐌𝐀𝐒𝐓𝐄𝐑𝐘:** {mastery}/600"
                f"\n**𝐄𝐗𝐏:** {xp}/{xp_needed} ({xp_percentage:.2f}%)"
            )
            await self.send_embed(ctx, technique_name, description, discord.Color.blue(), image_url)

    @commands.has_permissions(administrator=True)
    @commands.command(name='activate')
    async def activate(self, ctx):
        self.active = not self.active
        status = "𝐀𝐓𝐈𝐕𝐀𝐃𝐎" if self.active else "𝐃𝐄𝐒𝐀𝐓𝐈𝐕𝐀𝐃𝐎"
        await ctx.send(f"- > **A funcionalidade de leitura de webhooks está agora** **__`{status}`__**.")

    async def process_webhook(self, data, user):
        message_content = data.get("content", "")
        character_name = data.get("author", {}).get("name")
        if not character_name:
            return None

        c.execute("SELECT technique_name, xp, mastery, usage_count FROM techniques WHERE character_name COLLATE NOCASE=?", (character_name,))
        techniques = c.fetchall()

        for technique_name, xp, mastery, usage_count in techniques:
            if f"**{technique_name.lower()}**" in message_content.lower():
                usage_count += 1
                if random.random() < 0.5:
                    new_xp = xp + self.get_xp_gain(mastery)
                    new_xp, mastery = self.calculate_new_mastery(new_xp, mastery)
                    new_rank = self.update_rank(mastery)
                    c.execute("UPDATE techniques SET xp=?, mastery=?, usage_count=? WHERE character_name COLLATE NOCASE=? AND technique_name COLLATE NOCASE=?",
                              (new_xp, mastery, usage_count, character_name, technique_name))
                    conn.commit()
                    await user.send(f"- > **Técnica** **__`{technique_name}`__** **usada!** **__`{character_name}`__** **ganhou XP. Mastery agora é** **__`{mastery}`__**, **Rank agora é** **__`{new_rank}`__**.")
                else:
                    c.execute("UPDATE techniques SET usage_count=? WHERE character_name COLLATE NOCASE=? AND technique_name COLLATE NOCASE=?",
                              (usage_count, character_name, technique_name))
                    conn.commit()
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        c.execute("SELECT name, prefix, image_url FROM characters WHERE user_id=?", (message.author.id,))
        characters = c.fetchall()

        for name, prefix, image_url in characters:
            if message.content.startswith(prefix):
                new_message_content = message.content[len(prefix):].strip()
                if not new_message_content and not message.attachments:
                    await message.channel.send('- > **Não pode enviar uma mensagem vazia.**')
                    return

                reference = message.reference
                reply_header = ""
                if reference and isinstance(reference.resolved, discord.Message):
                    referenced_message = reference.resolved
                    link = f"https://discord.com/channels/{referenced_message.guild.id}/{referenced_message.channel.id}/{referenced_message.id}"
                    original_author_mention = referenced_message.author.mention
                    if referenced_message.webhook_id:
                        c.execute("SELECT user_id FROM characters WHERE name=?", (referenced_message.author.name,))
                        original_author_id = c.fetchone()
                        if original_author_id:
                            original_author = await self.bot.fetch_user(original_author_id[0])
                            original_author_mention += f" ({original_author.mention})"

                    raw_content = referenced_message.clean_content.split("\n")
                    raw_content = [line for line in raw_content if not line.strip().startswith(">")]
                    raw_content = "\n".join(raw_content)
                    truncated_content = raw_content[:100] + "..." if len(raw_content) > 100 else raw_content
                    reply_header = f"> [𝐑𝐄𝐏𝐋𝐘 𝐓𝐎]({link}): {original_author_mention}\n> {truncated_content}\n"

                reply_content = f"{reply_header}{new_message_content}"

                async with aiohttp.ClientSession() as session:
                    if isinstance(message.channel, discord.Thread):
                        parent_channel = message.channel.parent
                    else:
                        parent_channel = message.channel

                    webhook_name = "KillyanHook"
                    webhooks = await parent_channel.webhooks()
                    webhook = next((hook for hook in webhooks if hook.name == webhook_name), None)
                    if webhook is None:
                        webhook = await parent_channel.create_webhook(name=webhook_name)

                    if isinstance(message.channel, discord.Thread):
                        await webhook.send(
                            content=reply_content,
                            username=name,
                            avatar_url=image_url,
                            allowed_mentions=discord.AllowedMentions(users=True),
                            suppress_embeds=True,
                            files=[await attachment.to_file() for attachment in message.attachments],
                            thread=message.channel
                        )
                    else:
                        await webhook.send(
                            content=reply_content,
                            username=name,
                            avatar_url=image_url,
                            allowed_mentions=discord.AllowedMentions(users=True),
                            suppress_embeds=True,
                            files=[await attachment.to_file() for attachment in message.attachments]
                        )

                    webhook_url = webhook.url
                    c.execute("UPDATE characters SET webhook_url=? WHERE name COLLATE NOCASE=? AND user_id=?", (webhook_url, name, message.author.id))
                    conn.commit()

                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass

                c.execute("UPDATE characters SET message_count = message_count + 1 WHERE name COLLATE NOCASE=? AND user_id=?", (name, message.author.id))
                conn.commit()

                if self.active:
                    data = {
                        "content": new_message_content,
                        "author": {"name": name}
                    }
                    user = await self.bot.fetch_user(message.author.id)
                    await self.process_webhook(data, user)
                return

async def setup(bot):
    await bot.add_cog(Techniques(bot))
