import discord
from discord.ext import commands
from discord import app_commands
import logs 
from discord.ui import Button, View, Modal, TextInput
import sqlite3
import aiohttp
import math
import os

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix=['kill!', 'Kill!'], intents=intents)

conn = sqlite3.connect('characters.db')
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON")

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
            category_id INTEGER,
            FOREIGN KEY(category_id) REFERENCES abilities(category_id) ON DELETE SET NULL,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        )''',
        
        '''CREATE TABLE IF NOT EXISTS abilities (
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
            FOREIGN KEY(category_id) REFERENCES category(category_id) ON DELETE CASCADE, 
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

        '''ALTER TABLE inventory ADD COLUMN message_id INTEGER DEFAULT NULL''',

        '''ALTER TABLE abilities ADD COLUMN description TEXT''',
        '''ALTER TABLE abilities ADD COLUMN character_id INTEGER'''
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

    migrate_abilities_schema()

    conn.commit()


def migrate_abilities_schema():
    # Migra a tabela antiga categories para abilities sem perder dados.
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
    has_categories = c.fetchone() is not None
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='abilities'")
    has_abilities = c.fetchone() is not None

    if has_categories and not has_abilities:
        c.execute("ALTER TABLE categories RENAME TO abilities")
        return

    if has_categories and has_abilities:
        c.execute("""
            INSERT INTO abilities (category_id, character_id, category_name, description)
            SELECT c.category_id, c.character_id, c.category_name, c.description
            FROM categories c
            WHERE NOT EXISTS (
                SELECT 1 FROM abilities a WHERE a.category_id = c.category_id
            )
        """)
        c.execute("DROP TABLE categories")

create_tables()

def apply_layout(user_id, title, description):
    """Aplica o layout personalizado do usuário ao título e descrição"""
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

def to_bold_sans_serif(text):
    """Converte texto para bold sans-serif Unicode"""
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

async def send_embed(ctx, title, description, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


async def sync_slash_commands(guild_id: int | None = None):
    if guild_id:
        guild = discord.Object(id=guild_id)

        # Remove comandos de guild para evitar duplicacao com os globais.
        bot.tree.clear_commands(guild=guild)
        removed_guild = await bot.tree.sync(guild=guild)
        print(f"Slash de guild limpos no servidor {guild_id}: {len(removed_guild)}")

    synced_global = await bot.tree.sync()
    print(f"Slash global sincronizados: {len(synced_global)}")


def build_assist_pages():
    return [
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

        discord.Embed(title="``` 𝐀𝐉𝐔𝐃𝐀 - 𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄𝐒 ```", description="""
        **__𝐂𝐑𝐈𝐀𝐑 𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄__**
        `kill!createability 'Nome do Personagem' 'Nome da Habilidade'`
        - > **Cria uma nova habilidade para o personagem especificado.**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄__**
        `kill!delability 'Nome do Personagem' 'Nome da Habilidade'`
        - > **Remove a habilidade do personagem especificado.**

        **__𝐋𝐈𝐒𝐓𝐀𝐑 𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄𝐒__**
        `kill!listabilities 'Nome do Personagem'`
        - > **Lista todas as habilidades associadas ao personagem especificado.**

        **__𝐃𝐄𝐓𝐀𝐋𝐇𝐄𝐒 𝐃𝐀 𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄__**
        `kill!abilitydetails 'Nome do Personagem' 'Nome da Habilidade'`
        - > **Mostra os detalhes da habilidade e técnicas vinculadas.**

        **__𝐕𝐈𝐍𝐂𝐔𝐋𝐀𝐑 𝐓𝐄𝐂𝐍𝐈𝐂𝐀 𝐀 𝐔𝐌𝐀 𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄__**
        `kill!assignability 'Nome do Personagem' 'Nome da Técnica' 'Nome da Habilidade'`
        - > **Vincula uma técnica do personagem a uma habilidade.**

        **__𝐂𝐎𝐌𝐏𝐀𝐓𝐈𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄__**
        `kill!createcategory`, `kill!delcategory`, `kill!listcategories`, `kill!categorydetails`, `kill!assigntechnique`
        - > **Os comandos antigos continuam funcionando como alias.**
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

        **__𝐀𝐓𝐈𝐕𝐀𝐑 𝐋𝐄𝐈𝐓𝐔𝐑𝐀 𝐃𝐄 𝐖𝐄𝐁𝐇𝐎𝐎𝐊𝐒__**
        `kill!activate`
        - > **Ativa ou desativa a leitura de webhooks para progressão automática de técnicas.**

        **__𝐂𝐀𝐑𝐃 𝐃𝐀 𝐇𝐀𝐁𝐈𝐋𝐈𝐃𝐀𝐃𝐄 (image.png)__**
        `kill!showability NomeDoPersonagem NomeDaTecnica`
        - > **Gera a imagem da técnica usando o template `image.png`.**
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


def assist_topic_map():
    return {
        'personagem': 0,
        'personagens': 0,
        'habilidade': 1,
        'habilidades': 1,
        'xp': 2,
        'nivel': 2,
        'inventario': 3,
        'item': 3,
        'classe': 4,
        'classes': 4,
        'tecnica': 5,
        'tecnicas': 5,
        'layout': 6,
    }


def build_menu_embed_and_view():
    embed = discord.Embed(
        title="𝐌𝐄𝐍𝐔 𝐑𝐏 𝐑𝐀́𝐏𝐈𝐃𝐎",
        description=(
            "Escolha uma área para receber os comandos principais de uso diário.\n\n"
            "- **Personagem**\n"
            "- **Inventário**\n"
            "- **Técnicas**\n"
            "- **Habilidades**\n"
            "- **Pendências**"
        ),
        color=discord.Color.blurple()
    )

    view = View(timeout=120)

    person_button = Button(label="Personagem", style=discord.ButtonStyle.secondary)
    inv_button = Button(label="Inventário", style=discord.ButtonStyle.secondary)
    tech_button = Button(label="Técnicas", style=discord.ButtonStyle.secondary)
    abil_button = Button(label="Habilidades", style=discord.ButtonStyle.secondary)
    pend_button = Button(label="Pendências", style=discord.ButtonStyle.success)

    async def person_cb(interaction):
        await interaction.response.send_message(
            "`kill!register` | `kill!details` | `kill!list` | `kill!rename` | `kill!avatar`",
            ephemeral=True,
        )

    async def inv_cb(interaction):
        await interaction.response.send_message(
            "`kill!additem` | `kill!inv` | `kill!showitem` | `kill!consumeitem` | `kill!delitem`",
            ephemeral=True,
        )

    async def tech_cb(interaction):
        await interaction.response.send_message(
            "`kill!addtechnique` | `kill!showtechnique` | `kill!assignability` | `kill!activate` | `kill!showability`",
            ephemeral=True,
        )

    async def abil_cb(interaction):
        await interaction.response.send_message(
            "`kill!createability` | `kill!listabilities` | `kill!abilitydetails` | `kill!delability`",
            ephemeral=True,
        )

    async def pend_cb(interaction):
        await interaction.response.send_message("Use `kill!pendencias NomeDoPersonagem`", ephemeral=True)

    person_button.callback = person_cb
    inv_button.callback = inv_cb
    tech_button.callback = tech_cb
    abil_button.callback = abil_cb
    pend_button.callback = pend_cb

    view.add_item(person_button)
    view.add_item(inv_button)
    view.add_item(tech_button)
    view.add_item(abil_button)
    view.add_item(pend_button)

    return embed, view

@bot.command(name='assist', aliases=['ajuda'])
async def assist(ctx, *, tema: str = None):
    pages = build_assist_pages()
    topic_map = assist_topic_map()

    if tema:
        page_index = topic_map.get(tema.lower())
        if page_index is None:
            await ctx.send("- > **Tema não reconhecido. Use:** `kill!assist personagens|habilidades|xp|inventario|classes|tecnicas|layout`")
            return
        await ctx.send(embed=pages[page_index])
        return

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


@bot.command(name='menu', aliases=['rp', 'atalhos'])
async def menu(ctx):
    embed, view = build_menu_embed_and_view()
    await ctx.send(embed=embed, view=view)


@bot.tree.command(name='assist', description='Mostra a ajuda geral ou por tema')
@app_commands.describe(tema='personagens, habilidades, xp, inventario, classes, tecnicas ou layout')
async def assist_slash(interaction: discord.Interaction, tema: str = None):
    pages = build_assist_pages()
    topic_map = assist_topic_map()

    if tema:
        page_index = topic_map.get(tema.lower())
        if page_index is None:
            embed = discord.Embed(
                title="**__```𝐄𝐑𝐑𝐎```__**",
                description="- > **Tema não reconhecido. Use: personagens, habilidades, xp, inventario, classes, tecnicas, layout.**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.send_message(embed=pages[page_index], ephemeral=True)
        return

    await interaction.response.send_message(
        embed=pages[0],
        ephemeral=True,
    )


@bot.tree.command(name='menu', description='Mostra o menu rápido de atalhos do RP')
async def menu_slash(interaction: discord.Interaction):
    embed, view = build_menu_embed_and_view()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name='showrankings', description='Exibe o top 10 por nivel')
async def show_rankings_slash(interaction: discord.Interaction):
    c.execute("SELECT name, level FROM characters ORDER BY level DESC LIMIT 10")
    rankings = c.fetchall()

    if not rankings:
        embed = discord.Embed(
            title="**__𝐓𝐎𝐏 𝟏𝟎 𝐉𝐎𝐆𝐀𝐃𝐎𝐑𝐄𝐒__**",
            description="- > **Nenhum ranking encontrado no momento.**",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    ranking_message = "\n".join([f"**{i+1}.** __{rank[0]}__ - Nível: **{rank[1]}**" for i, rank in enumerate(rankings)])
    embed = discord.Embed(
        title="**__𝐓𝐎𝐏 𝟏𝟎 𝐉𝐎𝐆𝐀𝐃𝐀𝐃𝐎𝐑𝐄𝐒__**",
        description=f"- > **Aqui estão os 10 melhores jogadores por nível:**\n\n{ranking_message}",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name='find', description='Procura personagens por nome')
@app_commands.describe(name='Nome completo ou parcial do personagem')
async def find_slash(interaction: discord.Interaction, name: str):
    c.execute("SELECT character_id, name, user_id, image_url, message_count, registered_at FROM characters WHERE name LIKE ?", (f'%{name}%',))
    results = c.fetchall()

    filtered_results = [
        result for result in results
        if not c.execute("SELECT private FROM characters WHERE user_id=? LIMIT 1", (result[2],)).fetchone()[0]
        or interaction.user.id == result[2]
    ]

    if not filtered_results:
        embed = discord.Embed(
            title="**__```𝐍𝐄𝐍𝐇𝐔𝐌 𝐄𝐍𝐂𝐎𝐍𝐓𝐑𝐀𝐃𝐎```__**",
            description=f"- > **Nenhum personagem com o nome \"{name}\" foi encontrado.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    preview = filtered_results[:10]
    lines = []
    for _, char_name, user_id, _, message_count, registered_at in preview:
        user_display_name = f"USER ID: {user_id}"
        user = bot.get_user(user_id)
        if user:
            user_display_name = user.name
        lines.append(
            f"**{char_name}**\n"
            f"𝐔𝐒𝐄𝐑: {user_display_name}\n"
            f"𝐌𝐄𝐒𝐒𝐀𝐆𝐄𝐒 𝐒𝐄𝐍𝐓: {message_count}\n"
            f"𝐑𝐄𝐆𝐈𝐒𝐓𝐄𝐑𝐄𝐃: {registered_at}"
        )

    description = "\n\n".join(lines)
    embed = discord.Embed(
        title="**__```𝐑𝐄𝐒𝐔𝐋𝐓𝐀𝐃𝐎𝐒```__**",
        description=f"- > {description}",
        color=discord.Color.dark_grey()
    )
    if len(filtered_results) > 10:
        embed.set_footer(text=f"Mostrando 10 de {len(filtered_results)} resultados.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='private', description='Alterna visibilidade dos seus personagens')
async def private_slash(interaction: discord.Interaction):
    user_id = interaction.user.id
    c.execute("SELECT private FROM characters WHERE user_id=?", (user_id,))
    private_status = c.fetchone()

    if private_status:
        new_status = 1 - private_status[0]
        c.execute("UPDATE characters SET private=? WHERE user_id=?", (new_status, user_id))
        conn.commit()
        status_text = "𝐏𝐑𝐈𝐕𝐀𝐃𝐎𝐒" if new_status == 1 else "𝐏𝐔́𝐁𝐋𝐈𝐂𝐎𝐒"
        embed = discord.Embed(
            title="**__```𝐒𝐓𝐀𝐓𝐔𝐒 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐎```__**",
            description=f"- > **Seus personagens agora estão {status_text}.**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="**__```𝐀𝐕𝐈𝐒𝐎```__**",
            description="- > **Sem personagens registrados.**",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='settitle', description='Define seu layout de titulo personalizado')
@app_commands.describe(layout='Template com {title}')
async def set_title_layout_slash(interaction: discord.Interaction, layout: str):
    user_id = interaction.user.id
    c.execute(
        """
        INSERT INTO layout_settings (user_id, title_layout)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET title_layout=excluded.title_layout
        """,
        (user_id, layout),
    )
    conn.commit()
    embed = discord.Embed(
        title="**__```𝐋𝐀𝐘𝐎𝐔𝐓 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐎```__**",
        description=f"- > **Layout de título atualizado para:**\n```{layout}```",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='setdesc', description='Define seu layout de descricao personalizado')
@app_commands.describe(layout='Template com {description}')
async def set_description_layout_slash(interaction: discord.Interaction, layout: str):
    user_id = interaction.user.id
    c.execute(
        """
        INSERT INTO layout_settings (user_id, description_layout)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET description_layout=excluded.description_layout
        """,
        (user_id, layout),
    )
    conn.commit()
    embed = discord.Embed(
        title="**__```𝐋𝐀𝐘𝐎𝐔𝐓 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐎```__**",
        description=f"- > **Layout de descrição atualizado para:**\n```{layout}```",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='register', description='Registra um novo personagem')
@app_commands.describe(name='Nome do personagem', image_url='URL opcional da imagem')
async def register_slash(interaction: discord.Interaction, name: str, image_url: str = None):
    c.execute("SELECT 1 FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (name, interaction.user.id))
    if c.fetchone():
        embed = discord.Embed(
            title="**__```𝐍𝐎𝐌𝐄 𝐄𝐌 𝐔𝐒𝐎```__**",
            description="- > **Você já tem um personagem com esse nome.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    c.execute(
        "INSERT INTO characters (name, image_url, user_id) VALUES (?, ?, ?)",
        (name, image_url, interaction.user.id)
    )
    conn.commit()

    embed = discord.Embed(
        title="**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐃𝐎!!!```__**",
        description=f'- > **Personagem __{name}__ registrado com sucesso!**\n\n- > **Próximo passo:** use `kill!details {name}` para ver o perfil',
        color=discord.Color.green()
    )
    if image_url:
        embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='remove', description='Remove um personagem seu')
@app_commands.describe(name='Nome do personagem')
async def remove_slash(interaction: discord.Interaction, name: str):
    c.execute("DELETE FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (name, interaction.user.id))
    if c.rowcount == 0:
        embed = discord.Embed(
            title="**__```𝐄𝐑𝐑𝐎```__**",
            description="- > **Personagem não encontrado ou você não tem permissão para removê-lo.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    conn.commit()
    embed = discord.Embed(
        title="**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐀```__**",
        description=f'- > **Personagem __{name}__ removido com sucesso.**\n\n- > **Próximo passo:** use `kill!register` para criar outro',
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='details', description='Mostra detalhes do personagem')
@app_commands.describe(name='Nome do personagem')
async def details_slash(interaction: discord.Interaction, name: str):
    c.execute(
        "SELECT character_id, name, image_url, experience, level, points, rank, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia FROM characters WHERE name COLLATE NOCASE=? AND user_id=?",
        (name, interaction.user.id)
    )
    row = c.fetchone()
    if not row:
        embed = discord.Embed(
            title="**__```𝐄𝐑𝐑𝐎```__**",
            description="- > **Personagem não encontrado ou você não tem permissão para visualizá-lo.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    character_id, char_name, image_url, experience, level, points, rank, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia = row
    c.execute("SELECT main_class, sub_class1, sub_class2 FROM characters_classes WHERE character_id=?", (character_id,))
    classes = c.fetchone() or (None, None, None)
    main_class, sub_class1, sub_class2 = classes

    points_info = f"{points}" if points > 0 else "𝐍𝐎𝐍𝐄"
    
    description = (
        f"``` 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍 ```- — ◇\n"
        f"> **__𝐍𝐀𝐌𝐄__**\n"
        f"● *{char_name}*\n"
        f"> **__𝐋𝐄𝐕𝐄𝐋__**\n"
        f"● *{level}*\n"
        f"> **__𝐄𝐗𝐏__**\n"
        f"○ *{experience}*\n"
        f"> **__𝐂𝐋𝐀𝐒𝐒__**\n"
        f"● *{main_class or '𝐍𝐎𝐍𝐄'}*\n"
        f"> **__𝐒𝐔𝐁𝐂𝐋𝐀𝐒𝐒__**\n"
        f"○ *{sub_class1 or '𝐍𝐎𝐍𝐄'}, {sub_class2 or '𝐍𝐎𝐍𝐄'}*\n\n"
        f"- — *[* **𝐏𝐎𝐈𝐍𝐓𝐒: ** ` {points_info} ` *]* —\n"
        f"● ○ ***[*** `𝐑𝐀𝐍𝐊 {rank}` ***]*** ○ ●"
    )

    embed = discord.Embed(title="``` 𝔻𝔼𝕿𝔸𝕴𝕷𝕾 ```", description=description, color=discord.Color.dark_grey())
    if image_url:
        embed.set_image(url=image_url)

    # Criar view com buttons
    view = discord.ui.View()
    
    button_status = discord.ui.Button(label="𝐒𝐓𝐀𝐓𝐔𝐒", style=discord.ButtonStyle.secondary, custom_id=f"status_{interaction.user.id}")
    button_inventory = discord.ui.Button(label="𝐈𝐍𝐕𝐄𝐍𝐓𝐎𝐑𝐘", style=discord.ButtonStyle.secondary, custom_id=f"inventory_{interaction.user.id}")
    button_techniques = discord.ui.Button(label="𝐓𝐄𝐂𝐇𝐍𝐈𝐐𝐔𝐄𝐒", style=discord.ButtonStyle.secondary, custom_id=f"techniques_{interaction.user.id}")

    async def button_status_callback(button_interaction):
        if button_interaction.user.id != interaction.user.id:
            await button_interaction.response.send_message("- > **Você não tem permissão.**", ephemeral=True)
            return
        
        status_description = (
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
        
        status_embed = discord.Embed(title="𝕾𝖙𝖆𝖋𝖚𝖘", description=status_description, color=discord.Color.dark_grey())
        
        button_back = discord.ui.Button(label="𝐃𝐄𝐓𝐀𝐈𝐋𝐒", style=discord.ButtonStyle.secondary)
        async def button_back_callback(back_interaction):
            if back_interaction.user.id != interaction.user.id:
                await back_interaction.response.send_message("- > **Você não tem permissão.**", ephemeral=True)
                return
            await back_interaction.response.edit_message(embed=embed, view=view)
        
        button_back.callback = button_back_callback
        back_view = discord.ui.View()
        back_view.add_item(button_back)
        
        await button_interaction.response.edit_message(embed=status_embed, view=back_view)

    button_status.callback = button_status_callback
    view.add_item(button_status)
    view.add_item(button_inventory)
    view.add_item(button_techniques)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name='list', description='Lista personagens do usuário')
@app_commands.describe(member='Usuário opcional para listar personagens')
async def list_slash(interaction: discord.Interaction, member: discord.Member = None):
    target_user = member.id if member else interaction.user.id

    c.execute("SELECT private FROM characters WHERE user_id=? LIMIT 1", (target_user,))
    private_status = c.fetchone()
    if private_status and private_status[0] == 1 and interaction.user.id != target_user:
        embed = discord.Embed(
            title="**__```𝐄𝐑𝐑𝐎```__**",
            description="- > **Os personagens deste usuário são privados.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    c.execute("SELECT name, level, rank FROM characters WHERE user_id=? ORDER BY level DESC", (target_user,))
    chars = c.fetchall()
    if not chars:
        embed = discord.Embed(
            title="**__```𝐊𝐎𝐍𝐇𝐔𝐌 𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐃𝐎```__**",
            description="- > **Nenhum personagem registrado.**",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    lines = [f"**{name}** - Nível {level} ({rank})" for name, level, rank in chars[:20]]
    embed = discord.Embed(
        title="**__```𝐋𝐈𝐒𝐓𝐀 𝐃𝐄 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐍𝐒```__**",
        description="\n".join(lines),
        color=discord.Color.dark_grey(),
    )
    if len(chars) > 20:
        embed.set_footer(text=f"Mostrando 20 de {len(chars)} personagens.")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='pendencias', description='Mostra pendências do personagem')
@app_commands.describe(name='Nome do personagem (opcional)')
async def pendencias_slash(interaction: discord.Interaction, name: str = None):
    if name:
        c.execute("SELECT character_id, name, points, level, limit_break, rank FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (name, interaction.user.id))
    else:
        c.execute("SELECT character_id, name, points, level, limit_break, rank FROM characters WHERE user_id=? ORDER BY level DESC LIMIT 1", (interaction.user.id,))

    character = c.fetchone()
    if not character:
        embed = discord.Embed(
            title="**__```𝐀𝐕𝐈𝐒𝐎```__**",
            description="- > **Nenhum personagem encontrado para verificar pendências.**",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    character_id, char_name, points, level, limit_break, rank = character
    pendencias_lista = []

    if points > 0:
        pendencias_lista.append(f"- Você tem **{points}** pontos para distribuir. (`kill!points {char_name} forca 1`)")

    c.execute("SELECT COUNT(*) FROM techniques WHERE character_id=? AND category_id IS NULL", (character_id,))
    sem_habilidade = c.fetchone()[0]
    if sem_habilidade > 0:
        pendencias_lista.append(f"- Você tem **{sem_habilidade}** técnica(s) sem habilidade. (`kill!assignability '{char_name}' 'Tecnica' 'Habilidade'`)")

    c.execute("SELECT COUNT(*) FROM inventory WHERE character_name COLLATE NOCASE=? AND user_id=?", (char_name, interaction.user.id))
    itens = c.fetchone()[0]
    rank_capacities = {
        'F-': 4, 'F': 8, 'F+': 12, 'E-': 16, 'E': 20, 'E+': 24,
        'D-': 28, 'D': 32, 'D+': 36, 'C-': 40, 'C': 44, 'C+': 48,
        'B-': 52, 'B': 56, 'B+': 60, 'A-': 64, 'A': 68, 'A+': 72,
        'S': 76, 'S+': 80, 'SS': 84, 'SS+': 88, 'SSS': 92, 'SSS+': 96, 'Z': 100
    }
    cap = rank_capacities.get(rank, 4)
    if cap - itens <= 2:
        pendencias_lista.append(f"- Inventário quase cheio: **{itens}/{cap}**.")

    if level >= limit_break:
        pendencias_lista.append(f"- Você atingiu o limitador de nível (**{limit_break}**). Use `kill!evolve {char_name}`.")

    if not pendencias_lista:
        embed = discord.Embed(
            title="**__```𝐀𝐑𝐄𝐍𝐀𝐃𝐎```__**",
            description=f"- > **{char_name} está em dia.**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(
        title=f"**__```𝐏𝐄𝐍𝐃𝐄̂𝐍𝐂𝐈𝐀𝐒 𝐃𝐄 {char_name.upper()}```__**",
        description="\n".join(pendencias_lista),
        color=discord.Color.orange(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='inv', description='Mostra o inventário do personagem')
@app_commands.describe(character_name='Nome do personagem')
async def inv_slash(interaction: discord.Interaction, character_name: str):
    c.execute("SELECT item_name, description FROM inventory WHERE character_name COLLATE NOCASE=? AND user_id=?", (character_name, interaction.user.id))
    items = c.fetchall()
    if not items:
        embed = discord.Embed(
            title="**__```𝐈𝐍𝐕𝐄𝐍𝐓𝐀́𝐑𝐈𝐎 𝐕𝐀𝐙𝐈𝐎```__**",
            description=f"- > **O inventário de {character_name} está vazio.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    c.execute("SELECT rank FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, interaction.user.id))
    character_rank = c.fetchone()
    if not character_rank:
        embed = discord.Embed(
            title="**__```𝐄𝐑𝐑𝐎```__**",
            description=f"- > **Personagem {character_name} não encontrado.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    rank = character_rank[0]
    capacity = 10 + (rank * 2)
    
    item_list = "\n".join([f"- {item[0]}: {item[1]}" for item in items])
    formatted_character_name = to_bold_sans_serif(character_name)
    
    embed = discord.Embed(
        title=f"𝐈𝐧𝐯𝐞𝐧𝐭𝐚́𝐫𝐢𝐨 𝐝𝐞 {formatted_character_name}",
        description=f"{item_list}\n\n𝐂𝐚𝐩𝐚𝐜𝐢𝐝𝐚𝐝𝐞: {len(items)}/{capacity} itens",
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='showitem', description='Mostra detalhes de um item do inventário')
@app_commands.describe(character_name='Nome do personagem', item_name='Nome do item')
async def showitem_slash(interaction: discord.Interaction, character_name: str, item_name: str):
    c.execute(
        "SELECT item_name, description, image_url FROM inventory WHERE character_name COLLATE NOCASE=? AND item_name COLLATE NOCASE=? AND user_id=?",
        (character_name, item_name, interaction.user.id)
    )
    item = c.fetchone()
    if not item:
        embed = discord.Embed(
            title="**__```𝐄𝐑𝐑𝐎```__**",
            description=f"- > **Item {item_name} não encontrado no inventário de {character_name}.**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    found_name, description, image_url = item
    formatted_title, formatted_description = apply_layout(interaction.user.id, found_name, description)
    embed = discord.Embed(title=formatted_title, description=formatted_description, color=discord.Color.blue())
    if image_url:
        embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='xp', description='Admin: adiciona XP a um personagem')
@app_commands.default_permissions(administrator=True)
@app_commands.describe(character_name='Nome do personagem', xp_amount='Quantidade de XP')
async def xp_slash(interaction: discord.Interaction, character_name: str, xp_amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sem permissão de administrador.", ephemeral=True)
        return

    c.execute("SELECT experience, level, points, limit_break, xp_multiplier FROM characters WHERE name=?", (character_name,))
    character = c.fetchone()
    if not character:
        await interaction.response.send_message(f"Personagem {character_name} não encontrado.", ephemeral=True)
        return

    experience, level, points, limit_break, xp_multiplier = character
    gained_xp = int(xp_amount * (xp_multiplier or 1.0))
    new_experience = experience + gained_xp

    def xp_for_next_level(local_level: int):
        return int(100 * local_level * math.log(local_level + 1))

    while level < 1000 and new_experience >= xp_for_next_level(level):
        new_experience -= xp_for_next_level(level)
        level += 1
        points += 3
        if level >= limit_break:
            new_experience = 0
            break

    c.execute("UPDATE characters SET experience=?, level=?, points=? WHERE name=?", (new_experience, level, points, character_name))
    conn.commit()
    await interaction.response.send_message(
        f"XP aplicado em **{character_name}**. Nível atual: **{level}**, XP atual: **{round(new_experience)}**, pontos: **{points}**.",
        ephemeral=True,
    )

@bot.command(name='showrankings', aliases=['ranking', 'top10'])
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

@bot.command(name='find', aliases=['buscar'])
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

@bot.command(name='private', aliases=['privado'])
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


@bot.command(name='syncslash')
@commands.has_permissions(administrator=True)
async def syncslash(ctx):
    if not ctx.guild:
        await ctx.send('- > **Use esse comando em um servidor.**')
        return

    await sync_slash_commands(ctx.guild.id)
    await ctx.send(f'- > **Slash commands sincronizados para este servidor (__{ctx.guild.id}__).**')

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

@bot.command(name='settitle', aliases=['titlelayout'])
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

@bot.command(name='setdesc', aliases=['desclayout'])
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

    guild_id = None
    guild_env = os.getenv('DISCORD_GUILD_ID')
    if guild_env and guild_env.isdigit():
        guild_id = int(guild_env)

    await sync_slash_commands(guild_id)

bot.setup_hook = setup_hook

import register
register.register_commands(bot)

def load_bot_token():
    token = os.getenv('DISCORD_TOKEN')
    if token:
        return token

    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                if key.strip() == 'DISCORD_TOKEN':
                    return value.strip().strip('"').strip("'")

    raise RuntimeError('Token nao encontrado. Defina DISCORD_TOKEN no ambiente ou no arquivo .env')


bot.run(load_bot_token())

conn.close()