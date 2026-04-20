import discord
from discord import app_commands
from discord.ui import Button, View


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

        discord.Embed(title="𝐀𝐉𝐔𝐃𝐀 - 𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀𝐒", description="""
        **__𝐋𝐈𝐒𝐓𝐀𝐑 𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀𝐒 𝐃𝐄𝐅𝐈𝐍𝐈𝐃𝐀𝐒__**
        kill!charlistdefs
        - > **Lista todas as características disponíveis no sistema.**

        **__𝐋𝐈𝐒𝐓𝐀𝐑 𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀𝐒 𝐃𝐎 𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌__**
        kill!charlist 'Nome do Personagem'
        - > **Mostra as características atualmente aplicadas ao personagem.**

        **__𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐑 𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀__**
        kill!charadd 'Nome do Personagem'
        - > **Mostra as características disponíveis e aplica por número (somente para administradores).**

        **__𝐑𝐄𝐌𝐎𝐕𝐄𝐑 𝐂𝐀𝐑𝐀𝐂𝐓𝐄𝐑𝐈́𝐒𝐓𝐈𝐂𝐀__**
        kill!charremove 'Nome do Personagem' 'Nome da Característica'
        - > **Remove uma característica do personagem (somente para administradores).**
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

        discord.Embed(title="``` 𝐀𝐉𝐔𝐃𝐀 - 𝐒𝐎𝐔𝐋 𝐖𝐀𝐍𝐃𝐄𝐑𝐈𝐍𝐆 ```", description="""
        **__𝐑𝐀𝐂̧𝐀 (𝐒𝐋𝐀𝐒𝐇)__**
        /race character_name:<nome> action:view|set|evolve race:<opcional> stage:<opcional>
        - > **Mostra, define ou evolui o estágio racial do personagem.**

        **__𝐑𝐄𝐈𝐑𝐘𝐎𝐊𝐔 (𝐒𝐋𝐀𝐒𝐇)__**
        /reiryoku character_name:<nome>
        - > **Exibe estado atual do reservatório, estabilidade e pureza.**

        **__𝐑𝐄𝐈𝐀𝐓𝐒𝐔 (𝐒𝐋𝐀𝐒𝐇)__**
        /reiatsu character_name:<nome> action:view|set category:<opcional>
        - > **Mostra ou define a categoria principal de Reiatsu.**

        **__𝐀𝐖𝐀𝐊𝐄𝐍-𝐒𝐊𝐈𝐋𝐋 (𝐒𝐋𝐀𝐒𝐇)__**
        /awaken-skill character_name:<nome> skill_name:<Ten|Zetsu|...>
        - > **Desperta técnicas-base de Reiryoku.**

        **__𝐂𝐎𝐑𝐄 (𝐒𝐋𝐀𝐒𝐇)__**
        /core character_name:<nome>
        - > **Mostra os detalhes do núcleo de Reiryoku.**

        **__𝐒𝐎𝐔𝐋 𝐃𝐄𝐓𝐀𝐈𝐋𝐒 (𝐒𝐋𝐀𝐒𝐇)__**
        /soul_details character_name:<nome>
        - > **Exibe o painel completo do personagem no sistema Soul Wandering.**
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
        'caracteristica': 5,
        'caracteristicas': 5,
        'tecnica': 6,
        'tecnicas': 6,
        'soul': 7,
        'race': 7,
        'reiatsu': 7,
        'reiryoku': 7,
        'core': 7,
        'layout': 8,
    }


HELP_TOPIC_CHOICES = [
    app_commands.Choice(name='Personagens', value='personagens'),
    app_commands.Choice(name='Habilidades', value='habilidades'),
    app_commands.Choice(name='XP e Niveis', value='xp'),
    app_commands.Choice(name='Inventario', value='inventario'),
    app_commands.Choice(name='Classes', value='classes'),
    app_commands.Choice(name='Caracteristicas', value='caracteristicas'),
    app_commands.Choice(name='Tecnicas', value='tecnicas'),
    app_commands.Choice(name='Soul Wandering', value='soul'),
    app_commands.Choice(name='Layout', value='layout'),
]


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


async def _send_assist_prefix(ctx, tema: str | None = None):
    pages = build_assist_pages()
    topic_map = assist_topic_map()

    if tema:
        page_index = topic_map.get(tema.lower())
        if page_index is None:
            await ctx.send("- > **Tema não reconhecido. Use:** `kill!help personagens|habilidades|xp|inventario|classes|caracteristicas|tecnicas|soul|layout`")
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


async def _send_assist_slash(interaction: discord.Interaction, tema: str | None = None):
    pages = build_assist_pages()
    topic_map = assist_topic_map()

    if tema:
        page_index = topic_map.get(tema.lower())
        if page_index is None:
            embed = discord.Embed(
                title="**__```𝐄𝐑𝐑𝐎```__**",
                description="- > **Tema não reconhecido. Use: personagens, habilidades, xp, inventario, classes, caracteristicas, tecnicas, soul, layout.**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.send_message(embed=pages[page_index], ephemeral=True)
        return

    current_page = 0

    async def update_page(interaction: discord.Interaction):
        await interaction.response.edit_message(embed=pages[current_page], view=create_view())

    def create_view():
        view = View(timeout=120)
        prev_button = Button(label="⏮️", style=discord.ButtonStyle.secondary)
        next_button = Button(label="⏭️", style=discord.ButtonStyle.secondary)
        first_button = Button(label="⏪", style=discord.ButtonStyle.secondary)
        last_button = Button(label="⏩", style=discord.ButtonStyle.secondary)
        jump_button = Button(label="...", style=discord.ButtonStyle.secondary)

        async def prev_button_callback(interaction: discord.Interaction):
            nonlocal current_page
            current_page = (current_page - 1) % len(pages)
            await update_page(interaction)

        async def next_button_callback(interaction: discord.Interaction):
            nonlocal current_page
            current_page = (current_page + 1) % len(pages)
            await update_page(interaction)

        async def first_button_callback(interaction: discord.Interaction):
            nonlocal current_page
            current_page = 0
            await update_page(interaction)

        async def last_button_callback(interaction: discord.Interaction):
            nonlocal current_page
            current_page = len(pages) - 1
            await update_page(interaction)

        async def jump_button_callback(interaction: discord.Interaction):
            modal = SlashJumpToPageModal(len(pages), update_page)
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

    class SlashJumpToPageModal(discord.ui.Modal):
        def __init__(self, total_pages, update_page_callback):
            super().__init__(title="Ir para página")
            self.total_pages = total_pages
            self.update_page_callback = update_page_callback
            self.page_number = discord.ui.TextInput(label="Número da página", style=discord.TextStyle.short)
            self.add_item(self.page_number)

        async def on_submit(self, modal_interaction: discord.Interaction):
            nonlocal current_page
            try:
                page = int(self.page_number.value) - 1
                if 0 <= page < self.total_pages:
                    current_page = page
                    await self.update_page_callback(modal_interaction)
                else:
                    await modal_interaction.response.send_message(
                        f"Número de página inválido. Digite um número entre 1 e {self.total_pages}.",
                        ephemeral=True,
                    )
            except ValueError:
                await modal_interaction.response.send_message("Por favor, digite um número válido.", ephemeral=True)

    await interaction.response.send_message(embed=pages[current_page], view=create_view(), ephemeral=True)


def register_help_menu_commands(bot):
    @bot.command(name='help')
    async def help_alias(ctx, *, tema: str | None = None):
        await _send_assist_prefix(ctx, tema=tema)

    @bot.command(name='menu', aliases=['rp', 'atalhos'])
    async def menu(ctx):
        embed, view = build_menu_embed_and_view()
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    register_help_menu_commands(bot)
