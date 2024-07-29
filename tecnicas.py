import discord
from discord.ext import commands
import sqlite3
import aiohttp
import asyncio
import random

conn = sqlite3.connect('characters.db')
c = conn.cursor()

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
        while xp >= xp_needed:
            mastery += 1
            xp -= xp_needed
            xp_needed = 100 + (mastery * 20)
        return xp, mastery

    def get_xp_gain(self, mastery):
        return random.randint(1, max(10, (mastery // 10) + 1))

    def update_rank(self, mastery):
        RANKS = {
            'F-': 0, 'F': 10, 'E-': 20, 'E': 40, 'D-': 80, 'D': 160, 'C-': 320, 'C': 640,
            'B-': 1280, 'B': 2560, 'A-': 5120, 'A': 10240, 'S-': 20480, 'S': 40960
        }
        for rank, mastery_required in sorted(RANKS.items(), key=lambda item: item[1]):
            if mastery < mastery_required:
                return rank
        return 'Z'

    @commands.command(name='addtechnique')
    async def add_technique(self, ctx, character_name: str, technique_name: str):
        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__Erro__**", "- > **Personagem não encontrado ou você não tem permissão para adicionar técnicas a ele.**", discord.Color.red())
            return

        character_id = character[0]

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await self.send_embed(ctx, "Descrição da Técnica", "- > **Por favor, forneça a descrição da técnica.**")
        try:
            description_message = await self.bot.wait_for('message', check=check, timeout=60.0)
            description = description_message.content
            image_url = description_message.attachments[0].url if description_message.attachments else None

            c.execute("INSERT INTO techniques (character_id, technique_name, user_id, image_url, description) VALUES (?, ?, ?, ?, ?)",
                      (character_id, technique_name, ctx.author.id, image_url, description))
            conn.commit()
            await self.send_embed(ctx, "**__Técnica Adicionada__**", f"- > **Técnica** **__`{technique_name}`__** **adicionada ao personagem** **__`{character_name}`__**.", discord.Color.green(), image_url)
        except asyncio.TimeoutError:
            await self.send_embed(ctx, "**__Erro__**", "- > **Tempo esgotado. Por favor, tente novamente.**", discord.Color.red())

    @commands.command(name='removetechnique')
    async def remove_technique(self, ctx, character_name: str, technique_name: str):
        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__Erro__**", "- > **Personagem não encontrado ou você não tem permissão para remover técnicas dele.**", discord.Color.red())
            return

        character_id = character[0]
        c.execute("DELETE FROM techniques WHERE character_id=? AND technique_name COLLATE NOCASE=?", 
                  (character_id, technique_name))
        if c.rowcount == 0:
            await self.send_embed(ctx, "**__Erro__**", "- > **Técnica não encontrada ou você não tem permissão para removê-la.**", discord.Color.red())
        else:
            conn.commit()
            await self.send_embed(ctx, "**__Técnica Removida__**", f"- > **Técnica** **__`{technique_name}`__** **removida do personagem** **__`{character_name}`__**.", discord.Color.green())

    @commands.command(name='showtechnique')
    async def show_technique(self, ctx, character_name: str, technique_name: str):
        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__Erro__**", "- > **Personagem não encontrado ou você não tem permissão para visualizar técnicas dele.**", discord.Color.red())
            return

        character_id = character[0]
        c.execute("SELECT technique_name, description, image_url, xp, mastery FROM techniques WHERE character_id=? AND technique_name COLLATE NOCASE=?", 
                  (character_id, technique_name))
        technique = c.fetchone()
        if not technique:
            await self.send_embed(ctx, "**__Erro__**", "- > **Técnica não encontrada ou você não tem permissão para visualizá-la.**", discord.Color.red())
        else:
            technique_name, description, image_url, xp, mastery = technique
            xp_needed = 100 + (mastery * 20)
            xp_percentage = (xp / xp_needed) * 100

            description += (
                f"\n\n**MASTERY:** {mastery}/600"
                f"\n**EXP:** {xp}/{xp_needed} ({xp_percentage:.2f}%)"
            )
            await self.send_embed(ctx, technique_name, description, discord.Color.blue(), image_url)

    @commands.command(name='activate')
    async def activate(self, ctx):
        self.active = not self.active
        status = "ATIVADO" if self.active else "DESATIVADO"
        await ctx.send(f"- > **A funcionalidade de leitura de webhooks está agora** **__`{status}`__**.")

    async def process_webhook(self, data, user):
        message_content = data.get("content", "")
        character_id = data.get("author", {}).get("id")
        if not character_id:
            return None

        c.execute("SELECT technique_name, xp, mastery, usage_count FROM techniques WHERE character_id=?", (character_id,))
        techniques = c.fetchall()

        for technique_name, xp, mastery, usage_count in techniques:
            if f"**{technique_name.lower()}**" in message_content.lower():
                usage_count += 1
                if random.random() < 0.5:
                    new_xp = xp + self.get_xp_gain(mastery)
                    new_xp, mastery = self.calculate_new_mastery(new_xp, mastery)
                    new_rank = self.update_rank(mastery)
                    c.execute("UPDATE techniques SET xp=?, mastery=?, usage_count=? WHERE character_id=? AND technique_name COLLATE NOCASE=?",
                              (new_xp, mastery, usage_count, character_id, technique_name))
                    conn.commit()
                    await user.send(f"- > **Técnica** **__`{technique_name}`__** **usada!** **__`{character_id}`__** **ganhou XP. Mastery agora é** **__`{mastery}`__**, **Rank agora é** **__`{new_rank}`__**.")
                else:
                    c.execute("UPDATE techniques SET usage_count=? WHERE character_id=? AND technique_name COLLATE NOCASE=?",
                              (usage_count, character_id, technique_name))
                    conn.commit()
        return None

    async def get_reply_header(self, reference):
        if reference and isinstance(reference.resolved, discord.Message):
            referenced_message = reference.resolved
            link = f"https://discord.com/channels/{referenced_message.guild.id}/{referenced_message.channel.id}/{referenced_message.id}"
            character_name = referenced_message.author.name
            webhook_id = referenced_message.webhook_id

            if webhook_id:
                c.execute("SELECT character_id, user_id FROM characters WHERE name=? AND webhook_url LIKE ?", (character_name, f"%{webhook_id}%"))
                character_data = c.fetchone()

                if character_data:
                    character_id, original_author_id = character_data
                    original_author = await self.bot.fetch_user(original_author_id)
                    user_mention = original_author.mention if original_author else f"<@{original_author_id}>"
                else:
                    user_mention = f"<@{referenced_message.author.id}>"
            else:
                user_mention = f"<@{referenced_message.author.id}>"

            raw_content = referenced_message.clean_content.split("\n")
            raw_content = [line for line in raw_content if not line.strip().startswith(">")]
            truncated_content = " ".join(raw_content)
            if len(truncated_content) > 100:
                truncated_content = truncated_content[:100] + "..."

            return f"> ▪ [𝐑𝐄𝐏𝐋𝐘 𝐓𝐎]({link}): @{character_name} 〔{user_mention}〕▪\n> ⤷『 {truncated_content} 』•"

        return ""

    async def handle_message(self, message):
        if message.author == self.bot.user:
            return

        c.execute("SELECT character_id, name, prefix, image_url, user_id FROM characters")
        characters = c.fetchall()

        character_data = {(character_id, user_id): (name, prefix, image_url) for character_id, name, prefix, image_url, user_id in characters}

        message_lines = message.content.split("\n")
        to_send = []
        should_delete = False
        current_character = None
        current_message = []
        reference_handled = False

        for line in message_lines:
            for (character_id, user_id), (name, prefix, image_url) in character_data.items():
                if line.startswith(prefix) and message.author.id == user_id:
                    if current_message:
                        new_message_content = "\n".join(current_message).strip()
                        if new_message_content:
                            reply_header = ""
                            if not reference_handled:
                                reply_header = await self.get_reply_header(message.reference)
                                reference_handled = True

                            reply_content = f"{reply_header}\n{new_message_content}"
                            to_send.append((current_character, reply_content, message.attachments))
                            current_message = []

                    current_character = (character_id, name, image_url)
                    current_message.append(line[len(prefix):].strip())
                    should_delete = True
                    break
            else:
                if current_character:
                    current_message.append(line)

        if current_message and current_character:
            new_message_content = "\n".join(current_message).strip()
            if new_message_content:
                reply_header = ""
                if not reference_handled:
                    reply_header = await self.get_reply_header(message.reference)
                    reference_handled = True

                reply_content = f"{reply_header}\n{new_message_content}"
                to_send.append((current_character, reply_content, message.attachments))

        if current_character:
            async with aiohttp.ClientSession() as session:
                parent_channel = message.channel.parent if isinstance(message.channel, discord.Thread) else message.channel
                webhook_name = f"KillyanHook-{current_character[0]}"
                webhooks = await parent_channel.webhooks()
                webhook = next((hook for hook in webhooks if hook.name == webhook_name), None)
                if webhook is None:
                    webhook = await parent_channel.create_webhook(name=webhook_name)

                for (character_id, name, image_url), reply_content, attachments in to_send:
                    await webhook.send(
                        content=reply_content,
                        username=name,
                        avatar_url=image_url,
                        allowed_mentions=discord.AllowedMentions(users=True),
                        suppress_embeds=True,
                        files=[await attachment.to_file() for attachment in attachments]
                    )

                    c.execute("UPDATE characters SET webhook_url=? WHERE character_id=?", (webhook.url, character_id))
                    conn.commit()

        if should_delete:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass

            for (character_id, _, _), _, _ in to_send:
                c.execute("UPDATE characters SET message_count = message_count + 1 WHERE character_id=?", (character_id,))
                conn.commit()

        if self.active:
            for (character_id, name, image_url), new_message_content, _ in to_send:
                data = {
                    "content": new_message_content,
                    "author": {"id": character_id, "name": name}
                }
                user = await self.bot.fetch_user(message.author.id)
                await self.process_webhook(data, user)

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.handle_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self.handle_message(after)

async def setup(bot):
    await bot.add_cog(Techniques(bot))
