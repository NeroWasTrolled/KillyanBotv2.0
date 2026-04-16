import sqlite3
import discord
from discord.ext import commands
from commands.logs import Logs
from discord.ui import Modal, TextInput, Button, View
import re
from database.connection import create_connection
from utils.common import sanitize_input, send_embed
from services.characteristics_service import (
    get_class_assignment_schema,
    get_class_role_multiplier,
    get_class_slots,
)

conn = create_connection()
c = conn.cursor()

def parse_assign_args(args):
    pattern = r'\'(.*?)\'|(\S+)'
    matches = re.findall(pattern, args)
    tokens = [match[0] if match[0] else match[1] for match in matches]
    character_name = tokens[0] if len(tokens) > 0 else None
    class_tokens = tokens[1:] if len(tokens) > 1 else []
    return character_name, class_tokens

class ClassNameModal(Modal):
    def __init__(self):
        super().__init__(title="𝐍𝐎𝐌𝐄 𝐃𝐀 𝐂𝐋𝐀𝐒𝐒𝐄")
        self.class_name = TextInput(label="𝐍𝐎𝐌𝐄 𝐃𝐀 𝐂𝐋𝐀𝐒𝐒𝐄", style=discord.TextStyle.short, placeholder="𝑫𝒊𝒈𝒊𝒕𝒆 𝒐 𝒏𝒐𝒎𝒆 𝒅𝒂 𝒄𝒍𝒂𝒔𝒔𝒆", required=True)
        self.add_item(self.class_name)

    async def on_submit(self, interaction: discord.Interaction):
        class_name = self.class_name.value.strip()
        if not class_name:
            await interaction.response.send_message("𝑵𝒐𝒎𝒆 𝒅𝒂 𝒄𝒍𝒂𝒔𝒔𝒆 𝒏𝒂̃𝒐 𝒑𝒐𝒅𝒆 𝒔𝒆𝒓 𝒗𝒂𝒛𝒊𝒐.", ephemeral=True)
            return

        c.execute("SELECT 1 FROM classes WHERE class_name = ?", (class_name,))
        if c.fetchone():
            await interaction.response.send_message(f"- > **A classe** **__{class_name}__** **já existe. Escolha outro nome.**", ephemeral=True)
            return

        view = View()
        view.add_item(AttributesModal1Button(class_name))
        await interaction.response.send_message(f"- > **Classe** **__{class_name}__** **- Configuração dos atributos iniciada.**", view=view, ephemeral=True)

class AttributesModal1(Modal):
    def __init__(self, class_name):
        super().__init__(title="𝐀𝐓𝐑𝐈𝐁𝐔𝐓𝐎𝐒")
        self.class_name = class_name
        self.forca = TextInput(label="𝐒𝐓𝐑𝐄𝐍𝐆𝐓𝐇", style=discord.TextStyle.short, placeholder="0", required=True)
        self.resistencia = TextInput(label="𝐑𝐄𝐒𝐈𝐒𝐓𝐀𝐍𝐂𝐄", style=discord.TextStyle.short, placeholder="0", required=True)
        self.vitalidade = TextInput(label="𝐕𝐈𝐓𝐀𝐋𝐈𝐓𝐘", style=discord.TextStyle.short, placeholder="0", required=True)
        self.add_item(self.forca)
        self.add_item(self.resistencia)
        self.add_item(self.vitalidade)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            forca = int(self.forca.value)
            resistencia = int(self.resistencia.value)
            vitalidade = int(self.vitalidade.value)
        except ValueError:
            await interaction.response.send_message("- > **Os atributos devem ser números inteiros.**", ephemeral=True)
            return

        if any(attr < 0 for attr in (forca, resistencia, vitalidade)):
            await interaction.response.send_message("- > **Os atributos devem ser valores positivos.**", ephemeral=True)
            return

        view = View()
        view.add_item(AttributesModal2Button(self.class_name, forca, resistencia, vitalidade))
        await interaction.response.send_message("- > **Primeira parte dos atributos configurada.**", view=view, ephemeral=True)

class AttributesModal2(Modal):
    def __init__(self, class_name, forca, resistencia, vitalidade):
        super().__init__(title="𝐀𝐓𝐑𝐈𝐁𝐔𝐓𝐎𝐒")
        self.class_name = class_name
        self.forca = forca
        self.resistencia = resistencia
        self.vitalidade = vitalidade
        self.agilidade = TextInput(label="𝐀𝐆𝐈𝐋𝐈𝐓𝐘", style=discord.TextStyle.short, placeholder="0", required=True)
        self.sentidos = TextInput(label="𝐒𝐄𝐍𝐒𝐄𝐒", style=discord.TextStyle.short, placeholder="0", required=True)
        self.inteligencia = TextInput(label="𝐈𝐍𝐓𝐄𝐋𝐋𝐈𝐆𝐄𝐍𝐂𝐄", style=discord.TextStyle.short, placeholder="0", required=True)
        self.add_item(self.agilidade)
        self.add_item(self.sentidos)
        self.add_item(self.inteligencia)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            agilidade = int(self.agilidade.value)
            sentidos = int(self.sentidos.value)
            inteligencia = int(self.inteligencia.value)
        except ValueError:
            await interaction.response.send_message("- > **Os atributos devem ser números inteiros.**", ephemeral=True)
            return

        if any(attr < 0 for attr in (agilidade, sentidos, inteligencia)):
            await interaction.response.send_message("- > **Os atributos devem ser valores positivos.**", ephemeral=True)
            return

        try:
            c.execute("INSERT INTO classes (class_name, forca, resistencia, vitalidade, agilidade, sentidos, inteligencia) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (self.class_name, self.forca, self.resistencia, self.vitalidade, agilidade, sentidos, inteligencia))
            conn.commit()
            await interaction.response.send_message(f"- > **Classe __{self.class_name}__ registrada com sucesso com os atributos especificados.**", ephemeral=True)
        except sqlite3.IntegrityError:
            await interaction.response.send_message(f"- > **A classe __{self.class_name}__ já existe. Escolha outro nome.**", ephemeral=True)

class StartClassCreationButton(Button):
    def __init__(self):
        super().__init__(label="𝐂𝐑𝐈𝐀𝐑 𝐂𝐋𝐀𝐒𝐒𝐄", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        modal = ClassNameModal()
        await interaction.response.send_modal(modal)

class AttributesModal1Button(Button):
    def __init__(self, class_name):
        super().__init__(label="𝐀𝐓𝐑𝐈𝐁𝐔𝐓𝐎𝐒", style=discord.ButtonStyle.secondary)
        self.class_name = class_name

    async def callback(self, interaction: discord.Interaction):
        modal = AttributesModal1(self.class_name)
        await interaction.response.send_modal(modal)

class AttributesModal2Button(Button):
    def __init__(self, class_name, forca, resistencia, vitalidade):
        super().__init__(label="𝐀𝐓𝐑𝐈𝐁𝐔𝐓𝐎𝐒", style=discord.ButtonStyle.secondary)
        self.class_name = class_name
        self.forca = forca
        self.resistencia = resistencia
        self.vitalidade = vitalidade

    async def callback(self, interaction: discord.Interaction):
        modal = AttributesModal2(self.class_name, self.forca, self.resistencia, self.vitalidade)
        await interaction.response.send_modal(modal)

class CancelButton(Button):
    def __init__(self):
        super().__init__(label="𝐂𝐀𝐍𝐂𝐄𝐋𝐀𝐑", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        if interaction.message is not None:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("- > **Nada para cancelar nesta interação.**", ephemeral=True)

@commands.has_permissions(administrator=True)
@commands.command(name='registerclass', aliases=['newclass', 'addclass'])
async def registerclass(ctx):
    view = View()
    view.add_item(StartClassCreationButton())
    view.add_item(CancelButton())
    await ctx.send("- > **Clique no botão abaixo para iniciar a criação da classe ou cancelar.**", view=view)

@commands.has_permissions(administrator=True)
@commands.command(name='removeclass', aliases=['delclass'])
async def removeclass(ctx, *, class_name: str):
    c.execute("DELETE FROM classes WHERE class_name=?", (class_name,))
    if c.rowcount == 0:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Classe não encontrada.**", discord.Color.red())
    else:
        conn.commit()
        await send_embed(ctx, "𝐂𝐋𝐀𝐒𝐒𝐄 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐀", f'- > **Classe __{class_name}__ removida com sucesso.**', discord.Color.green())

class ClassListView(View):
    def __init__(self, pages, current_page):
        super().__init__(timeout=None)
        self.pages = pages
        self.current_page = current_page
        self.add_item(PreviousPageButton(self))
        self.add_item(PageButton(self))
        self.add_item(NextPageButton(self))

class PreviousPageButton(Button):
    def __init__(self, view):
        super().__init__(style=discord.ButtonStyle.primary, label="⏮️")
        self.custom_view = view

    async def callback(self, interaction: discord.Interaction):
        self.custom_view.current_page = (self.custom_view.current_page - 1) % len(self.custom_view.pages)
        await interaction.response.edit_message(embed=self.custom_view.pages[self.custom_view.current_page], view=self.custom_view)

class NextPageButton(Button):
    def __init__(self, view):
        super().__init__(style=discord.ButtonStyle.primary, label="⏭️")
        self.custom_view = view

    async def callback(self, interaction: discord.Interaction):
        self.custom_view.current_page = (self.custom_view.current_page + 1) % len(self.custom_view.pages)
        await interaction.response.edit_message(embed=self.custom_view.pages[self.custom_view.current_page], view=self.custom_view)

class PageButton(Button):
    def __init__(self, view):
        super().__init__(style=discord.ButtonStyle.primary, label="...")

@commands.command(name='classes', aliases=['listclass'])
async def classes(ctx):
    c.execute('''
        SELECT c.category_name, cl.class_name
        FROM category c
        LEFT JOIN class_category cc ON c.category_id = cc.category_id
        LEFT JOIN classes cl ON cc.class_id = cl.class_id
        ORDER BY c.category_name, cl.class_name
    ''')
    categories = c.fetchall()
    if not categories:
        await send_embed(ctx, "**__```𝐍𝐄𝐍𝐇𝐔𝐌𝐀 𝐂𝐋𝐀𝐒𝐒𝐄 𝐄𝐍𝐂𝐎𝐍𝐓𝐑𝐀𝐃𝐀```__**", "- > **Nenhuma categoria ou classe registrada.**", discord.Color.red())
        return

    pages = []
    current_category = None
    description = ""
    unlinked_classes = []

    for category_name, class_name in categories:
        if category_name != current_category:
            if current_category is not None and description:
                embed = discord.Embed(title=f"𝐂𝐋𝐀𝐒𝐒𝐄𝐒 𝐍𝐀 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀: {current_category}", description=description)
                pages.append(embed)
                description = ""
            current_category = category_name
        if class_name:
            description += f"- {class_name}\n"
        else:
            description += "- 𝐍𝐄𝐍𝐇𝐔𝐌𝐀 𝐂𝐋𝐀𝐒𝐒𝐄\n"

    if description:
        embed = discord.Embed(title=f"𝐂𝐋𝐀𝐒𝐒𝐄𝐒 𝐍𝐀 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀: {current_category}", description=description)
        pages.append(embed)

    c.execute('''
        SELECT cl.class_name
        FROM classes cl
        LEFT JOIN class_category cc ON cl.class_id = cc.class_id
        WHERE cc.class_id IS NULL
        ORDER BY cl.class_name
    ''')
    unlinked_classes = [class_name for (class_name,) in c.fetchall()]
    if unlinked_classes:
        unlinked_description = "\n".join(f"- {class_name}" for class_name in unlinked_classes)
        embed = discord.Embed(title="𝐂𝐋𝐀𝐒𝐒𝐄𝐒 𝐍𝐀̃𝐎 𝐕𝐈𝐍𝐂𝐔𝐋𝐀𝐃𝐀𝐒", description=unlinked_description)
        pages.append(embed)

    page = 0
    view = ClassListView(pages, page)
    await ctx.send(embed=pages[page], view=view)

@commands.command(name='showclass', aliases=['classinfo'])
async def showclass(ctx, *, class_name: str):
    c.execute('''
        SELECT class_name, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia
        FROM classes
        WHERE class_name = ?
    ''', (class_name,))
    class_info = c.fetchone()
    if not class_info:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Classe __{class_name}__ não encontrada.**", discord.Color.red())
        return

    class_name, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia = class_info
    description = (
        f"# — • ***[*** __𝐀𝐓𝐓𝐑𝐈𝐁𝐔𝐓𝐄𝐒__ ***]*** • —\n"
        f"- ``` . . . ```\n"
        f"- 𝐒𝐓𝐑𝐄𝐍𝐆𝐓𝐇 ***[*** ` {forca} ` ***]***\n"
        f"- 𝐑𝐄𝐒𝐈𝐒𝐓𝐀𝐍𝐂𝐄 ***[*** ` {resistencia} ` ***]***\n"
        f"- 𝐀𝐆𝐈𝐋𝐈𝐓𝐘 ***[*** ` {agilidade} ` ***]***\n"
        f"- 𝐒𝐄𝐍𝐒𝐄𝐒 ***[*** ` {sentidos} ` ***]***\n"
        f"- 𝐕𝐈𝐓𝐀𝐋𝐈𝐓𝐘 ***[*** ` {vitalidade} ` ***]***\n"
        f"- 𝐈𝐍𝐓𝐄𝐋𝐋𝐈𝐆𝐄𝐍𝐂𝐄 ***[*** ` {inteligencia} ` ***]***\n"
        f"- ``` . . . ```"
    )

    embed = discord.Embed(title=f"𝐃𝐄𝐓𝐀𝐋𝐇𝐄𝐒 𝐃𝐀 𝐂𝐋𝐀𝐒𝐒𝐄: {class_name}", description=description)
    await ctx.send(embed=embed)

@commands.has_permissions(administrator=True)
@commands.command(name='category', aliases=['classcategory'])
async def category(ctx, *, category_name: str):
    try:
        c.execute("INSERT INTO category (category_name) VALUES (?)", (category_name,))
        conn.commit()
        await send_embed(ctx, "𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀 𝐂𝐑𝐈𝐀𝐃𝐀", f'> **Categoria __{category_name}__ criada com sucesso.**', discord.Color.green())
    except sqlite3.IntegrityError:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Esta categoria já está registrada.**", discord.Color.red())

@commands.has_permissions(administrator=True)
@commands.command(name='removecategory', aliases=['delclasscategory'])
async def removecategory(ctx, *, category_name: str):
    c.execute("SELECT category_id FROM category WHERE category_name=?", (category_name,))
    category = c.fetchone()
    if not category:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Categoria não encontrada.**", discord.Color.red())
        return
    category_id = category[0]
    c.execute("DELETE FROM class_category WHERE category_id=?", (category_id,))
    c.execute("DELETE FROM category WHERE category_id=?", (category_id,))
    conn.commit()
    await send_embed(ctx, "𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐀", f'- > **Categoria __{category_name}__ e suas vinculações foram removidas com sucesso.**', discord.Color.green())

@commands.has_permissions(administrator=True)
@commands.command(name='vinculate', aliases=['linkclass'])
async def vinculate(ctx, *, args: str):
    match = re.match(r"'(.+?)'\s*'(.+?)'", args)
    if not match:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Formato inválido.**\n **Use: kill!vinculate 'Nome da Classe' 'Nome da Categoria'**", discord.Color.red())
        return
    class_name, category_name = match.groups()
    c.execute("SELECT class_id FROM classes WHERE class_name=?", (class_name,))
    class_id = c.fetchone()
    if not class_id:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Classe '{class_name}' não encontrada.**", discord.Color.red())
        return
    class_id = class_id[0]
    c.execute("SELECT category_id FROM category WHERE category_name=?", (category_name,))
    category_id = c.fetchone()
    if not category_id:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Categoria '{category_name}' não encontrada.**", discord.Color.red())
        return
    category_id = category_id[0]
    try:
        c.execute("INSERT INTO class_category (class_id, category_id) VALUES (?, ?)", (class_id, category_id))
        conn.commit()
        await send_embed(ctx, "𝐂𝐋𝐀𝐒𝐒𝐄 𝐕𝐈𝐍𝐂𝐔𝐋𝐀𝐃𝐀", f'- > **Classe __`{class_name}`__ vinculada à categoria __`{category_name}`__ com sucesso.**', discord.Color.green())
    except sqlite3.IntegrityError:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Esta classe já está vinculada a esta categoria.**", discord.Color.red())

@commands.command(name='assignclass', aliases=['setclass'])
async def assignclass(ctx, *, args: str):
    character_name, class_tokens = parse_assign_args(args)
    if not character_name or not class_tokens:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Formato inválido. Use: kill!assignclass 'Nome do Personagem' ClassePrincipal [SubClasse1] [SubClasse2]**", discord.Color.red())
        return

    c.execute("""
        SELECT c.character_id, p.forca, p.resistencia, p.agilidade, p.sentidos, p.vitalidade, p.inteligencia
        FROM characters c
        JOIN character_progression p ON c.character_id = p.character_id
        WHERE c.name COLLATE NOCASE=? AND c.user_id=?
    """, (character_name, ctx.author.id))
    character_row = c.fetchone()
    if not character_row:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Personagem '{character_name}' não encontrado ou você não tem permissão para atribuir classes.**", discord.Color.red())
        return

    character_id, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia = character_row

    slots = get_class_slots(character_id)
    max_slots = int(slots.get("main", 1)) + int(slots.get("sub", 2))
    if len(class_tokens) > max_slots:
        await send_embed(
            ctx,
            "**__```𝐄𝐑𝐑𝐎```__**",
            f"- > **Quantidade de classes invalida para este personagem. Limite atual: {max_slots} (main={slots.get('main', 1)}, sub={slots.get('sub', 2)}).**",
            discord.Color.red(),
        )
        return

    assignment_schema = get_class_assignment_schema(character_id)
    input_roles = assignment_schema["input_roles"]
    stored_columns = assignment_schema["stored_columns"]

    c.execute("SELECT main_class, sub_class1, sub_class2 FROM characters_classes WHERE character_id=?", (character_id,))
    current_classes = c.fetchone()

    if current_classes:
        for idx, current_class in enumerate(current_classes):
            if not current_class:
                continue
            role = input_roles[idx] if idx < len(input_roles) else "sub_secondary"
            role_multiplier = get_class_role_multiplier(role)
            c.execute(
                "SELECT forca, resistencia, agilidade, sentidos, vitalidade, inteligencia FROM classes WHERE class_name=?",
                (current_class,),
            )
            class_attrs = c.fetchone()
            if not class_attrs:
                continue

            forca -= class_attrs[0] * role_multiplier
            resistencia -= class_attrs[1] * role_multiplier
            agilidade -= class_attrs[2] * role_multiplier
            sentidos -= class_attrs[3] * role_multiplier
            vitalidade -= class_attrs[4] * role_multiplier
            inteligencia -= class_attrs[5] * role_multiplier

    for idx, selected_class in enumerate(class_tokens[:len(input_roles)]):
        role = input_roles[idx]
        role_multiplier = get_class_role_multiplier(role)
        c.execute(
            "SELECT forca, resistencia, agilidade, sentidos, vitalidade, inteligencia FROM classes WHERE class_name=?",
            (selected_class,),
        )
        selected_attrs = c.fetchone()
        if not selected_attrs:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Classe '{selected_class}' não encontrada.**", discord.Color.red())
            return

        forca += selected_attrs[0] * role_multiplier
        resistencia += selected_attrs[1] * role_multiplier
        agilidade += selected_attrs[2] * role_multiplier
        sentidos += selected_attrs[3] * role_multiplier
        vitalidade += selected_attrs[4] * role_multiplier
        inteligencia += selected_attrs[5] * role_multiplier

    store_values = [None, None, None]
    for idx, selected_class in enumerate(class_tokens[:len(stored_columns)]):
        store_values[idx] = selected_class

    c.execute('''
        UPDATE character_progression
        SET forca = ?, resistencia = ?, agilidade = ?, sentidos = ?, vitalidade = ?, inteligencia = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE character_id = ?
    ''', (int(round(forca)), int(round(resistencia)), int(round(agilidade)), int(round(sentidos)), int(round(vitalidade)), int(round(inteligencia)), character_id))

    c.execute("DELETE FROM characters_classes WHERE character_id=?", (character_id,))
    c.execute("INSERT INTO characters_classes (character_id, main_class, sub_class1, sub_class2, user_id) VALUES (?, ?, ?, ?, ?)",
              (character_id, store_values[0], store_values[1], store_values[2], ctx.author.id))
    conn.commit()

    selected_text = ", ".join(class_tokens[:len(input_roles)])
    await send_embed(ctx, "𝐂𝐋𝐀𝐒𝐒𝐄 𝐀𝐓𝐑𝐈𝐁𝐔𝐈́𝐃𝐀", f"- > **Classes atribuídas ao personagem __{character_name}__: {selected_text}. Slots atuais: main={slots.get('main', 1)}, sub={slots.get('sub', 2)}.**", discord.Color.green())
    
async def setup(bot):
    bot.add_command(registerclass)
    bot.add_command(removeclass)
    bot.add_command(classes)
    bot.add_command(showclass)
    bot.add_command(category)
    bot.add_command(removecategory)
    bot.add_command(vinculate)
    bot.add_command(assignclass)
