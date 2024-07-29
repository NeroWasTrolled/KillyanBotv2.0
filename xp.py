import sqlite3
import random
from discord.ext import commands
import discord

conn = sqlite3.connect('characters.db')
c = conn.cursor()

RANKS = {
    'F-': 1, 'F': 3, 'F+': 10, 'E-': 25, 'E': 50, 'E+': 75,
    'D-': 100, 'D': 150, 'D+': 200, 'C-': 250, 'C': 300, 'C+': 350,
    'B-': 400, 'B': 450, 'B+': 500, 'A-': 550, 'A': 600, 'A+': 650,
    'S': 700, 'S+': 750, 'SS': 800, 'SS+': 850, 'SSS': 900, 'SSS+': 950, 'Z': 1000
}

rank_up_levels = {
    1: 'F-', 15: 'F', 30: 'F+', 45: 'E-', 60: 'E', 75: 'E+',
    90: 'D-', 105: 'D', 120: 'D+', 135: 'C-', 150: 'C', 165: 'C+',
    180: 'B-', 195: 'B', 210: 'B+', 225: 'A-', 240: 'A', 255: 'A+',
    270: 'S', 285: 'S+', 300: 'SS', 315: 'SS+', 330: 'SSS', 345: 'SSS+', 360: 'Z'
}

def xp_for_next_level(level):
    return int(100 * (1.1 ** (level - 1)))

def set_random_limit_break(current_level):
    return random.randint(current_level + 1, current_level + 14)

def update_experience_and_level(character_name, user_id, xp_to_add):
    c.execute("SELECT experience, level, points, limit_break FROM characters WHERE name=? AND user_id=?", (character_name, user_id))
    character = c.fetchone()
    if character:
        experience, level, points, limit_break = character
        if level == limit_break:
            return experience, level, points, 0, True 

        new_experience = experience + xp_to_add
        next_level_xp = xp_for_next_level(level)
        levels_gained = 0

        while new_experience >= next_level_xp:
            new_experience -= next_level_xp
            level += 1
            points += 3  
            levels_gained += 1

            if level == limit_break:
                new_experience = 0  
                break

            next_level_xp = xp_for_next_level(level)

            if level in rank_up_levels:
                limit_break = set_random_limit_break(level)
                c.execute("UPDATE characters SET limit_break=? WHERE name=? AND user_id=?", (limit_break, character_name, user_id))
                break

        c.execute("UPDATE characters SET experience=?, level=?, points=? WHERE name=? AND user_id=?", (new_experience, level, points, character_name, user_id))
        conn.commit()
        return new_experience, level, points, levels_gained, False  
    return None, None, None, 0, False

def update_rank_and_attributes(character_name, user_id, new_rank):
    bonus = RANKS.get(new_rank, 0)
    c.execute("SELECT rank FROM characters WHERE name=? AND user_id=?", (character_name, user_id))
    current_rank = c.fetchone()[0]

    adjusted_attributes = [bonus] * 6

    c.execute('''UPDATE characters SET rank=?, forca=?, resistencia=?, agilidade=?, sentidos=?, vitalidade=?, inteligencia=?
                 WHERE name=? AND user_id=?''',
              (new_rank, *adjusted_attributes, character_name, user_id))
    conn.commit()

def set_level(character_name, user_id, new_level):
    c.execute("SELECT level FROM characters WHERE name=? AND user_id=?", (character_name, user_id))
    character = c.fetchone()
    if character:
        old_level = character[0]

        new_total_points = max((new_level - 1) * 3, 0)

        new_rank = None
        for lvl, rank in sorted(rank_up_levels.items(), reverse=True):
            if new_level >= lvl:
                new_rank = rank
                break

        new_rank_bonus = RANKS.get(new_rank, 0)
        updated_attributes = [new_rank_bonus] * 6

        c.execute('''UPDATE characters 
                     SET experience=?, level=?, points=?, rank=?, forca=?, resistencia=?, agilidade=?, sentidos=?, vitalidade=?, inteligencia=?
                     WHERE name=? AND user_id=?''',
                  (0, new_level, new_total_points, new_rank, 
                   updated_attributes[0], updated_attributes[1], updated_attributes[2], 
                   updated_attributes[3], updated_attributes[4], updated_attributes[5], 
                   character_name, user_id))
        conn.commit()

        return 0, new_level, new_total_points, new_rank
    return None, None, None, None

async def get_user_id_from_name(ctx, character_name):
    c.execute("SELECT user_id FROM characters WHERE name=?", (character_name,))
    user_ids = c.fetchall()
    if len(user_ids) > 1:
        await ctx.send(embed=discord.Embed(description=f"- > **O personagem __'{character_name}'__ existe para múltiplos usuários. Por favor, mencione o usuário específico.**", color=discord.Color.red()))
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=60.0)
            mentioned_users = msg.mentions
            if mentioned_users:
                return mentioned_users[0].id
            else:
                await ctx.send(embed=discord.Embed(description="- > **Usuário não mencionado. Operação cancelada.**", color=discord.Color.red()))
                return None
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(description="- > **Tempo esgotado. Operação cancelada.**", color=discord.Color.red()))
            return None
    elif user_ids:
        return user_ids[0][0]
    else:
        await ctx.send(embed=discord.Embed(description=f"- > **Personagem __'{character_name}'__ não encontrado.**", color=discord.Color.red()))
        return None

@commands.has_permissions(administrator=True)
@commands.command(name='xp')
async def xp(ctx, character_name: str, xp_amount: int):
    user_id = await get_user_id_from_name(ctx, character_name)
    if user_id:
        experience, level, points, levels_gained, at_limit_break = update_experience_and_level(character_name, user_id, xp_amount)
        if experience is not None:
            if at_limit_break:
                await ctx.send(embed=discord.Embed(description=f'- > **{character_name} atingiu o limitador de nível e não pode receber mais XP até quebrar o limitador.**', color=discord.Color.orange()))
            else:
                await ctx.send(embed=discord.Embed(description=f'- > **🎉 {character_name} recebeu __{xp_amount}__ XP e agora está no nível __{level}__ com __{experience}__ XP restante e __{points}__ pontos disponíveis.**', color=discord.Color.green()))
        else:
            await ctx.send(embed=discord.Embed(description=f'- > **Personagem __"{character_name}"__ não encontrado.**', color=discord.Color.red()))
            
@commands.has_permissions(administrator=True)
@commands.command(name='setlevel')
async def setlevel(ctx, character_name: str, level: int):
    user_id = await get_user_id_from_name(ctx, character_name)
    if user_id:
        experience, new_level, points, new_rank = set_level(character_name, user_id, level)
        if experience is not None:
            await ctx.send(embed=discord.Embed(
                description=f'- > **O nível de {character_name} foi ajustado para {new_level}. Experiência zerada e {points} pontos disponíveis. Novo rank: {new_rank}.**',
                color=discord.Color.green()
            ))
        else:
            await ctx.send(embed=discord.Embed(
                description=f'- > **Personagem "{character_name}" não encontrado.**',
                color=discord.Color.red()
            ))
            
@commands.has_permissions(administrator=True)
@commands.command(name='evolve')
async def evolve(ctx, character_name: str):
    user_id = await get_user_id_from_name(ctx, character_name)
    if user_id:
        c.execute("SELECT level, limit_break FROM characters WHERE name=? AND user_id=?", (character_name, user_id))
        character = c.fetchone()
        if character:
            level, limit_break = character
            if level == limit_break:
                next_limit_break = set_random_limit_break(level)
                c.execute("UPDATE characters SET limit_break=? WHERE name=? AND user_id=?", (next_limit_break, character_name, user_id)) 
                conn.commit()
                await ctx.send(embed=discord.Embed(description=f'- > **🎉 __{character_name}__ quebrou o limitador de nível e pode continuar evoluindo! Próximo limitador em __{next_limit_break}__.**', color=discord.Color.green()))
            elif level in rank_up_levels:
                new_rank = rank_up_levels[level]
                update_rank_and_attributes(character_name, user_id, new_rank)
                next_limit_break = set_random_limit_break(level)
                c.execute("UPDATE characters SET experience=?, limit_break=? WHERE name=? AND user_id=?", (0, next_limit_break, character_name, user_id)) 
                conn.commit()
                await ctx.send(embed=discord.Embed(description=f'- > **🎉 __{character_name}__ evoluiu para o rank __{new_rank}__! Próximo limitador em __{next_limit_break}__.**', color=discord.Color.green()))
            else:
                await ctx.send(embed=discord.Embed(description=f'- > **😡 __{character_name}__ não está no nível para evoluir ou quebrar um limitador!**', color=discord.Color.red()))
        else:
            await ctx.send(embed=discord.Embed(description=f'- > **😡 Personagem __"{character_name}"__ não encontrado.**', color=discord.Color.red()))

@commands.command(name='points')
async def points(ctx, character_name: str, attribute: str, points: int):
    valid_attributes = ["forca", "resistencia", "agilidade", "sentidos", "vitalidade", "inteligencia"]
    if attribute.lower() not in valid_attributes:
        await ctx.send(embed=discord.Embed(description=f'- > **Atributo inválido. Os atributos válidos são: {", ".join(valid_attributes)}.**', color=discord.Color.red()))
        return

    c.execute("SELECT points, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
    character = c.fetchone()
    if not character:
        await ctx.send(embed=discord.Embed(description=f'- > **Personagem __"{character_name}"__ não encontrado ou você não tem permissão para distribuir pontos.**', color=discord.Color.red()))
        return

    current_points, *attrs = character
    if points > current_points:
        await ctx.send(embed=discord.Embed(description=f'- > **Você não tem pontos suficientes. Pontos disponíveis: __{current_points}__.**', color=discord.Color.red()))
        return

    updated_attributes = dict(zip(valid_attributes, attrs))
    updated_attributes[attribute.lower()] += points
    current_points -= points

    c.execute('''UPDATE characters SET points=?, forca=?, resistencia=?, agilidade=?, sentidos=?, vitalidade=?, inteligencia=?
                 WHERE name COLLATE NOCASE=? AND user_id=?''',
              (current_points, *updated_attributes.values(), character_name, ctx.author.id))
    conn.commit()

    await ctx.send(embed=discord.Embed(description=f'- > **🎉 __{points}__ pontos distribuídos para __{attribute}__ de __{character_name}__. Pontos restantes: __{current_points}__.**', color=discord.Color.green()))

async def setup(bot):
    bot.add_command(xp)
    bot.add_command(setlevel)
    bot.add_command(evolve)
    bot.add_command(points)
