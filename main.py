import discord
from discord.ext import commands
import logs 
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
            limit_break INTEGER DEFAULT 0,
            xp_multiplier REAL DEFAULT 1.0,
            message_id INTEGER DEFAULT NULL -- Coluna adicionada
        )''',

        '''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            character_id INTEGER,
            character_name TEXT, 
            item_name TEXT, 
            description TEXT, 
            image_url TEXT, 
            user_id INTEGER,
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
            passive TEXT DEFAULT 'Nenhuma', -- Adicionando passiva padrão como 'Nenhuma'
            rank TEXT DEFAULT 'F-', -- Adicionando rank padrão como 'F-'
            message_id INTEGER DEFAULT NULL, -- Adicionando message_id para referência de mensagem
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        )''',
        
        '''CREATE TABLE categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        character_id INTEGER NOT NULL,
        category_name TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE
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

        '''CREATE TABLE IF NOT EXISTS category (
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
        )''',

        '''CREATE TABLE IF NOT EXISTS rebirths (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            character_name TEXT COLLATE NOCASE, 
            user_id INTEGER, 
            rebirth_count INTEGER DEFAULT 0
        )''',

        '''CREATE TABLE IF NOT EXISTS layout_settings (
            user_id INTEGER PRIMARY KEY, 
            title_layout TEXT DEFAULT '╚╡ ⬥ {title} ⬥ ╞',
            description_layout TEXT DEFAULT '╚───► *「{description}」*'
        )'''
    ]

    alter_queries = [
        '''ALTER TABLE characters ADD COLUMN limit_break INTEGER DEFAULT 0''',
        '''ALTER TABLE characters ADD COLUMN xp_multiplier REAL DEFAULT 1.0''',
        '''ALTER TABLE characters ADD COLUMN message_id INTEGER DEFAULT NULL''',

        '''ALTER TABLE techniques ADD COLUMN passive TEXT DEFAULT 'Nenhuma' ''',
        '''ALTER TABLE techniques ADD COLUMN rank TEXT DEFAULT 'F-' ''',
        '''ALTER TABLE techniques ADD COLUMN message_id INTEGER DEFAULT NULL''',
        '''ALTER TABLE techniques ADD COLUMN category_id INTEGER''',
        '''ALTER TABLE techniques ADD FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE''',

        '''ALTER TABLE categories ADD COLUMN description TEXT''',
        '''ALTER TABLE categories ADD COLUMN character_id INTEGER''',
        '''ALTER TABLE categories ADD FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE'''
    ]

    for query in queries:
        try:
            c.execute(query)
        except sqlite3.Error as e:
            print(f"Erro ao criar tabela: {e}")

    for alter_query in alter_queries:
        try:
            c.execute(alter_query)
        except sqlite3.OperationalError:
            pass
        except sqlite3.Error as e:
            print(f"Erro ao alterar tabela: {e}")

    conn.commit()

create_tables()

async def send_embed(ctx, title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='assist')
async def assist(ctx):
    pages = [
        discord.Embed(title="``` 𝐀𝐉𝐔𝐃𝐀 - 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐍𝐒 ```", description="""
        **__𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐑 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        `kill!register 'Nome do Personagem'`
        - > **Registra um novo personagem com o nome e imagem (opcional).**

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

        **__𝐃𝐄𝐓𝐀𝐋𝐇𝐄𝐒 𝐃𝐎 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        `kill!details NomeDoPersonagem`
        - > **Mostra detalhes do personagem, incluindo classes vinculadas, nível e experiência.**

        **__𝐏𝐑𝐈𝐕𝐀𝐓𝐈𝐙𝐀𝐑 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐍𝐒__**
        `kill!private`
        - > **Alterna o status de privacidade dos personagens do usuário entre privado e público.**

        **__𝐏𝐑𝐎𝐂𝐔𝐑𝐀𝐑 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        `kill!find NomeDoPersonagem`
        - > **Procura personagens pelo nome.**

        **__𝐓𝐎𝐏 𝟏𝟎 𝐑𝐀𝐍𝐊𝐈𝐍𝐆__**
        `kill!showrankings`
        - > **Exibe o ranking dos 10 personagens com maior nível.**
        """, color=discord.Color.blue()),

        discord.Embed(title="``` 𝐀𝐉𝐔𝐃𝐀 - 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀𝐒 ```", description="""
        **__𝐂𝐑𝐈𝐀𝐑 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀__**
        `kill!createcategory 'Nome do Personagem' 'Nome da Categoria'`
        - > **Cria uma nova categoria para o personagem especificado.**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀__**
        `kill!removecategory 'Nome do Personagem' 'Nome da Categoria'`
        - > **Remove a categoria do personagem especificado.**

        **__𝐋𝐈𝐒𝐓𝐀𝐑 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀𝐒__**
        `kill!listcategories 'Nome do Personagem'`
        - > **Lista todas as categorias associadas ao personagem especificado.**

        **__𝐕𝐈𝐍𝐂𝐔𝐋𝐀𝐑 𝐓𝐄𝐂𝐍𝐈𝐂𝐀 𝐀 𝐔𝐌𝐀 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀__**
        `kill!assigntechnique 'Nome do Personagem' 'Nome da Técnica' 'Nome da Categoria'`
        - > **Vincula uma técnica do personagem a uma categoria.**
        """, color=discord.Color.blue()),

        discord.Embed(title="𝐀𝐉𝐔𝐃𝐀 - 𝐗𝐏 𝐄 𝐍𝐈́𝐕𝐄𝐈𝐒", description="""
        **__𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐑 𝐗𝐏__**
        kill!xp NomeDoPersonagem QuantidadeDeXP
        - > **Adiciona a quantidade especificada de XP ao personagem (somente para administradores).**

        **__𝐃𝐄𝐅𝐈𝐍𝐈𝐑 𝐍𝐈́𝐕𝐄𝐋__**
        kill!setlevel NomeDoPersonagem Nível
        - > **Define o nível especificado para o personagem, ajustando a experiência para zero (somente para administradores).**

        **__𝐃𝐈𝐒𝐓𝐑𝐈𝐁𝐔𝐈𝐑 𝐏𝐎𝐍𝐓𝐎𝐒__**
        kill!points NomeDoPersonagem NomeDoAtributo QuantidadeDePontos
        - > **Distribui a quantidade especificada de pontos para o atributo do personagem (ex.: kill!points Killyan forca 3).**

        **__𝐑𝐄𝐍𝐀𝐒𝐂𝐄𝐑 (𝐑𝐄𝐁𝐈𝐑𝐓𝐇)__**
        kill!rebirth NomeDoPersonagem
        - > **Permite que o personagem passe pelo processo de renascimento.** 
        - > **O renascimento redefine o personagem para o nível 1, mas o recompensa com benefícios como atributos ou habilidades extras.** 
        - > **É uma ótima maneira de continuar progredindo com o personagem, acumulando novas vantagens após alcançar certos marcos de nível.**
        """, color=discord.Color.blue()),

        discord.Embed(title="𝐀𝐉𝐔𝐃𝐀 - 𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎", description="""
        **__𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐑 𝐈𝐓𝐄𝐌__**
        kill!additem NomeDoPersonagem NomeDoItem
        - > **Adiciona o item especificado ao inventário do personagem.**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐈𝐓𝐄𝐌__**
        kill!delitem NomeDoPersonagem NomeDoItem
        - > **Remove o item especificado do inventário do personagem.**

        **__𝐋𝐈𝐒𝐓𝐀𝐑 𝐈𝐓𝐄𝐍𝐒__**
        kill!inv NomeDoPersonagem
        - > **Lista todos os itens no inventário do personagem.**

        **__𝐃𝐄𝐓𝐀𝐋𝐇𝐄𝐒 𝐃𝐎 𝐈𝐓𝐄𝐌__**
        kill!showitem NomeDoPersonagem NomeDoItem
        - > **Mostra os detalhes do item especificado no inventário do personagem.**

        **__𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐑 𝐈𝐌𝐀𝐆𝐄𝐌 𝐃𝐎 𝐈𝐓𝐄𝐌__**
        kill!pfpitem 'Nome do Personagem' 'Nome do Item'
        - > **Atualiza ou adiciona uma imagem ao item especificado do personagem.**

        **__𝐂𝐎𝐍𝐒𝐔𝐌𝐈𝐑 𝐈𝐓𝐄𝐌__**
        kill!consumeitem 'Nome do Personagem' 'Nome do Item'
        - > **Consome um item do inventário do personagem, removendo-o após o uso.**
        """, color=discord.Color.blue()),

        discord.Embed(title="𝐀𝐉𝐔𝐃𝐀 - 𝐂𝐋𝐀𝐒𝐒𝐄𝐒 𝐄 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀𝐒", description="""
        **__𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐑 𝐂𝐋𝐀𝐒𝐒𝐄__**
        kill!registerclass NomeDaClasse
        - > **Registra uma nova classe (somente para administradores).**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐂𝐋𝐀𝐒𝐒𝐄__**
        kill!removeclass NomeDaClasse
        - > **Remove a classe especificada do banco de dados (somente para administradores).**

        **__𝐋𝐈𝐒𝐓𝐀𝐑 𝐂𝐋𝐀𝐒𝐒𝐄𝐒 𝐄 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀𝐒__**
        kill!classes
        - > **Lista todas as categorias e as classes vinculadas a elas.**

        **__𝐕𝐈𝐍𝐂𝐔𝐋𝐀𝐑 𝐂𝐋𝐀𝐒𝐒𝐄 𝐀 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        kill!assignclass 'Nome do Personagem' ClassePrincipal [SubClasse1] [SubClasse2]
        - > **Vincula uma ou mais classes a um personagem.**

        **__𝐂𝐑𝐈𝐀𝐑 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀__**
        kill!category NomeDaCategoria
        - > **Cria uma nova categoria para organizar classes (somente para administradores).**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀__**
        kill!removecategory NomeDaCategoria
        - > **Remove uma categoria e desassocia todas as classes vinculadas a ela (somente para administradores).**

        **__𝐕𝐈𝐍𝐂𝐔𝐋𝐀𝐑 𝐂𝐋𝐀𝐒𝐒𝐄 𝐀 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀__**
        kill!vinculate 'NomeDaClasse' 'NomeDaCategoria'
        - > **Vincula uma classe a uma categoria (somente para administradores).**
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

        **__𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐑 𝐈𝐌𝐀𝐆𝐄𝐌 𝐃𝐀 𝐓𝐄𝐂𝐍𝐈𝐂𝐀__**
        `kill!pfptechnique 'Nome do Personagem' 'Nome da Técnica'`
        - > **Atualiza ou adiciona uma imagem à técnica especificada.**

        **__𝐃𝐄𝐅𝐈𝐍𝐈𝐑 𝐍𝐈́𝐕𝐄𝐋 𝐃𝐀 𝐓𝐄𝐂𝐍𝐈𝐂𝐀__**
        `kill!settechniquelevel NomeDoPersonagem NomeDaTecnica Nivel`
        - > **Define o nível de mastery de uma técnica específica (somente para administradores).**

        **__𝐃𝐄𝐅𝐈𝐍𝐈𝐑 𝐏𝐀𝐒𝐒𝐈𝐕𝐀__**
        `kill!setpassive NomeDoPersonagem NomeDaTecnica Passiva`
        - > **Define a passiva de uma técnica específica (somente para administradores).**
        """, color=discord.Color.blue()),

        discord.Embed(title="``` 𝐀𝐉𝐔𝐃𝐀 - 𝐋𝐀𝐘𝐎𝐔𝐓 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐋𝐈𝐙𝐀𝐃𝐎 ```", description="""
        **__𝐃𝐄𝐅𝐈𝐍𝐈𝐑 𝐋𝐀𝐘𝐎𝐔𝐓 𝐃𝐄 𝐓𝐈́𝐓𝐔𝐋𝐎__**
        `kill!settitle <layout personalizado>`
        - > **Define um layout personalizado para o título das suas categorias, técnicas e habilidades. Exemplo: `kill!settitle ╚╡ ⬥ {title} ⬥ ╞`.**

        **__𝐃𝐄𝐅𝐈𝐍𝐈𝐑 𝐋𝐀𝐘𝐎𝐔𝐓 𝐃𝐄 𝐃𝐄𝐒𝐂𝐑𝐈𝐂̧𝐀̃𝐎__**
        `kill!setdesc <layout personalizado>`
        - > **Define um layout personalizado para a descrição das suas categorias e habilidades. Exemplo: `kill!setdesc ╚───► *「{description}」*`.**

        **Dica**: Use as chaves `{title}` e `{description}` para marcar onde o título ou a descrição será inserido no layout.
        """, color=discord.Color.blue())
    ]

    current_page = 0

    async def update_page(interaction):
        await interaction.response.edit_message(embed=pages[current_page], view=create_view())

    def create_view():
        view = View()
        prev_button = Button(label="⏮️", style=discord.ButtonStyle.secondary)
        next_button = Button(label="⏭️", style=discord.ButtonStyle.secondary)
        first_button = Button(label="⏪", style=discord.ButtonStyle.secondary)
        last_button = Button(label="⏩", style=discord.ButtonStyle.secondary)
        jump_button = Button(label="...", style=discord.ButtonStyle.secondary)

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

@bot.command(name='showrankings')
async def show_rankings(ctx):
    c.execute("SELECT name, level FROM characters ORDER BY level DESC LIMIT 10")
    rankings = c.fetchall()

    if not rankings:
        await send_embed(ctx, "**__𝐄𝐑𝐑𝐎__**", "- > **Nenhum ranking encontrado no momento.**", discord.Color.red())
        return

    ranking_message = "\n".join([f"**{i+1}.** __{rank[0]}__ - Nível: **{rank[1]}**" for i, rank in enumerate(rankings)])

    title = "**__𝐓𝐎𝐏 𝟏𝟎 𝐉𝐎𝐆𝐀𝐃𝐎𝐑𝐄𝐒__**"
    description = f"- > **Aqui estão os 10 melhores jogadores por nível:**\n\n{ranking_message}"

    await send_embed(ctx, title, description, discord.Color.blue())

@bot.command(name='find')
async def find(ctx, *, name: str):
    per_page = 10
    c.execute("SELECT character_id, name, user_id, image_url, message_count, registered_at FROM characters WHERE name LIKE ?", (f'%{name}%',))
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
    for character_id, name, user_id, image_url, message_count, registered_at in results[start:end]:
        user_display_name = f"𝐔𝐒𝐄𝐑 𝐈𝐃: {user_id}"
        user = bot.get_user(user_id) or await bot.fetch_user(user_id)
        if user:
            user_display_name = user.name
        avatar_link = image_url if image_url else "𝐍𝐎 𝐀𝐕𝐀𝐓𝐀𝐑"
        result = (
            f"**{name}**\n"
            f"𝐔𝐒𝐄𝐑: {user_display_name}\n"
            f"[𝐀𝐕𝐀𝐓𝐀𝐑]({avatar_link})\n"
            f"𝐌𝐄𝐒𝐒𝐀𝐆𝐄𝐒 𝐒𝐄𝐍𝐓: {message_count}\n"
            f"𝐑𝐄𝐆𝐈𝐒𝐓𝐄𝐑𝐄𝐃: {registered_at}\n"
        )
        result_list.append(result)

    embed.description = "\n".join(result_list)
    embed.set_footer(text=f"Page {page} of {total_pages}")
    return embed

@bot.command(name='settitle')
async def set_title_layout(ctx, *, layout: str):
    user_id = ctx.author.id
    c.execute("""
        INSERT INTO layout_settings (user_id, title_layout) 
        VALUES (?, ?) 
        ON CONFLICT(user_id) 
        DO UPDATE SET title_layout=excluded.title_layout
    """, (user_id, layout))
    conn.commit()
    await ctx.send(f"- > **Layout de título atualizado para:**\n{layout}")

@bot.command(name='setdesc')
async def set_description_layout(ctx, *, layout: str):
    user_id = ctx.author.id
    c.execute("""
        INSERT INTO layout_settings (user_id, description_layout) 
        VALUES (?, ?) 
        ON CONFLICT(user_id) 
        DO UPDATE SET description_layout=excluded.description_layout
    """, (user_id, layout))
    conn.commit()
    await ctx.send(f"- > **Layout de descrição atualizado para:**\n{layout}")

async def setup_hook():
    await bot.load_extension('inventory')
    await bot.load_extension('xp')
    await bot.load_extension('classes')
    await bot.load_extension('tecnicas')
    await bot.load_extension('logs')
    await bot.load_extension('category')
    await bot.load_extension('image_skill')

bot.setup_hook = setup_hook

import register
register.register_commands(bot)

bot.run('')

conn.close()