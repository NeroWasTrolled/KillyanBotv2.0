import sqlite3
import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import math
import re

class Categories(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('characters.db')
        self.c = self.conn.cursor()

    def parse_registration_args(self, args):
        """Função para parsear argumentos"""
        pattern = r'\'(.*?)\'|(\S+)'
        matches = re.findall(pattern, args)
        tokens = [match[0] if match[0] else match[1] for match in matches]

        name = tokens[0] if len(tokens) > 0 else None
        return tokens

    def sanitize_input(self, input_str):
        """Sanitiza entradas para evitar caracteres especiais"""
        if not re.match("^[a-zA-Z0-9\s]*$", input_str):
            return False
        return True

    def apply_layout(self, user_id, title, description):
        """Aplica o layout personalizado para o título e descrição"""
        self.c.execute("SELECT title_layout, description_layout FROM layout_settings WHERE user_id=?", (user_id,))
        layout = self.c.fetchone()

        if layout:
            title_layout, description_layout = layout
        else:
            title_layout = "╚╡ ⬥ {title} ⬥ ╞"
            description_layout = "╚───► *「{description}」*"

        formatted_title = title_layout.replace("{title}", title)
        formatted_description = description_layout.replace("{description}", description)

        return formatted_title, formatted_description

    async def send_embed(self, ctx, title, description, color, image_url=None):
        """Envia um embed formatado"""
        embed = discord.Embed(title=title, description=description, color=color)
        if image_url:
            embed.set_image(url=image_url)
        await ctx.send(embed=embed)

    @commands.command(name='createcategory')
    async def create_category(self, ctx, *, args: str):
        """Inicia a criação de uma categoria vinculada a um personagem com validação"""
        parsed_args = self.parse_registration_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!createcategory 'Nome do Personagem' 'Nome da Categoria'**", discord.Color.red())
            return

        character_name, category_name = parsed_args[0], ' '.join(parsed_args[1:])

        if not self.sanitize_input(character_name) or not self.sanitize_input(category_name):
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Nome de personagem ou categoria inválido.**", discord.Color.red())
            return

        self.c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = self.c.fetchone()

        if not character:
            await ctx.send("- > **Personagem não encontrado.**")
            return

        character_id = character[0]

        await ctx.send(f"- > **Por favor, forneça uma descrição para a categoria `{category_name}`. Você tem 1 minuto.**")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            description_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            description = description_msg.content
        except asyncio.TimeoutError:
            await ctx.send("- > **Tempo esgotado. O processo de criação da categoria foi cancelado.**")
            return

        self.c.execute("INSERT INTO categories (character_id, category_name, description) VALUES (?, ?, ?)", (character_id, category_name, description))
        self.conn.commit()

        await ctx.send(f"- > **Categoria `{category_name}` criada com sucesso para o personagem `{character_name}`.**")


    @commands.command(name='delcategory')
    async def remove_category(self, ctx, *, args: str):
        """Remove uma categoria de um personagem"""
        parsed_args = self.parse_registration_args(args)
        if len(parsed_args) < 1:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!removecategory 'Nome do Personagem' 'Nome da Categoria'**", discord.Color.red())
            return

        character_name, category_name = parsed_args[0], ' '.join(parsed_args[1:])

        if not self.sanitize_input(category_name):
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Nome de categoria inválido.**", discord.Color.red())
            return

        self.c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = self.c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para remover categorias dele.**", discord.Color.red())
            return

        character_id = character[0]

        self.c.execute("SELECT category_id FROM categories WHERE character_id=? AND category_name COLLATE NOCASE=?", (character_id, category_name))
        category = self.c.fetchone()

        if not category:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Categoria não encontrada.**", discord.Color.red())
            return

        category_id = category[0]

        await ctx.send(f"- > **Tem certeza que deseja remover a categoria `{category_name}`? Responda com `sim` ou `não`.**")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            confirmation = await self.bot.wait_for('message', check=check, timeout=30.0)
            if confirmation.content.lower() != 'sim':
                await ctx.send("- > **Remoção cancelada.**")
                return
        except asyncio.TimeoutError:
            await ctx.send("- > **Tempo esgotado. Remoção cancelada.**")
            return

        self.c.execute("UPDATE techniques SET category_id=NULL WHERE category_id=?", (category_id,))
        self.c.execute("DELETE FROM categories WHERE category_id=?", (category_id,))
        self.conn.commit()

        await ctx.send(f"- > **Categoria `{category_name}` e suas associações foram removidas com sucesso.**")


    @commands.command(name='assigntechnique')
    async def assign_technique(self, ctx, *, args: str):
        """Vincula uma técnica a uma categoria"""
        parsed_args = self.parse_registration_args(args)
        if len(parsed_args) < 3:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!assigntechnique 'Nome do Personagem' 'Nome da Técnica' 'Nome da Categoria'**", discord.Color.red())
            return

        character_name, technique_name, category_name = parsed_args[0], parsed_args[1], ' '.join(parsed_args[2:])

        if not self.sanitize_input(character_name) or not self.sanitize_input(technique_name) or not self.sanitize_input(category_name):
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Nome de personagem, técnica ou categoria inválido.**", discord.Color.red())
            return

        self.c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = self.c.fetchone()

        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para vinculá-lo.**", discord.Color.red())
            return

        character_id = character[0]

        self.c.execute("SELECT category_id FROM categories WHERE character_id=? AND category_name COLLATE NOCASE=?", (character_id, category_name))
        category = self.c.fetchone()

        if not category:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Categoria não encontrada.**", discord.Color.red())
            return

        category_id = category[0]

        self.c.execute("UPDATE techniques SET category_id=? WHERE character_id=? AND technique_name COLLATE NOCASE=?", (category_id, character_id, technique_name))
        if self.c.rowcount == 0:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada para o personagem.**", discord.Color.red())
        else:
            self.conn.commit()
            await self.send_embed(ctx, "- > **Sucesso**", f"- > **Técnica `{technique_name}` vinculada à categoria `{category_name}` com sucesso.**", discord.Color.green())

    @commands.command(name='listcategories')
    async def list_categories(self, ctx, character_name: str):
        """Lista todas as categorias e as técnicas vinculadas a um personagem"""
        self.c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = self.c.fetchone()

        if not character:
            await ctx.send("- > **Personagem não encontrado.**")
            return

        character_id = character[0]

        self.c.execute("SELECT category_name, description FROM categories WHERE character_id=?", (character_id,))
        categories = self.c.fetchall()

        if not categories:
            await ctx.send("- > **Nenhuma categoria encontrada para o personagem.**")
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

            modal = GoToPageModal(update_message, total_pages)
            await interaction.response.send_modal(modal)

        embed = await self.create_list_embed(ctx, categories, current_page, per_page, total_pages, total_results, character_name, character_id)
        await ctx.send(embed=embed, view=create_list_view(current_page))

    async def create_list_embed(self, ctx, categories, page, per_page, total_pages, total_results, character_name, character_id):
        start = (page - 1) * per_page
        end = start + per_page

        embed = discord.Embed(title=f"{character_name}'s Registered Categories (Page {page}/{total_pages})", color=discord.Color.blue())
        result_list = []
        for category_name, description in categories[start:end]:
            self.c.execute("SELECT technique_name FROM techniques WHERE category_id=(SELECT category_id FROM categories WHERE category_name=? AND character_id=?)", (category_name, character_id))
            techniques = self.c.fetchall()
            technique_list = ', '.join([tech[0] for tech in techniques]) or 'Nenhuma técnica associada'

            formatted_title, formatted_description = self.apply_layout(ctx.author.id, category_name, description)

            result_list.append(f"{formatted_title}\n{formatted_description}\n**Skills**: {technique_list}")

        embed.description = "\n\n".join(result_list)
        embed.set_footer(text=f"Page {page}/{total_pages} • Total Categories: {total_results}")
        return embed

    def apply_layout(self, user_id, title, description):
        """Aplica o layout personalizado para o título e descrição"""
        self.c.execute("SELECT title_layout, description_layout FROM layout_settings WHERE user_id=?", (user_id,))
        layout = self.c.fetchone()

        if layout:
            title_layout, description_layout = layout
        else:
            title_layout = "╚╡ ⬥ {title} ⬥ ╞"
            description_layout = "╚───► *「{description}」*"

        formatted_title = title_layout.replace("{title}", title)
        formatted_description = description_layout.replace("{description}", description)

        return formatted_title, formatted_description

    class GoToPageModal(Modal):
        def __init__(self, update_message, total_pages):
            super().__init__(title="Go to Page")
            self.update_message = update_message
            self.total_pages = total_pages
            self.page_number = TextInput(label="Page Number", style=discord.TextStyle.short)
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

    @commands.command(name='categorydetails')
    async def category_details(self, ctx, *, args: str):
        """Exibe detalhes de uma categoria específica e suas técnicas"""
        parsed_args = self.parse_registration_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!categorydetails 'Nome do Personagem' 'Nome da Categoria'**", discord.Color.red())
            return

        character_name, category_name = parsed_args[0], ' '.join(parsed_args[1:])

        if not self.sanitize_input(category_name):
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Nome de categoria inválido.**", discord.Color.red())
            return

        self.c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = self.c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para visualizar as categorias dele.**", discord.Color.red())
            return

        character_id = character[0]

        self.c.execute("SELECT category_name, description FROM categories WHERE character_id=? AND category_name COLLATE NOCASE=?", (character_id, category_name))
        category = self.c.fetchone()

        if not category:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Categoria não encontrada ou você não tem permissão para visualizá-la.**", discord.Color.red())
            return

        category_name, description = category

        self.c.execute("SELECT technique_name FROM techniques WHERE category_id=(SELECT category_id FROM categories WHERE category_name=? AND character_id=?)", (category_name, character_id))
        techniques = self.c.fetchall()
        technique_list = ', '.join([tech[0] for tech in techniques]) or 'Nenhuma técnica associada'

        formatted_title, formatted_description = self.apply_layout(ctx.author.id, category_name, description)

        formatted_description += f"\n\n**Skills:** {technique_list}"

        await self.send_embed(ctx, formatted_title, formatted_description, discord.Color.blue())

async def setup(bot):
    await bot.add_cog(Categories(bot))