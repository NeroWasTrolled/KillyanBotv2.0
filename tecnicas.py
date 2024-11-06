import sqlite3
import discord
from discord.ext import commands
from logs import Logs
import random
import re

conn = sqlite3.connect('characters.db')
c = conn.cursor()

def sanitize_input(input_str):
    if not re.match("^[a-zA-Z0-9\s]*$", input_str):
        return False
    return True

def apply_layout(user_id, title, description):
    c.execute("SELECT title_layout, description_layout FROM layout_settings WHERE user_id=?", (user_id,))
    layout = c.fetchone()

    if layout:
        title_layout, description_layout = layout
    else:
        title_layout = "╚╡ ⬥ {title} ⬥ ╞"
        description_layout = "╚───► *「{description}」*"

    formatted_title = title_layout.replace("{title}", title)
    formatted_description = description_layout.replace("{description}", description)

    return formatted_title, formatted_description

passives = {
    "Rare": [
        "Aumenta o XP ganho em 5%", 
        "Reduz o tempo de recarga em 3%", 
        "Aumenta a precisão em 2%", 
        "Chance de evasão aumentada em 3%", 
        "Efeito garantido em 10% dos usos",
        "Aumenta a chance de sucesso de efeitos de controle em 5%",
        "Aumenta a recuperação de energia em 2%"
    ],
    "Epic": [
        "Aumenta o XP ganho em 10%", 
        "Reduz o tempo de recarga em 5%", 
        "Dano crítico aumenta em 15%", 
        "Chance de golpe crítico aumenta em 10%", 
        "Aumenta a chance de aplicar debuffs em 8%", 
        "Reduz efeitos negativos sofridos em 5%", 
        "Ataques ignoram 5% da defesa do oponente"
    ],
    "Legendary": [
        "Duplica o XP ganho por uso", 
        "Reduz o tempo de recarga em 10%", 
        "Chance de golpe crítico aumenta em 25%", 
        "Todos os debuffs têm efeito garantido uma vez por combate",
        "Aumenta a resistência a controle de grupo em 15%", 
        "Chance de aplicar efeitos negativos adicionais em 10%", 
        "Recupera 5% da energia após usar uma habilidade"
    ],
    "Mythical": [
        "Triplica o XP ganho por uso", 
        "Reduz o tempo de recarga em 20%", 
        "Dano crítico aumenta em 50%", 
        "Efeitos de controle e debuffs são ineficazes por 5 segundos após o uso",
        "Chance de anular efeitos negativos do oponente em 25%", 
        "Aumenta todos os atributos temporariamente em 10% após usar uma habilidade",
        "Chance de recarregar instantaneamente uma habilidade ao usá-la"
    ]
}

rarity_probabilities = {
    "F-": {"Rare": 100, "Epic": 0, "Legendary": 0, "Mythical": 0},
    "F": {"Rare": 90, "Epic": 10, "Legendary": 0, "Mythical": 0},
    "E-": {"Rare": 80, "Epic": 15, "Legendary": 5, "Mythical": 0},
    "D-": {"Rare": 70, "Epic": 20, "Legendary": 10, "Mythical": 0},
    "C": {"Rare": 50, "Epic": 35, "Legendary": 15, "Mythical": 0},
    "B": {"Rare": 40, "Epic": 40, "Legendary": 20, "Mythical": 0},
    "A": {"Rare": 30, "Epic": 30, "Legendary": 30, "Mythical": 10},
    "S-": {"Rare": 20, "Epic": 30, "Legendary": 35, "Mythical": 15},
    "S": {"Rare": 10, "Epic": 20, "Legendary": 35, "Mythical": 35},
    "Z": {"Rare": 0, "Epic": 20, "Legendary": 30, "Mythical": 50},
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
        """Calcula a experiência e o nível de mastery"""
        xp_needed = 100 + (mastery * 20)
        while xp >= xp_needed:
            mastery += 1
            xp -= xp_needed
            xp_needed = 100 + (mastery * 20)
        return xp, mastery

    def get_xp_gain(self, mastery, passive=None):
        base_xp = random.randint(5, 15) 
        mastery_multiplier = 1 + (mastery / 200)  
        total_xp = base_xp * mastery_multiplier

        if passive and "XP ganho em" in passive:
            bonus = int(re.search(r'\d+', passive).group()) / 100
            total_xp *= (1 + bonus)

        return int(total_xp)

    def update_rank(self, mastery):
        """Atualiza o rank de uma técnica com base em seu mastery"""
        RANKS = {
            'F-': 0, 'F': 10, 'F+': 20, 'E-': 40, 'E': 60, 'E+': 80, 'D-': 100, 'D': 150, 'D+': 200, 'C-': 250, 'C': 300, 'C+': 350, 'B-': 400, 'B': 450, 'B+': 500, 'A-': 520, 'A': 540, 'A+': 560, 'S': 580, 'SS': 590, 'SSS': 600
        }

        for rank, mastery_required in sorted(RANKS.items(), key=lambda item: item[1]):
            if mastery < mastery_required:
                return rank
        return 'Z'

    def get_passive_by_rank(self, rank):
        """Obtém uma passiva com base no rank"""
        probabilities = rarity_probabilities[rank]
        rarity = random.choices(
            population=["Rare", "Epic", "Legendary", "Mythical"],
            weights=[probabilities["Rare"], probabilities["Epic"], probabilities["Legendary"], probabilities["Mythical"]],
            k=1
        )[0]
        passive = random.choice(passives[rarity])
        return rarity, passive

    async def process_webhook(self, message):
        """Processa os webhooks e o uso de técnicas"""

        webhook_name = message.author.name
        message_content = message.content

        c.execute("SELECT character_id, user_id, message_count FROM characters WHERE name=?", (webhook_name,))
        character_data = c.fetchone()

        if not character_data:
            return None

        character_id, user_id, message_count = character_data
        user = await self.bot.fetch_user(user_id)

        message_count += 1
        c.execute("UPDATE characters SET message_count=? WHERE character_id=?", (message_count, character_id))
        conn.commit()

        c.execute("SELECT technique_name, xp, mastery, usage_count, passive FROM techniques WHERE character_id=?", (character_id,))
        techniques = c.fetchall()

        bolded_texts = re.findall(r'\*\*(.*?)\*\*', message_content)

        hashtag_texts = re.findall(r'#\s*(.*)', message_content)

        processed_techniques = set()  

        for technique_name, xp, mastery, usage_count, current_passive in techniques:
            technique_found = False

            for bolded_text in bolded_texts:
                if technique_name.lower() in bolded_text.lower():
                    technique_found = True
                    break

            if not technique_found:
                for hashtag_text in hashtag_texts:
                    if technique_name.lower() in hashtag_text.lower():
                        technique_found = True
                        break

            if technique_found and technique_name.lower() not in processed_techniques:
                usage_count += 1
                new_xp = xp + self.get_xp_gain(mastery, current_passive)
                new_xp, new_mastery = self.calculate_new_mastery(new_xp, mastery)

                current_rank = self.update_rank(mastery)
                new_rank = self.update_rank(new_mastery)

                passive_triggered_message = self.check_and_apply_passive(current_passive, technique_name)

                if passive_triggered_message:
                    await message.channel.send(passive_triggered_message)

                if new_rank != current_rank:
                    rarity, new_passive = self.get_passive_by_rank(new_rank)

                    if new_passive != current_passive:
                        await user.send(f"- > **Você evoluiu para o rank {new_rank}! Nova passiva disponível: {new_passive} ({rarity}).**\n"
                                        f"**Passiva atual: {current_passive or 'Nenhuma'}**.\n"
                                        f"**Deseja trocar? Responda com 'sim' ou 'não'.**")

                        def check(m):
                            return m.author == user and m.content.lower() in ['sim', 'não']

                        try:
                            response = await self.bot.wait_for('message', check=check, timeout=30.0)
                            if response.content.lower() == 'sim':
                                current_passive = new_passive
                                await user.send(f"- > **Passiva trocada! Agora sua passiva é: {new_passive}**.")
                        except asyncio.TimeoutError:
                            await user.send("- > **Tempo esgotado. Mantendo a passiva atual.**")

                c.execute(
                    "UPDATE techniques SET xp=?, mastery=?, usage_count=?, passive=? WHERE character_id=? AND technique_name COLLATE NOCASE=?",
                    (new_xp, new_mastery, usage_count, current_passive, character_id, technique_name)
                )
                conn.commit()

                await user.send(f"- > **Técnica __`{technique_name}`__ usada! __`{webhook_name}`__ ganhou XP. Mastery agora é __`{new_mastery}`__, Rank agora é __`{new_rank}`__.**")

                processed_techniques.add(technique_name.lower())
    
    def check_and_apply_passive(self, passive, technique_name):
        """Aplica passivas com base em suas chances e retorna mensagens específicas."""
        if passive:
            if "dano crítico" in passive:
                chance = int(re.search(r'\d+', passive).group())
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} causou __dano crítico!__**"

            if "Chance de evasão aumentada" in passive:
                chance = int(re.search(r'\d+', passive).group())
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} teve __uma evasão incrível!__**"

            if "Efeito garantido" in passive:
                chance = int(re.search(r'\d+', passive).group())
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} teve __um acerto garantido!__**"

            if "Chance de aplicar debuffs" in passive:
                chance = int(re.search(r'\d+', passive).group())
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} aplicou __um debuff!__**"

            if "Reduz o tempo de recarga" in passive:
                reduction = int(re.search(r'\d+', passive).group())
                return f"- > **{technique_name} teve __o tempo de recarga reduzido em {reduction}%!__**"

            if "Aumenta a precisão" in passive:
                precision_increase = int(re.search(r'\d+', passive).group())
                return f"- > **{technique_name} teve __a precisão aumentada em {precision_increase}%!__**"

            if "Aumenta a chance de sucesso de efeitos de controle" in passive:
                control_increase = int(re.search(r'\d+', passive).group())
                return f"- > **{technique_name} teve __a chance de controle aumentada em {control_increase}%!__**"

            if "Aumenta a recuperação de energia" in passive:
                energy_recovery = int(re.search(r'\d+', passive).group())
                return f"- > **{technique_name} recuperou __{energy_recovery}% de energia!__**"

            if "Ataques ignoram" in passive:
                defense_ignored = int(re.search(r'\d+', passive).group())
                return f"- > **{technique_name} ignorou __{defense_ignored}% da defesa do oponente!__**"

            if "Recupera" in passive and "energia" in passive:
                energy_recovery = int(re.search(r'\d+', passive).group())
                return f"- > **{technique_name} recuperou __{energy_recovery}% de energia após o uso!__**"

            if "Chance de anular efeitos negativos" in passive:
                chance = int(re.search(r'\d+', passive).group())
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} __anulou efeitos negativos__ do oponente!**"

            if "Aumenta todos os atributos temporariamente" in passive:
                attribute_increase = int(re.search(r'\d+', passive).group())
                return f"- > **{technique_name} aumentou todos os atributos em __{attribute_increase}%__ temporariamente!**"

            if "Chance de recarregar instantaneamente" in passive:
                chance = int(re.search(r'\d+', passive).group())
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} foi __recarregada instantaneamente!__**"

        return None

    @commands.command(name='activate')
    async def activate(self, ctx):
        """Ativa ou desativa o modo de leitura de webhooks"""
        self.active = not self.active
        status = "𝐀𝐓𝐈𝐕𝐀𝐃𝐎" if self.active else "𝐃𝐄𝐒𝐀𝐓𝐈𝐕𝐀𝐃𝐎"
        await ctx.send(f"- > **A funcionalidade de leitura de webhooks está agora __`{status}`__.**")

    def parse_args(self, args):
        """Função para parsear os argumentos"""
        parts = re.findall(r"'(.*?)'|(\S+)", args)
        return [''.join(filter(None, part)) for part in parts]

    @commands.command(name='addtechnique')
    async def add_technique(self, ctx, *, args: str):
        """Comando para adicionar uma técnica a um personagem"""
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!addtechnique 'Nome do Personagem' 'Nome da Técnica'**", discord.Color.red())
            return

        character_name, technique_name = parsed_args[0], ' '.join(parsed_args[1:])

        passive = "Nenhuma"

        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para adicionar técnicas a ele.**", discord.Color.red())
            return

        character_id = character[0]

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await self.send_embed(ctx, "**__```𝐃𝐄𝐒𝐂𝐑𝐈𝐂̧𝐀̃𝐎 𝐃𝐀 𝐓𝐄́𝐂𝐍𝐈𝐂𝐀```__**", "- > **Por favor, forneça a descrição da técnica.**")
        try:
            description_message = await self.bot.wait_for('message', check=check, timeout=60.0)
            description = description_message.content
            image_url = description_message.attachments[0].url if description_message.attachments else None

            c.execute("INSERT INTO techniques (character_id, technique_name, user_id, image_url, description, passive) VALUES (?, ?, ?, ?, ?, ?)",
                  (character_id, technique_name, ctx.author.id, image_url, description, passive))
            conn.commit()
            await self.send_embed(ctx, "**__```𝐓𝐄́𝐂𝐍𝐈𝐂𝐀 𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐃𝐀```__**", f"- > **Técnica __`{technique_name}`__ adicionada ao personagem __`{character_name}`__.**", discord.Color.green(), image_url)
        except asyncio.TimeoutError:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Tempo esgotado. Por favor, tente novamente.**", discord.Color.red())

    @commands.command(name='removetechnique')
    async def remove_technique(self, ctx, *, args: str):
        """Comando para remover uma técnica de um personagem"""
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!removetechnique 'Nome do Personagem' 'Nome da Técnica'**", discord.Color.red())
            return

        character_name, technique_name = parsed_args[0], ' '.join(parsed_args[1:])
        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para remover técnicas dele.**", discord.Color.red())
            return

        character_id = character[0]
        c.execute("DELETE FROM techniques WHERE character_id=? AND technique_name COLLATE NOCASE=?", 
                  (character_id, technique_name))
        if c.rowcount == 0:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada ou você não tem permissão para removê-la.**", discord.Color.red())
        else:
            conn.commit()
            await self.send_embed(ctx, "**__```𝐓𝐄́𝐂𝐍𝐈𝐂𝐀 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐀```__**", f"- > **Técnica __`{technique_name}`__ removida do personagem __`{character_name}`__.**", discord.Color.green())

    @commands.command(name='showtechnique')
    async def show_technique(self, ctx, *, args: str):
        """Comando para exibir informações de uma técnica"""
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!showtechnique 'Nome do Personagem' 'Nome da Técnica'**", discord.Color.red())
            return

        character_name, technique_name = parsed_args[0], ' '.join(parsed_args[1:])
        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para visualizar técnicas dele.**", discord.Color.red())
            return

        character_id = character[0]
        c.execute("SELECT technique_name, description, image_url, xp, mastery, passive FROM techniques WHERE character_id=? AND technique_name COLLATE NOCASE=?", 
                  (character_id, technique_name))
        technique = c.fetchone()
        if not technique:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada ou você não tem permissão para visualizá-la.**", discord.Color.red())
            return

        technique_name, description, image_url, xp, mastery, passive = technique
        xp_needed = 100 + (mastery * 20)
        xp_percentage = (xp / xp_needed) * 100
        current_rank = self.update_rank(mastery)

        formatted_title, formatted_description = apply_layout(ctx.author.id, technique_name, description)

        formatted_description += (
            f"\n\n**𝐌𝐀𝐒𝐓𝐄𝐑𝐘:** {mastery}/600"
            f"\n**𝐄𝐗𝐏:** {xp}/{xp_needed} ({xp_percentage:.2f}%)"
            f"\n**𝐑𝐀𝐍𝐊 𝐀𝐓𝐔𝐀𝐋:** {current_rank}"
            f"\n**𝐏𝐀𝐒𝐒𝐈𝐕𝐀:** {passive or 'Nenhuma'}"
        )

        await self.send_embed(ctx, formatted_title, formatted_description, discord.Color.blue(), image_url)

    
    @commands.command(name='settechniquelevel')
    async def set_technique_level(self, ctx, *, args: str):
        """Define o nível de mastery de uma técnica"""
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 3:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!settechniquelevel 'Nome do Personagem' 'Nome da Técnica' <Novo Nível>**", discord.Color.red())
            return

        character_name, technique_name, new_level_str = parsed_args[0], ' '.join(parsed_args[1:-1]), parsed_args[-1]

        try:
            new_mastery_level = int(new_level_str)
            if new_mastery_level <= 0: 
                await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **O nível de mastery deve ser um número inteiro positivo.**", discord.Color.red())
                return
        except ValueError:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **O nível deve ser um número inteiro válido.**", discord.Color.red())
            return

        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para alterar técnicas dele.**", discord.Color.red())
            return

        character_id = character[0]

        c.execute("SELECT technique_name, xp, mastery FROM techniques WHERE character_id=? AND technique_name COLLATE NOCASE=?", (character_id, technique_name))
        technique = c.fetchone()
        if not technique:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada ou você não tem permissão para alterar essa técnica.**", discord.Color.red())
            return

        new_mastery = new_mastery_level
        new_xp = 0

        c.execute("UPDATE techniques SET mastery=?, xp=? WHERE character_id=? AND technique_name COLLATE NOCASE=?", 
                  (new_mastery, new_xp, character_id, technique_name))
        conn.commit()

        await self.send_embed(ctx, "**__```𝐍𝐈́𝐕𝐄𝐋 𝐀𝐉𝐔𝐒𝐓𝐀𝐃𝐎```__**", f"- > **Técnica __`{technique_name}`__ agora está no nível de mastery __`{new_mastery}`__.**", discord.Color.green())

    @commands.has_permissions(administrator=True)
    @commands.command(name='setpassive')
    async def set_passive(self, ctx, *, args: str):
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 3:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!setpassive 'Nome do Personagem' 'Nome da Técnica' 'Passiva'**", discord.Color.red())
            return

        character_name, technique_name, passive_name = parsed_args[0], parsed_args[1], ' '.join(parsed_args[2:])

        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para alterar passivas dele.**", discord.Color.red())
            return

        character_id = character[0]

        c.execute("SELECT technique_name FROM techniques WHERE character_id=? AND technique_name COLLATE NOCASE=?", (character_id, technique_name))
        technique = c.fetchone()
        if not technique:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada para o personagem.**", discord.Color.red())
            return

        c.execute("UPDATE techniques SET passive=? WHERE character_id=? AND technique_name COLLATE NOCASE=?", (passive_name, character_id, technique_name))
        conn.commit()

        await self.send_embed(ctx, "**__```𝐏𝐀𝐒𝐒𝐈𝐕𝐀 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐀```__**", f"- > **A passiva da técnica __`{technique_name}`__ foi atualizada para __`{passive_name}`__**", discord.Color.green())

    @commands.command(name='pfptechnique')
    async def pfptechnique(self, ctx, *, args: str):
        args = self.parse_args(args)
        if len(args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso correto: `kill!pfptechnique [nome personagem] [nome técnica]`**", discord.Color.red())
            return

        character_name, technique_name = args[0], ' '.join(args[1:])

        c.execute("SELECT technique_name FROM techniques WHERE character_id=(SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?) AND technique_name COLLATE NOCASE=?",
                  (character_name, ctx.author.id, technique_name))
        technique = c.fetchone()

        if not technique:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Técnica** **__`{technique_name}`__** **não encontrada para o personagem** **__`{character_name}`__**.", discord.Color.red())
            return

        if ctx.message.attachments:
            image_url = ctx.message.attachments[0].url
            message_id = ctx.message.id

            c.execute("UPDATE techniques SET image_url=?, message_id=? WHERE character_id=(SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?) AND technique_name COLLATE NOCASE=?",
                      (image_url, message_id, character_name, ctx.author.id, technique_name))
            conn.commit()

            await self.send_embed(ctx, "**__```𝐈𝐌𝐀𝐆𝐄𝐌 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐀```__**", f"- > **Imagem da técnica** **__`{technique_name}`__** **atualizada com sucesso para o personagem** **__`{character_name}`__**.", discord.Color.green(), image_url)
        else:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Por favor, anexe uma imagem ao usar este comando para definir o avatar da técnica.**", discord.Color.red())

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listener para processar mensagens recebidas de webhooks"""
        if self.active and message.webhook_id:
            await self.process_webhook(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Listener para processar mensagens editadas"""
        await self.process_webhook(after)

async def setup(bot):
    await bot.add_cog(Techniques(bot))
