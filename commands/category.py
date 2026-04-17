import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import math
import asyncio
from database.connection import create_connection
from utils.common import (
    apply_layout as shared_apply_layout,
    parse_quoted_args,
    sanitize_input,
    send_embed as shared_send_embed,
    to_bold_sans_serif,
)

class Categories(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = create_connection()
        self.c = self.conn.cursor()

    def parse_registration_args(self, args):
        """Função para parsear argumentos"""
        return parse_quoted_args(args)

    def sanitize_input(self, input_str):
        """Sanitiza entradas para evitar caracteres especiais"""
        return sanitize_input(input_str)

    async def send_embed(self, ctx, title, description, color, image_url=None):
        """Envia um embed formatado"""
        await shared_send_embed(ctx, title, description, color, image_url=image_url)

    @commands.command(name='createability', aliases=['createcategory'])
    async def create_category(self, ctx, *, args: str):
        """Inicia a criação de uma habilidade vinculada a um personagem com validação"""
        parsed_args = self.parse_registration_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!createability 'Nome do Personagem' 'Nome da Habilidade'**", discord.Color.red())
            return

        character_name, ability_name = parsed_args[0], ' '.join(parsed_args[1:])

        if not self.sanitize_input(character_name) or not self.sanitize_input(ability_name):
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Nome de personagem ou habilidade inválido.**", discord.Color.red())
            return

        self.c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = self.c.fetchone()
        formatted_character = to_bold_sans_serif(character_name)
        formatted_ability = to_bold_sans_serif(ability_name)

        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado.**", discord.Color.red())
            return

        character_id = character[0]

        await self.send_embed(
            ctx,
            "**__```𝐃𝐄𝐒𝐂𝐑𝐈𝐂̧𝐀̃𝐎 𝐃𝐀 𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄```__**",
            f"- > **Forneça a descrição de {formatted_ability} para o personagem {formatted_character}. Você tem 1 minuto.**",
            discord.Color.blue(),
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            description_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            description = description_msg.content
        except asyncio.TimeoutError:
            await self.send_embed(ctx, "**__```𝐓𝐄𝐌𝐏𝐎 𝐄𝐒𝐆𝐎𝐓𝐀𝐃𝐎```__**", "- > **O processo de criação da habilidade foi cancelado.**", discord.Color.red())
            return

        self.c.execute("INSERT INTO abilities (character_id, category_name, description) VALUES (?, ?, ?)", (character_id, ability_name, description))
        self.conn.commit()

        await self.send_embed(
            ctx,
            "**__```𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄 𝐂𝐑𝐈𝐀𝐃𝐀```__**",
            f"- > **A habilidade {formatted_ability} foi criada com sucesso para {formatted_character}.**",
            discord.Color.green(),
        )


    @commands.command(name='delability', aliases=['delcategory'])
    async def remove_category(self, ctx, *, args: str):
        """Remove uma habilidade de um personagem"""
        parsed_args = self.parse_registration_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!delability 'Nome do Personagem' 'Nome da Habilidade'**", discord.Color.red())
            return

        character_name, ability_name = parsed_args[0], ' '.join(parsed_args[1:])

        if not self.sanitize_input(ability_name):
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Nome de habilidade inválido.**", discord.Color.red())
            return

        self.c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = self.c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para remover habilidades dele.**", discord.Color.red())
            return

        character_id = character[0]

        self.c.execute("SELECT category_id FROM abilities WHERE character_id=? AND category_name COLLATE NOCASE=?", (character_id, ability_name))
        category = self.c.fetchone()

        if not category:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Habilidade não encontrada.**", discord.Color.red())
            return

        category_id = category[0]

        formatted_ability = to_bold_sans_serif(ability_name)
        await self.send_embed(
            ctx,
            "**__```𝐂𝐎𝐍𝐅𝐈𝐑𝐌𝐀𝐂̧𝐀̃𝐎```__**",
            f"- > **Deseja remover a habilidade {formatted_ability}? Responda com `sim` ou `não`.**",
            discord.Color.orange(),
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            confirmation = await self.bot.wait_for('message', check=check, timeout=30.0)
            if confirmation.content.lower() != 'sim':
                await self.send_embed(ctx, "**__```𝐂𝐀𝐍𝐂𝐄𝐋𝐀𝐃𝐎```__**", "- > **Remoção cancelada.**", discord.Color.red())
                return
        except asyncio.TimeoutError:
            await self.send_embed(ctx, "**__```𝐓𝐄𝐌𝐏𝐎 𝐄𝐒𝐆𝐎𝐓𝐀𝐃𝐎```__**", "- > **Remoção cancelada por tempo esgotado.**", discord.Color.red())
            return

        self.c.execute("UPDATE techniques SET category_id=NULL WHERE category_id=?", (category_id,))
        self.c.execute("DELETE FROM abilities WHERE category_id=?", (category_id,))
        self.conn.commit()

        await self.send_embed(
            ctx,
            "**__```𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐀```__**",
            f"- > **A habilidade {formatted_ability} e suas associações foram removidas com sucesso.**",
            discord.Color.green(),
        )


    @commands.command(name='assignability', aliases=['assigntechnique'])
    async def assign_technique(self, ctx, *, args: str):
        """Vincula uma técnica a uma habilidade"""
        parsed_args = self.parse_registration_args(args)
        if len(parsed_args) < 3:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!assignability 'Nome do Personagem' 'Nome da Técnica' 'Nome da Habilidade'**", discord.Color.red())
            return

        character_name, technique_name, ability_name = parsed_args[0], parsed_args[1], ' '.join(parsed_args[2:])

        if not self.sanitize_input(character_name) or not self.sanitize_input(technique_name) or not self.sanitize_input(ability_name):
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Nome de personagem, técnica ou habilidade inválido.**", discord.Color.red())
            return

        self.c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = self.c.fetchone()

        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para vinculá-lo.**", discord.Color.red())
            return

        character_id = character[0]

        self.c.execute("SELECT category_id FROM abilities WHERE character_id=? AND category_name COLLATE NOCASE=?", (character_id, ability_name))
        category = self.c.fetchone()

        if not category:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Habilidade não encontrada.**", discord.Color.red())
            return

        category_id = category[0]

        self.c.execute("UPDATE techniques SET category_id=? WHERE character_id=? AND technique_name COLLATE NOCASE=?", (category_id, character_id, technique_name))
        if self.c.rowcount == 0:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada para o personagem.**", discord.Color.red())
        else:
            self.conn.commit()
            formatted_technique = to_bold_sans_serif(technique_name)
            formatted_ability = to_bold_sans_serif(ability_name)
            await self.send_embed(
                ctx,
                "**__```𝐕𝐈𝐍𝐂𝐔𝐋𝐀𝐂̧𝐀̃𝐎 𝐂𝐎𝐍𝐂𝐋𝐔𝐈́𝐃𝐀```__**",
                f"- > **A técnica {formatted_technique} foi vinculada à habilidade {formatted_ability}.**",
                discord.Color.green(),
            )

    @commands.command(name='listabilities', aliases=['listcategories'])
    async def list_categories(self, ctx, character_name: str):
        """Lista todas as habilidades e as técnicas vinculadas a um personagem"""
        self.c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = self.c.fetchone()

        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado.**", discord.Color.red())
            return

        character_id = character[0]

        self.c.execute("SELECT category_name, description FROM abilities WHERE character_id=?", (character_id,))
        categories = self.c.fetchall()

        if not categories:
            await self.send_embed(ctx, "**__```𝐒𝐄𝐌 𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄𝐒```__**", "- > **Nenhuma habilidade encontrada para o personagem.**", discord.Color.blue())
            return

        per_page = 5
        total_results = len(categories)
        total_pages = math.ceil(total_results / per_page)
        current_page = 1

        async def update_message(interaction, page):
            if page < 1:
                page = total_pages
            elif page > total_pages:
                page = 1
            embed = await self.create_list_embed(ctx, categories, page, per_page, total_pages, total_results, character_name, character_id)
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

            modal = self.GoToPageModal(update_message, total_pages)
            await interaction.response.send_modal(modal)

        embed = await self.create_list_embed(ctx, categories, current_page, per_page, total_pages, total_results, character_name, character_id)
        await ctx.send(embed=embed, view=create_list_view(current_page))

    async def create_list_embed(self, ctx, categories, page, per_page, total_pages, total_results, character_name, character_id):
        start = (page - 1) * per_page
        end = start + per_page

        formatted_character = to_bold_sans_serif(character_name)
        embed = discord.Embed(title=f"𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄𝐒 𝐃𝐄 {formatted_character} (Página {page}/{total_pages})", color=discord.Color.blue())
        result_list = []
        for category_name, description in categories[start:end]:
            self.c.execute("SELECT technique_name FROM techniques WHERE category_id=(SELECT category_id FROM abilities WHERE category_name=? AND character_id=?)", (category_name, character_id))
            techniques = self.c.fetchall()
            technique_list = ', '.join([tech[0] for tech in techniques]) or 'Nenhuma técnica associada'

            formatted_title, formatted_description = self.apply_layout(ctx.author.id, category_name, description)

            result_list.append(f"{formatted_title}\n{formatted_description}\n**Técnicas**: {technique_list}")

        embed.description = "\n\n".join(result_list)
        embed.set_footer(text=f"Página {page}/{total_pages} • Total de Habilidades: {total_results}")
        return embed

    def apply_layout(self, user_id, title, description):
        """Aplica o layout personalizado para o título e descrição"""
        return shared_apply_layout(
            user_id,
            title,
            description,
            default_title="╚╡ ⬥ {title} ⬥ ╞",
            default_description="╚───► *「{description}」*",
        )

    class GoToPageModal(Modal):
        def __init__(self, update_message, total_pages):
            super().__init__(title="Ir para página")
            self.update_message = update_message
            self.total_pages = total_pages
            self.page_number = TextInput(label="Número da página", style=discord.TextStyle.short)
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

    @commands.command(name='abilitydetails', aliases=['categorydetails'])
    async def category_details(self, ctx, *, args: str):
        """Exibe detalhes de uma habilidade específica e suas técnicas"""
        parsed_args = self.parse_registration_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!abilitydetails 'Nome do Personagem' 'Nome da Habilidade'**", discord.Color.red())
            return

        character_name, category_name = parsed_args[0], ' '.join(parsed_args[1:])

        if not self.sanitize_input(category_name):
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Nome de habilidade inválido.**", discord.Color.red())
            return

        self.c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = self.c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para visualizar as habilidades dele.**", discord.Color.red())
            return

        character_id = character[0]

        self.c.execute("SELECT category_name, description FROM abilities WHERE character_id=? AND category_name COLLATE NOCASE=?", (character_id, category_name))
        category = self.c.fetchone()

        if not category:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Habilidade não encontrada ou você não tem permissão para visualizá-la.**", discord.Color.red())
            return

        category_name, description = category

        self.c.execute("SELECT technique_name FROM techniques WHERE category_id=(SELECT category_id FROM abilities WHERE category_name=? AND character_id=?)", (category_name, character_id))
        techniques = self.c.fetchall()
        technique_list = ', '.join([tech[0] for tech in techniques]) or 'Nenhuma técnica associada'

        formatted_title, formatted_description = self.apply_layout(ctx.author.id, category_name, description)

        formatted_description += f"\n\n**Técnicas:** {technique_list}"

        await self.send_embed(ctx, formatted_title, formatted_description, discord.Color.blue())

async def setup(bot):
    await bot.add_cog(Categories(bot))