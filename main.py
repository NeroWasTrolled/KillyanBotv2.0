import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import sqlite3
import aiohttp
import math

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix=['kill!', 'Kill!'], intents=intents)

conn = sqlite3.connect('characters.db')
c = conn.cursor()

def create_tables():
    queries = [
        '''CREATE TABLE IF NOT EXISTS characters (
            character_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT COLLATE NOCASE NOT NULL, 
            prefix TEXT NOT NULL, 
            image_url TEXT, 
            user_id INTEGER NOT NULL, 
            experience INTEGER DEFAULT 0, 
            level INTEGER DEFAULT 1,
            points INTEGER DEFAULT 0, 
            forca INTEGER DEFAULT 1, 
            resistencia INTEGER DEFAULT 1, 
            agilidade INTEGER DEFAULT 1, 
            sentidos INTEGER DEFAULT 1, 
            vitalidade INTEGER DEFAULT 1, 
            inteligencia INTEGER DEFAULT 1, 
            rank TEXT DEFAULT 'F-', 
            message_count INTEGER DEFAULT 0, 
            registered_at TEXT DEFAULT CURRENT_TIMESTAMP, 
            private INTEGER DEFAULT 0,
            webhook_url TEXT,
            message_id INTEGER
        )''',
        '''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            character_id INTEGER,
            item_name TEXT,
            description TEXT,
            image_url TEXT,
            user_id INTEGER,
            message_id INTEGER,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        )''',
        '''CREATE TABLE IF NOT EXISTS techniques (
            character_id INTEGER, 
            technique_name TEXT COLLATE NOCASE, 
            xp INTEGER DEFAULT 0, 
            mastery INTEGER DEFAULT 0, 
            user_id INTEGER,
            image_url TEXT, 
            description TEXT, 
            usage_count INTEGER DEFAULT 0,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        )''',
        '''CREATE TABLE IF NOT EXISTS classes (
            class_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            class_name TEXT UNIQUE,
            forca INTEGER DEFAULT 0, 
            resistencia INTEGER DEFAULT 0, 
            agilidade INTEGER DEFAULT 0,
            sentidos INTEGER DEFAULT 0, 
            vitalidade INTEGER DEFAULT 0, 
            inteligencia INTEGER DEFAULT 0
        )''',
        '''CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            category_name TEXT UNIQUE
        )''',
        '''CREATE TABLE IF NOT EXISTS class_category (
            class_id INTEGER, 
            category_id INTEGER,
            FOREIGN KEY(class_id) REFERENCES classes(class_id) ON DELETE CASCADE,
            FOREIGN KEY(category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
            UNIQUE(class_id, category_id)
        )''',
        '''CREATE TABLE IF NOT EXISTS characters_classes (
            character_id INTEGER, 
            main_class TEXT, 
            sub_class1 TEXT, 
            sub_class2 TEXT,
            user_id INTEGER,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE,
            FOREIGN KEY(main_class) REFERENCES classes(class_name) ON DELETE SET NULL,
            FOREIGN KEY(sub_class1) REFERENCES classes(class_name) ON DELETE SET NULL,
            FOREIGN KEY(sub_class2) REFERENCES classes(class_name) ON DELETE SET NULL
        )'''
    ]
    for query in queries:
        c.execute(query)
    conn.commit()

create_tables()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='assist')
async def assist(ctx):
    pages = [
        discord.Embed(title="``` 𝐀𝐉𝐔𝐃𝐀 - 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐍𝐒 ```", description="""
        **__𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐑 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        `kill!register 'Nome do Personagem' Prefixo Text`
        - > **Registra um novo personagem com o nome, prefixo e imagem (opcional).**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        `kill!remove NomeDoPersonagem`
        - > **Remove o personagem especificado do banco de dados.**

        **__𝐋𝐈𝐒𝐓𝐀𝐑 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐍𝐒__**
        `kill!list [@Usuário]`
        - > **Lista todos os personagens registrados pelo usuário ou pelo usuário mencionado.**

        **__𝐆𝐄𝐑𝐄𝐍𝐂𝐈𝐀𝐑 𝐀𝐕𝐀𝐓𝐀𝐑__**
        `kill!avatar NomeDoPersonagem`
        - > **Mostra ou atualiza o avatar do personagem especificado. Se uma imagem estiver anexada, o avatar será atualizado.**

        **__𝐑𝐄𝐍𝐎𝐌𝐄𝐀𝐑 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        `kill!rename 'Nome Antigo' 'Nome Novo'`
        - > **Renomeia o personagem especificado.**

        **__𝐆𝐄𝐑𝐄𝐍𝐂𝐈𝐀𝐑 𝐏𝐑𝐄𝐅𝐈𝐗𝐎__**
        `kill!brackets NomeDoPersonagem NovoPrefixo`
        - > **Atualiza o prefixo do personagem especificado.**

        **__𝐃𝐄𝐓𝐀𝐋𝐇𝐄𝐒 𝐃𝐎 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        `kill!details NomeDoPersonagem`
        - > **Mostra detalhes do personagem, incluindo classes vinculadas, nível e experiência.**

        **__𝐏𝐑𝐈𝐕𝐀𝐓𝐈𝐙𝐀𝐑 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐍𝐒__**
        `kill!private`
        - > **Alterna o status de privacidade dos personagens do usuário entre privado e público.**

        **__𝐏𝐑𝐎𝐂𝐔𝐑𝐀𝐑 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        `kill!find NomeDoPersonagem`
        - > **Procura personagens pelo nome.**
        """, color=discord.Color.blue()),

        discord.Embed(title="``` 𝐀𝐉𝐔𝐃𝐀 - 𝐂𝐋𝐀𝐒𝐒𝐄𝐒 𝐄 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀𝐒 ```", description="""
        **__𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐑 𝐂𝐋𝐀𝐒𝐒𝐄__**
        `kill!register_class NomeDaClasse`
        - > **Registra uma nova classe (somente para administradores).**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐂𝐋𝐀𝐒𝐒𝐄__**
        `kill!remove_class NomeDaClasse`
        - > **Remove a classe especificada do banco de dados (somente para administradores).**

        **__𝐋𝐈𝐒𝐓𝐀𝐑 𝐂𝐋𝐀𝐒𝐒𝐄𝐒 𝐄 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀𝐒__**
        `kill!classes`
        - > **Lista todas as categorias e as classes vinculadas a elas.**

        **__𝐕𝐈𝐍𝐂𝐔𝐋𝐀𝐑 𝐂𝐋𝐀𝐒𝐒𝐄 𝐀 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        `kill!assign_class 'Nome do Personagem' ClassePrincipal [SubClasse1] [SubClasse2]`
        - > **Vincula uma ou mais classes a um personagem (somente para administradores).**

        **__𝐂𝐑𝐈𝐀𝐑 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀__**
        `kill!category NomeDaCategoria`
        - > **Cria uma nova categoria para organizar classes (somente para administradores).**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀__**
        `kill!remove_category NomeDaCategoria`
        - > **Remove uma categoria e desassocia todas as classes vinculadas a ela (somente para administradores).**

        **__𝐕𝐈𝐍𝐂𝐔𝐋𝐀𝐑 𝐂𝐋𝐀𝐒𝐒𝐄 𝐀 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀__**
        `kill!vinculate 'NomeDaClasse' 'NomeDaCategoria'`
        - > **Vincula uma classe a uma categoria (somente para administradores).**
        """, color=discord.Color.blue()),

        discord.Embed(title="``` 𝐀𝐉𝐔𝐃𝐀 - 𝐗𝐏 𝐄 𝐍𝐈́𝐕𝐄𝐈𝐒 ```", description="""
        **__𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐑 𝐗𝐏__**
        `kill!xp NomeDoPersonagem QuantidadeDeXP`
        - > **Adiciona a quantidade especificada de XP ao personagem (somente para administradores).**

        **__𝐃𝐄𝐅𝐈𝐍𝐈𝐑 𝐍𝐈́𝐕𝐄𝐋__**
        `kill!setlevel NomeDoPersonagem Nível`
        - > **Define o nível especificado para o personagem, ajustando a experiência para zero (somente para administradores).**

        **__𝐃𝐈𝐒𝐓𝐑𝐈𝐁𝐔𝐈𝐑 𝐏𝐎𝐍𝐓𝐎𝐒__**
        `kill!points NomeDoPersonagem NomeDoAtributo QuantidadeDePontos`
        - > **Distribui a quantidade especificada de pontos para o atributo do personagem (ex.: `kill!points Killyan forca 3`).**
        """, color=discord.Color.blue()),

        discord.Embed(title="``` 𝐀𝐉𝐔𝐃𝐀 - 𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎 ```", description="""
        **__𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐑 𝐈𝐓𝐄𝐌__**
        `kill!additem NomeDoPersonagem NomeDoItem`
        - > **Adiciona o item especificado ao inventário do personagem.**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐈𝐓𝐄𝐌__**
        `kill!removeitem NomeDoPersonagem NomeDoItem`
        - > **Remove o item especificado do inventário do personagem.**

        **__𝐋𝐈𝐒𝐓𝐀𝐑 𝐈𝐓𝐄𝐍𝐒__**
        `kill!inventory NomeDoPersonagem`
        - > **Lista todos os itens no inventário do personagem.**

        **__𝐃𝐄𝐓𝐀𝐋𝐇𝐄𝐒 𝐃𝐎 𝐈𝐓𝐄𝐌__**
        `kill!itemdetails NomeDoPersonagem NomeDoItem`
        - > **Mostra os detalhes do item especificado no inventário do personagem.**

        **__𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐑 𝐈𝐌𝐀𝐆𝐄𝐌 𝐃𝐎 𝐈𝐓𝐄𝐌__**
        `kill!pfpitem 'Nome do Personagem' 'Nome do Item'`
        - > **Atualiza ou adiciona uma imagem ao item especificado do personagem.**
        """, color=discord.Color.blue()),

        discord.Embed(title="``` 𝐀𝐉𝐔𝐃𝐀 - 𝐓𝐄𝐂𝐍𝐈𝐂𝐀𝐒 ```", description="""
        **__𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐑 𝐓𝐄𝐂𝐍𝐈𝐂𝐀__**
        `kill!addtechnique NomeDoPersonagem NomeDaTecnica`
        - > **Adiciona uma técnica ao personagem especificado.**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐓𝐄𝐂𝐍𝐈𝐂𝐀__**
        `kill!removetechnique NomeDoPersonagem NomeDaTecnica`
        - > **Remove a técnica especificada do personagem.**

        **__𝐌𝐎𝐒𝐓𝐑𝐀𝐑 𝐓𝐄𝐂𝐍𝐈𝐂𝐀__**
        `kill!showtechnique NomeDoPersonagem NomeDaTecnica`
        - > **Mostra os detalhes da técnica especificada do personagem.**
        """, color=discord.Color.blue())
    ]

    current_page = 0

    async def update_page(interaction):
        await interaction.response.edit_message(embed=pages[current_page], view=create_view())

    def create_view():
        view = View()
        prev_button = Button(label="⏮️", style=discord.ButtonStyle.primary)
        next_button = Button(label="⏭️", style=discord.ButtonStyle.primary)
        first_button = Button(label="⏪", style=discord.ButtonStyle.primary)
        last_button = Button(label="⏩", style=discord.ButtonStyle.primary)
        jump_button = Button(label="...", style=discord.ButtonStyle.primary)

        async def prev_button_callback(interaction):
            nonlocal current_page
            current_page = (current_page - 1) % len(pages)
            await update_page(interaction)

        async def next_button_callback(interaction):
            nonlocal current_page
            current_page = (current_page + 1) % len(pages)
            await update_page(interaction)

        async def first_button_callback(interaction):
            nonlocal current_page
            current_page = 0
            await update_page(interaction)

        async def last_button_callback(interaction):
            nonlocal current_page
            current_page = len(pages) - 1
            await update_page(interaction)

        async def jump_button_callback(interaction):
            modal = JumpToPageModal(len(pages), update_page)
            await interaction.response.send_modal(modal)

        prev_button.callback = prev_button_callback
        next_button.callback = next_button_callback
        first_button.callback = first_button_callback
        last_button.callback = last_button_callback
        jump_button.callback = jump_button_callback

        view.add_item(first_button)
        view.add_item(prev_button)
        view.add_item(jump_button)
        view.add_item(next_button)
        view.add_item(last_button)
        return view

    class JumpToPageModal(discord.ui.Modal):
        def __init__(self, total_pages, update_page_callback):
            super().__init__(title="Ir para página")
            self.total_pages = total_pages
            self.update_page_callback = update_page_callback

            self.page_number = discord.ui.TextInput(label="Número da página", style=discord.TextStyle.short)
            self.add_item(self.page_number)

        async def on_submit(self, interaction):
            nonlocal current_page
            try:
                page = int(self.page_number.value) - 1
                if 0 <= page < self.total_pages:
                    current_page = page
                    await self.update_page_callback(interaction)
                else:
                    await interaction.response.send_message(f"Número de página inválido. Digite um número entre 1 e {self.total_pages}.", ephemeral=True)
            except ValueError:
                await interaction.response.send_message("Por favor, digite um número válido.", ephemeral=True)

    await ctx.send(embed=pages[current_page], view=create_view())

@bot.command(name='private')
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
    for character_id, name, user_id, prefix, image_url, message_count, registered_at in results[start:end]:
        user_display_name = f"𝐔𝐒𝐄𝐑 𝐈𝐃: {user_id}"
        user = bot.get_user(user_id) or await bot.fetch_user(user_id)
        if user:
            user_display_name = user.name
        avatar_link = image_url if image_url else "𝐍𝐎 𝐀𝐕𝐀𝐓𝐀𝐑"
        result = (
            f"**{name}**\n"
            f"𝐔𝐒𝐄𝐑: {user_display_name}\n"
            f"𝐁𝐑𝐀𝐂𝐊𝐄𝐓𝐒: {prefix}\n"
            f"[𝐀𝐕𝐀𝐓𝐀𝐑]({avatar_link})\n"
            f"𝐌𝐄𝐒𝐒𝐀𝐆𝐄𝐒 𝐒𝐄𝐍𝐓: {message_count}\n"
            f"𝐑𝐄𝐆𝐈𝐒𝐓𝐄𝐑𝐄𝐃: {registered_at}\n"
        )
        result_list.append(result)

    embed.description = "\n".join(result_list)
    embed.set_footer(text=f"Page {page} of {total_pages}")
    return embed

@bot.command(name='find')
async def find(ctx, *, name: str):
    per_page = 10
    c.execute("SELECT character_id, name, user_id, prefix, image_url, message_count, registered_at FROM characters WHERE name LIKE ?", (f'%{name}%',))
    results = c.fetchall()
    filtered_results = [
        result for result in results if not c.execute("SELECT private FROM characters WHERE user_id=? LIMIT 1", (result[2],)).fetchone()[0] or ctx.author.id == result[2]
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

@bot.command(name='edit')
async def edit(ctx, *, new_content: str):
    if not ctx.message.reference:
        msg = await ctx.send("- > **Você precisa responder à mensagem do webhook que deseja editar.**")
        await asyncio.sleep(5)
        await msg.delete()
        return

    try:
        original_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except discord.errors.NotFound:
        msg = await ctx.send("- > **Não consegui encontrar a mensagem que você está tentando editar.**")
        await asyncio.sleep(5)
        await msg.delete()
        return

    if original_message.webhook_id:
        if isinstance(ctx.channel, discord.Thread):
            parent_channel = ctx.channel.parent
        else:
            parent_channel = ctx.channel

        c.execute("SELECT webhook_url FROM characters WHERE user_id=? AND webhook_url IS NOT NULL", (ctx.author.id,))
        webhook_urls = c.fetchall()
        if webhook_urls:
            webhook_urls = [url[0] for url in webhook_urls]
            webhooks = await parent_channel.webhooks()
            for webhook in webhooks:
                if webhook.id == original_message.webhook_id and webhook.url in webhook_urls:
                    c.execute("SELECT 1 FROM characters WHERE webhook_url=? AND user_id=?", (webhook.url, ctx.author.id))
                    if not c.fetchone():
                        msg = await ctx.send("- > **Você não pode editar esta mensagem porque não é sua ou não foi enviada por um webhook que você possui.**")
                        await asyncio.sleep(5)
                        await msg.delete()
                        return
                    async with aiohttp.ClientSession() as session:
                        webhook = discord.Webhook.from_url(webhook.url, session=session)
                        try:
                            if isinstance(ctx.channel, discord.Thread):
                                await webhook.edit_message(message_id=original_message.id, content=new_content, thread=ctx.channel)
                            else:
                                await webhook.edit_message(message_id=original_message.id, content=new_content)
                            await ctx.message.delete()  
                        except discord.errors.NotFound:
                            msg = await ctx.send("- > **Não consegui encontrar a mensagem para editar. Verifique se a mensagem ainda existe.**")
                            await asyncio.sleep(5)
                            await msg.delete()
                        return

    msg = await ctx.send("- > **Você não pode editar esta mensagem porque não é sua ou não foi enviada por um webhook que você possui.**")
    await asyncio.sleep(5)
    await msg.delete()

@bot.command(name='delete')
async def delete_message(ctx):
    if not ctx.message.reference:
        msg = await ctx.send("- > **Você precisa responder à mensagem do webhook que deseja deletar.**")
        await asyncio.sleep(5)
        await msg.delete()
        return

    try:
        original_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except discord.errors.NotFound:
        msg = await ctx.send("- > **Não consegui encontrar a mensagem que você está tentando deletar.**")
        await asyncio.sleep(5)
        await msg.delete()
        return

    if original_message.webhook_id:
        if isinstance(ctx.channel, discord.Thread):
            parent_channel = ctx.channel.parent
        else:
            parent_channel = ctx.channel

        c.execute("SELECT webhook_url FROM characters WHERE user_id=? AND webhook_url IS NOT NULL", (ctx.author.id,))
        webhook_urls = c.fetchall()
        if webhook_urls:
            webhook_urls = [url[0] for url in webhook_urls]
            webhooks = await parent_channel.webhooks()
            for webhook in webhooks:
                if webhook.id == original_message.webhook_id and webhook.url in webhook_urls:
                    async with aiohttp.ClientSession() as session:
                        webhook = discord.Webhook.from_url(webhook.url, session=session)
                        try:
                            await original_message.delete()
                            await ctx.message.delete()
                        except discord.errors.NotFound:
                            msg = await ctx.send("- > **Não consegui encontrar a mensagem para deletar. Verifique se a mensagem ainda existe.**")
                            await asyncio.sleep(5)
                            await msg.delete()
                        return

    msg = await ctx.send("- > **Você não pode deletar esta mensagem porque não é sua ou não foi enviada por um webhook que você possui.**")
    await asyncio.sleep(5)
    await msg.delete()

@commands.Cog.listener()
async def on_message(self, message):
    if message.author == self.bot.user:
        return

    c.execute("SELECT character_id, name, prefix, image_url, user_id FROM characters")
    characters = c.fetchall()

    character_data = {(prefix, user_id): (character_id, name, image_url) for character_id, name, prefix, image_url, user_id in characters}

    message_lines = message.content.split("\n")
    to_send = []
    should_delete = False
    current_character = None
    current_message = []
    reference_handled = False

    async def get_reply_header(reference):
        if reference and isinstance(reference.resolved, discord.Message):
            referenced_message = reference.resolved
            link = f"https://discord.com/channels/{referenced_message.guild.id}/{referenced_message.channel.id}/{referenced_message.id}"
            character_name = referenced_message.author.name
            user_mention = referenced_message.author.mention

            if referenced_message.webhook_id:
                c.execute("SELECT user_id FROM characters WHERE name=?", (character_name,))
                original_author_data = c.fetchone()
                if original_author_data:
                    original_author_id = original_author_data[0]
                    original_author = await self.bot.fetch_user(original_author_id)
                    if original_author:
                        user_mention = original_author.mention

            raw_content = referenced_message.clean_content.split("\n")
            raw_content = [line for line in raw_content if not line.strip().startswith(">")]
            raw_content = "\n".join(raw_content)
            truncated_content = raw_content[:100] + "..." if len(raw_content) > 100 else raw_content

            return f"> [𝐑𝐄𝐏𝐋𝐘 𝐓𝐎]({link}): @{character_name} 〔{user_mention}〕\n> {truncated_content}"

        return ""

    for line in message_lines:
        for (prefix, user_id), (character_id, name, image_url) in character_data.items():
            if line.startswith(prefix) and message.author.id == user_id:
                if current_message:
                    new_message_content = "\n".join(current_message).strip()
                    if new_message_content:
                        reply_header = ""
                        if not reference_handled:
                            reply_header = await get_reply_header(message.reference)
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
                reply_header = await get_reply_header(message.reference)
                reference_handled = True

            reply_content = f"{reply_header}\n{new_message_content}"
            to_send.append((current_character, reply_content, message.attachments))

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

        for (character_id, name, image_url), reply_content, attachments in to_send:
            if isinstance(message.channel, discord.Thread):
                await webhook.send(
                    content=reply_content,
                    username=name,
                    avatar_url=image_url,
                    allowed_mentions=discord.AllowedMentions(users=True),
                    suppress_embeds=True,
                    files=[await attachment.to_file() for attachment in attachments],
                    thread=message.channel
                )
            else:
                await webhook.send(
                    content=reply_content,
                    username=name,
                    avatar_url=image_url,
                    allowed_mentions=discord.AllowedMentions(users=True),
                    suppress_embeds=True,
                    files=[await attachment.to_file() for attachment in attachments]
                )

            webhook_url = webhook.url
            c.execute("UPDATE characters SET webhook_url=? WHERE character_id=?", (webhook_url, character_id))
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


async def setup_hook():
    await bot.load_extension('inventory')
    await bot.load_extension('xp')
    await bot.load_extension('classes')
    await bot.load_extension('tecnicas')

bot.setup_hook = setup_hook

import register
register.register_commands(bot)

bot.run('MTI2MTc2NTczMTEzODQwODYxMA.GSdysX.80VQSyAoOhZ2lgmv4O1CE3dnBLZZzA6VQgV_aM')

conn.close()