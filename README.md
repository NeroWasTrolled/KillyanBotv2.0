# KillyanBot v2.0

KillyanBot e um bot de Discord para gerenciamento de RPG em servidor, com foco em cadastro e evolucao de personagens, controle de inventario, tecnicas, classes e progressao por XP.

O projeto combina comandos por prefixo e slash commands para oferecer uma experiencia completa tanto para jogadores quanto para administradores.

## Funcionalidades

- Cadastro, consulta e remocao de personagens.
- Visualizacao detalhada de status, atributos, classe, subclasses e rank.
- Sistema de inventario com itens, descricao e imagem.
- Sistema de tecnicas com dominio, XP e rank.
- Sistema de classes e categorias para organizacao de build.
- Progressao de nivel com distribuicao de pontos de atributo.
- Controle de privacidade dos personagens por usuario.
- Layout personalizado de titulo e descricao para embeds.

## Estrutura do Projeto

- main.py: inicializacao do bot, banco SQLite, comandos slash e sincronizacao.
- register.py: comandos de personagens por prefixo.
- inventory.py: comandos de inventario.
- tecnicas.py: comandos de tecnicas.
- classes.py e category.py: sistema de classes e categorias.
- xp.py: logica de experiencia, nivel e pontos.
- logs.py e image_skill.py: modulos auxiliares.

## Tecnologias

- Python 3.10
- discord.py (API do Discord)
- SQLite (arquivo local characters.db)
- aiohttp

## Requisitos

- Python 3.10 instalado
- Token de bot do Discord

Dependencias principais em requirements.txt e pyproject.toml.

## Como Rodar Localmente

1. Clone o repositorio.
2. Crie e ative um ambiente virtual.
3. Instale as dependencias:

```bash
pip install -r requirements.txt
```

4. Configure o token do bot:

Opcao A: variavel de ambiente

```bash
DISCORD_TOKEN=seu_token_aqui
```

Opcao B: arquivo .env na raiz do projeto

```env
DISCORD_TOKEN=seu_token_aqui
```

5. Execute o bot:

```bash
python main.py
```

## Banco de Dados

O bot usa SQLite local no arquivo characters.db.

As tabelas sao criadas automaticamente na inicializacao (personagens, inventario, tecnicas, classes, categorias, layout e afins).

## Observacoes

- O projeto utiliza layouts visuais personalizados para embeds.
- Alguns comandos exigem permissao de administrador.
- Recomendado testar em servidor de desenvolvimento antes de usar em producao.

## Licenca

Defina aqui a licenca do projeto (exemplo: MIT).


