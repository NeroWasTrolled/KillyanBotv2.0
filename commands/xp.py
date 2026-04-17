import sqlite3
import random
import discord
import re
import math  
import asyncio
from commands.logs import Logs
from discord.ext import commands
from database.connection import create_connection
from utils.common import sanitize_input, send_embed

conn = create_connection()
c = conn.cursor()

MAX_LEVEL = 1000
POINTS_PER_LEVEL = 3

RANKS = {
    'F-': 1, 'F': 3, 'F+': 10, 'E-': 25, 'E': 50, 'E+': 75,
    'D-': 100, 'D': 150, 'D+': 200, 'C-': 250, 'C': 300, 'C+': 350,
    'B-': 400, 'B': 450, 'B+': 500, 'A-': 550, 'A': 600, 'A+': 650,
    'S': 700, 'S+': 750, 'SS': 800, 'SS+': 850, 'SSS': 900, 'SSS+': 950, 'Z': 1000
}

RANK_UP_LEVELS = {
    1: 'F-', 15: 'F', 30: 'F+', 45: 'E-', 60: 'E', 75: 'E+',
    90: 'D-', 105: 'D', 120: 'D+', 135: 'C-', 150: 'C', 165: 'C+',
    180: 'B-', 195: 'B', 210: 'B+', 225: 'A-', 240: 'A', 255: 'A+',
    270: 'S', 285: 'S+', 300: 'SS', 315: 'SS+', 330: 'SSS', 345: 'SSS+', 360: 'Z'
}

def xp_for_next_level(level):
    base_xp = 100  
    return int(base_xp * level * math.log(level + 1))  

def points_per_level(level):
    base_points = 3  
    extra_points = int(math.log(level + 1))  
    return base_points + extra_points

def format_large_number(num):
    """ Formatar números grandes para torná-los mais legíveis. """
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B" 
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"  
    elif num >= 1_000:
        return f"{num / 1_000:.2f}K"  
    else:
        return str(num)

def set_random_limit_break(current_level, rebirth_count):
    base_distance = 10
    growth_factor = 1.2
    distance_between_limits = int(base_distance * (growth_factor ** rebirth_count))
    next_limit_break = current_level + distance_between_limits
    return next_limit_break

# ============================================================================
# HELPERS PARA NOVO SCHEMA
# ============================================================================

def get_character_by_name_and_user(character_name, user_id):
    """Helper para obter character_id pelo nome e user_id"""
    c.execute("SELECT character_id FROM characters WHERE name = ? COLLATE NOCASE AND user_id = ?", 
              (character_name, user_id))
    result = c.fetchone()
    return result[0] if result else None

def get_character_progression(character_id):
    """Helper para obter todos os dados de progressão"""
    c.execute("SELECT * FROM character_progression WHERE character_id = ?", (character_id,))
    return c.fetchone()

def update_experience_and_level(character_name, user_id, xp_to_add):
    """Atualizar XP e level - NOVO: usa character_progression"""
    
    character_id = get_character_by_name_and_user(character_name, user_id)
    if not character_id:
        return None, None, None, 0, False
    
    # Buscar dados de progressão (agora em character_progression)
    c.execute("""
        SELECT experience, level, points_available, limit_break, rank, xp_multiplier
        FROM character_progression
        WHERE character_id = ?
    """, (character_id,))
    
    prog_data = c.fetchone()
    if not prog_data:
        return None, None, None, 0, False

    experience, level, points, limit_break, rank, xp_multiplier = prog_data

    # Verifica se já atingiu nível máximo
    if level >= MAX_LEVEL:
        return experience, level, points, 0, True

    xp_to_add *= xp_multiplier
    new_experience = experience + xp_to_add
    levels_gained = 0

    # Loop para adicionar níveis
    while new_experience >= xp_for_next_level(level) and level < MAX_LEVEL:
        new_experience -= xp_for_next_level(level)
        level += 1
        points += POINTS_PER_LEVEL
        levels_gained += 1

        if level >= MAX_LEVEL:
            level = MAX_LEVEL
            new_experience = 0
            break

        if level >= limit_break:
            new_experience = 0
            break

    # UPDATE para character_progression (não characters!)
    c.execute("""
        UPDATE character_progression 
        SET experience=?, level=?, points_available=?, updated_at=CURRENT_TIMESTAMP
        WHERE character_id=?
    """, (new_experience, level, points, character_id))
    
    # Atualizar rank se mudou
    for lvl, new_rank in RANK_UP_LEVELS.items():
        if level >= lvl and new_rank != rank:
            update_rank_and_attributes(character_name, user_id, new_rank)
            break
    
    conn.commit()

    return new_experience, level, points, levels_gained, level >= limit_break

def update_rank_and_attributes(character_name, user_id, new_rank):
    """Atualizar rank e atributos - NOVO: usa character_progression"""
    
    character_id = get_character_by_name_and_user(character_name, user_id)
    if not character_id:
        return

    new_bonus = RANKS.get(new_rank, 0)
    
    c.execute("""
        SELECT rank, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia
        FROM character_progression
        WHERE character_id = ?
    """, (character_id,))
    
    prog_data = c.fetchone()
    if prog_data:
        current_rank, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia = prog_data
        current_bonus = RANKS.get(current_rank, 0)

        adjusted_attributes = {
            'forca': forca - current_bonus + new_bonus,
            'resistencia': resistencia - current_bonus + new_bonus,
            'agilidade': agilidade - current_bonus + new_bonus,
            'sentidos': sentidos - current_bonus + new_bonus,
            'vitalidade': vitalidade - current_bonus + new_bonus,
            'inteligencia': inteligencia - current_bonus + new_bonus
        }

        c.execute("""
            UPDATE character_progression
            SET rank=?, forca=?, resistencia=?, agilidade=?, sentidos=?, vitalidade=?, inteligencia=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE character_id=?
        """,
            (new_rank, adjusted_attributes['forca'], adjusted_attributes['resistencia'],
             adjusted_attributes['agilidade'], adjusted_attributes['sentidos'],
             adjusted_attributes['vitalidade'], adjusted_attributes['inteligencia'],
             character_id))
        conn.commit()

def set_level(character_name, user_id, new_level):
    """Definir nível específico - NOVO: usa character_progression"""
    
    if new_level > MAX_LEVEL:
        new_level = MAX_LEVEL

    character_id = get_character_by_name_and_user(character_name, user_id)
    if not character_id:
        return None, None, None, None

    c.execute("SELECT rebirth_count FROM rebirths WHERE character_name=? AND user_id=?", (character_name, user_id))
    rebirth_data = c.fetchone()
    rebirth_points = rebirth_data[0] * 5 if rebirth_data else 0

    c.execute("""
        SELECT main_class, sub_class1, sub_class2 FROM characters_classes
        WHERE character_id = ?
    """, (character_id,))
    classes = c.fetchone()

    class_points = calculate_class_attributes(*classes) if classes else [0, 0, 0, 0, 0, 0]

    new_total_points = max((new_level - 1) * POINTS_PER_LEVEL, 0) + rebirth_points

    new_rank = None
    for lvl, rank in sorted(RANK_UP_LEVELS.items(), reverse=True):
        if new_level >= lvl:
            new_rank = rank
            break

    if new_rank:
        new_rank_bonus = RANKS.get(new_rank, 0)
        updated_attributes = [new_rank_bonus + class_points[i] for i in range(6)]

        c.execute("""
            UPDATE character_progression
            SET experience=?, level=?, points_available=?, rank=?, forca=?, resistencia=?, 
                agilidade=?, sentidos=?, vitalidade=?, inteligencia=?, updated_at=CURRENT_TIMESTAMP
            WHERE character_id=?
        """,
            (0, new_level, new_total_points, new_rank,
             updated_attributes[0], updated_attributes[1], updated_attributes[2],
             updated_attributes[3], updated_attributes[4], updated_attributes[5],
             character_id))
        conn.commit()

        return 0, new_level, new_total_points, new_rank
    return None, None, None, None

def reset_character(character_name, user_id, bonus_points, xp_multiplier):
    """Reset character para rebirth - NOVO: usa character_progression"""
    initial_level = 1
    initial_experience = 0
    initial_rank = 'F-'
    initial_attributes = [1, 1, 1, 1, 1, 1]

    character_id = get_character_by_name_and_user(character_name, user_id)
    if not character_id:
        return

    c.execute("""
        SELECT main_class, sub_class1, sub_class2 FROM characters_classes
        WHERE character_id = ?
    """, (character_id,))
    classes = c.fetchone()
    bonus_attributes = calculate_class_attributes(*classes) if classes else [0] * 6

    final_attributes = [x + y for x, y in zip(initial_attributes, bonus_attributes)]

    c.execute("""
        UPDATE character_progression
        SET level=?, experience=?, points_available=?, rank=?, forca=?, resistencia=?, 
            agilidade=?, sentidos=?, vitalidade=?, inteligencia=?, xp_multiplier=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE character_id=?
    """,
        (initial_level, initial_experience, bonus_points, initial_rank,
         final_attributes[0], final_attributes[1], final_attributes[2],
         final_attributes[3], final_attributes[4], final_attributes[5],
         xp_multiplier, character_id))
    conn.commit()

def calculate_class_attributes(main_class, sub_class1, sub_class2):
    attributes = [0, 0, 0, 0, 0, 0]
    if main_class:
        c.execute("SELECT forca, resistencia, agilidade, sentidos, vitalidade, inteligencia FROM classes WHERE class_name=?", (main_class,))
        main_attrs = c.fetchone()
        if main_attrs:
            attributes = [x + y for x, y in zip(attributes, main_attrs)]

    if sub_class1:
        c.execute("SELECT forca, resistencia, agilidade, sentidos, vitalidade, inteligencia FROM classes WHERE class_name=?", (sub_class1,))
        sub1_attrs = c.fetchone()
        if sub1_attrs:
            attributes = [x + y // 2 for x, y in zip(attributes, sub1_attrs)] 

    if sub_class2:
        c.execute("SELECT forca, resistencia, agilidade, sentidos, vitalidade, inteligencia FROM classes WHERE class_name=?", (sub_class2,))
        sub2_attrs = c.fetchone()
        if sub2_attrs:
            attributes = [x + y // 4 for x, y in zip(attributes, sub2_attrs)]  

    return attributes

def apply_rebirth(character_name, user_id, current_level, rebirth_type):
    rebirth_count = get_rebirth_data(character_name, user_id)

    rebirth_thresholds = {
        'early': 25 + rebirth_count * 5,
        'intermediate': 50 + rebirth_count * 10,
        'late': 75 + rebirth_count * 15
    }

    rebirth_type = rebirth_type.lower()

    if current_level >= rebirth_thresholds[rebirth_type]:
        rebirth_count += 1
        c.execute("UPDATE rebirths SET rebirth_count=? WHERE character_name=? AND user_id=?", (rebirth_count, character_name, user_id))
        conn.commit()

        if rebirth_type == 'early':
            bonus_points = 5 + rebirth_count * 2
            xp_multiplier = 1.1 + (rebirth_count * 0.02)  
        elif rebirth_type == 'intermediate':
            bonus_points = 10 + rebirth_count * 3  
            xp_multiplier = 1.2 + (rebirth_count * 0.03) 
        elif rebirth_type == 'late':
            bonus_points = 20 + rebirth_count * 5 
            xp_multiplier = 1.3 + (rebirth_count * 0.05)  
        else:
            return None

        next_rebirth_levels = {
            'early': 25 + rebirth_count * 5,
            'intermediate': 50 + rebirth_count * 10,
            'late': 75 + rebirth_count * 15
        }

        return bonus_points, xp_multiplier, rebirth_count, next_rebirth_levels

    return None

def get_rebirth_data(character_name, user_id):
    c.execute("SELECT rebirth_count FROM rebirths WHERE character_name=? AND user_id=?", (character_name, user_id))
    result = c.fetchone()
    if result:
        return result[0]
    c.execute("INSERT INTO rebirths (character_name, user_id, rebirth_count) VALUES (?, ?, 0)", (character_name, user_id))
    conn.commit()
    return 0

async def get_user_id_from_name(ctx, character_name):
    c.execute("SELECT user_id FROM characters WHERE name=?", (character_name,))
    user_ids = c.fetchall()
    if len(user_ids) > 1:
        await send_embed(ctx, "**__```𝐀𝐌𝐁𝐈𝐆𝐔𝐈𝐃𝐀𝐃𝐄```__**", f"**- > O personagem __'{character_name}'__ existe para múltiplos usuários. Por favor, mencione o usuário específico.**", discord.Color.red())
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=60.0)
            mentioned_users = msg.mentions
            if mentioned_users:
                return mentioned_users[0].id
            await send_embed(ctx, "**__```𝐎𝐏𝐄𝐑𝐀𝐂̧𝐀̃𝐎 𝐂𝐀𝐍𝐂𝐄𝐋𝐀𝐃𝐀```__**", "- > **Usuário não mencionado. Operação cancelada.**", discord.Color.red())
            return None
        except asyncio.TimeoutError:
            await send_embed(ctx, "**__```𝐓𝐄𝐌𝐏𝐎 𝐄𝐒𝐆𝐎𝐓𝐀𝐃𝐎```__**", "- > **Tempo esgotado. Operação cancelada.**", discord.Color.red())
            return None
    elif user_ids:
        return user_ids[0][0]
    await send_embed(ctx, "**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐍𝐀̃𝐎 𝐄𝐍𝐂𝐎𝐍𝐓𝐑𝐀𝐃𝐎```__**", f"- > **Personagem __'{character_name}'__ não encontrado.**", discord.Color.red())
    return None

@commands.has_permissions(administrator=True)
@commands.command(name='xp', aliases=['addxp', 'xpadd'])
async def xp(ctx, character_name: str, xp_amount: int):
    user_id = await get_user_id_from_name(ctx, character_name)
    if user_id:
        experience, level, points, levels_gained, at_limit_break = update_experience_and_level(character_name, user_id, xp_amount)
        if experience is not None:
            if at_limit_break or level == MAX_LEVEL:
                await send_embed(ctx, "**__```𝐋𝐈𝐌𝐈𝐓𝐀𝐃𝐎𝐑 𝐀𝐓𝐈𝐍𝐆𝐈𝐃𝐎```__**", f'- > **{character_name} atingiu o limitador de nível ou o nível máximo ({MAX_LEVEL}) e não pode receber mais XP até evoluir.**', discord.Color.orange())
            else:
                await send_embed(ctx, "**__```𝐗𝐏 𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐃𝐎```__**", f'- > **{character_name} recebeu __{xp_amount}__ XP e agora está no nível __{level}__ com __{round(experience)}__ XP restante e __{points}__ pontos disponíveis.**', discord.Color.green(), next_step="use `kill!details NomeDoPersonagem` para revisar nível e pontos")
        else:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f'- > **Personagem __"{character_name}"__ não encontrado.**', discord.Color.red())

@commands.has_permissions(administrator=True)
@commands.command(name='setlevel', aliases=['lvlset'])
async def setlevel(ctx, character_name: str, level: int):
    if level < 1 or level > MAX_LEVEL:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **O nível deve ser um número inteiro entre 1 e {MAX_LEVEL}.**", discord.Color.red())
        return

    user_id = await get_user_id_from_name(ctx, character_name)
    if user_id:
        experience, new_level, points, new_rank = set_level(character_name, user_id, level)
        if experience is not None:
            await send_embed(ctx, "**__```𝐍𝐈́𝐕𝐄𝐋 𝐀𝐉𝐔𝐒𝐓𝐀𝐃𝐎```__**", f'- > **O nível de {character_name} foi ajustado para {new_level}. Experiência zerada e {points} pontos disponíveis. Novo rank: {new_rank}.**', discord.Color.green(), next_step="use `kill!evolve` caso tenha atingido requisito de evolução")
        else:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f'- > **Personagem "{character_name}" não encontrado.**', discord.Color.red())

@commands.has_permissions(administrator=True)
@commands.command(name='evolve', aliases=['up'])
async def evolve(ctx, character_name: str):
    user_id = await get_user_id_from_name(ctx, character_name)
    if user_id:
        character_id = get_character_by_name_and_user(character_name, user_id)
        c.execute("""
            SELECT level, limit_break, rank
            FROM character_progression
            WHERE character_id=?
        """, (character_id,))
        character = c.fetchone()
        if character:
            level, limit_break, rank = character
            rebirth_count = get_rebirth_data(character_name, user_id)
            if level >= limit_break:
                next_limit_break = set_random_limit_break(level, rebirth_count)
                c.execute(
                    "UPDATE character_progression SET limit_break=?, updated_at=CURRENT_TIMESTAMP WHERE character_id=?",
                    (next_limit_break, character_id)
                )
                conn.commit()
                await send_embed(ctx, "**__```𝐋𝐈𝐌𝐈𝐓𝐀𝐃𝐎𝐑 𝐐𝐔𝐄𝐁𝐑𝐀𝐃𝐎```__**", f'- > **__{character_name}__ quebrou o limitador de nível e pode continuar evoluindo! Próximo limitador em __{next_limit_break}__.**', discord.Color.green(), next_step="use `kill!xp` para continuar evoluindo")
            elif level in RANK_UP_LEVELS and RANK_UP_LEVELS[level] != rank:
                new_rank = RANK_UP_LEVELS[level]
                update_rank_and_attributes(character_name, user_id, new_rank)
                next_limit_break = set_random_limit_break(level, rebirth_count)
                c.execute(
                    """
                    UPDATE character_progression
                    SET experience=?, rank=?, limit_break=?, updated_at=CURRENT_TIMESTAMP
                    WHERE character_id=?
                    """,
                    (0, new_rank, next_limit_break, character_id)
                )
                conn.commit()
                await send_embed(ctx, "**__```𝐑𝐀𝐍𝐊 𝐄𝐕𝐎𝐋𝐔𝐈́𝐃𝐎```__**", f'- > **🎉 __{character_name}__ evoluiu para o rank __{new_rank}__! Próximo limitador em __{next_limit_break}__.**', discord.Color.green(), next_step="use `kill!details NomeDoPersonagem` para ver os novos atributos")
            else:
                await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f'- > **{character_name} não está no nível para evoluir ou quebrar um limitador!**', discord.Color.red())
        else:
            await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f'- > **Personagem __"{character_name}"__ não encontrado.**', discord.Color.red())

@commands.has_permissions(administrator=True)
@commands.command(name='rebirth', aliases=['renascer'])
async def rebirth(ctx, character_name: str, rebirth_type: str | None = None):
    if rebirth_type is None:
        await send_embed(
            ctx,
            "**__```𝐓𝐈𝐏𝐎 𝐃𝐄 𝐑𝐄𝐁𝐈𝐑𝐓𝐇 𝐍𝐀̃𝐎 𝐄𝐍𝐂𝐎𝐍𝐓𝐑𝐀𝐃𝐎```__**",
            "- > **Para usar o comando corretamente, forneça o nome do personagem seguido do tipo de Rebirth.**\n\n"
            "**Exemplo de uso correto:**\n"
            "`kill!rebirth NomeDoPersonagem early`\n\n"
            "**Tipos de Rebirth válidos:**\n"
            "`early`, `intermediate`, `late`",
            discord.Color.red()
        )
        return

    if rebirth_type.lower() not in ['early', 'intermediate', 'late']:
        await send_embed(
            ctx,
            "**__```𝐎𝐏𝐂̧𝐀̃𝐎 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐀```__**",
            "- > **Opção de Rebirth inválida. Escolha entre as seguintes opções:**\n"
            "`early`, `intermediate`, `late`",
            discord.Color.red()
        )
        return

    user_id = await get_user_id_from_name(ctx, character_name)
    if user_id:
        character_id = get_character_by_name_and_user(character_name, user_id)
        c.execute("SELECT level FROM character_progression WHERE character_id=?", (character_id,))
        character = c.fetchone()
        if character:
            level = character[0]

            rebirth_count = get_rebirth_data(character_name, user_id)
            next_rebirth_levels = {
                'early': 25 + rebirth_count * 5,
                'intermediate': 50 + rebirth_count * 10,
                'late': 75 + rebirth_count * 15
            }

            rebirth_result = apply_rebirth(character_name, user_id, level, rebirth_type)
            if rebirth_result:
                bonus_points, xp_multiplier, rebirth_count, next_rebirth_levels = rebirth_result
                reset_character(character_name, user_id, bonus_points, xp_multiplier)

                await send_embed(
                    ctx,
                    "**__```𝐑𝐄𝐁𝐈𝐑𝐓𝐇 𝐂𝐎𝐍𝐂𝐋𝐔𝐈́𝐃𝐎```__**",
                    f'**🎉 __{character_name}__ realizou o Rebirth!**\n'
                    f'**Bônus: +{bonus_points} pontos, Multiplicador de XP: {xp_multiplier:.2f}x.**\n'
                    f'**Rebirths acumulados: {rebirth_count}.**\n'
                    f'**Próximos requisitos de Rebirth: Early: {next_rebirth_levels["early"]}, '
                    f'Intermediate: {next_rebirth_levels["intermediate"]}, Late: {next_rebirth_levels["late"]}.**',
                    discord.Color.green(),
                    next_step="use `kill!points` para redistribuir atributos"
                )
            else:
                await send_embed(
                    ctx,
                    "**__```𝐑𝐄𝐁𝐈𝐑𝐓𝐇 𝐍𝐀̃𝐎 𝐏𝐎𝐃𝐄 𝐒𝐄𝐑 𝐑𝐄𝐀𝐋𝐈𝐙𝐀𝐃𝐎```__**",
                    f'**{character_name} não está no nível necessário para realizar o Rebirth.**\n\n'
                    f'**Próximos requisitos de Rebirth:**\n'
                    f'`Early`: {next_rebirth_levels["early"]}\n'
                    f'`Intermediate`: {next_rebirth_levels["intermediate"]}\n'
                    f'`Late`: {next_rebirth_levels["late"]}',
                    discord.Color.red()
                )
        else:
            await send_embed(
                ctx,
                "**__```𝐄𝐑𝐑𝐎```__**",
                f'**Personagem __"{character_name}"__ não encontrado.**',
                discord.Color.red()
            )

@commands.command(name='points', aliases=['addpoint', 'pontos'])
async def points(ctx, character_name: str, attribute: str, points: int):
    valid_attributes = ["forca", "resistencia", "agilidade", "sentidos", "vitalidade", "inteligencia"]
    if attribute.lower() not in valid_attributes:
        await send_embed(ctx, "**__```𝐀𝐓𝐑𝐈𝐁𝐔𝐓𝐎 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐎```__**", f'**Atributo inválido. Os atributos válidos são: {", ".join(valid_attributes)}.**', discord.Color.red())
        return

    character_id = get_character_by_name_and_user(character_name, ctx.author.id)
    c.execute("""
        SELECT points_available, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia
        FROM character_progression
        WHERE character_id=?
    """, (character_id,))
    character = c.fetchone()
    if not character:
        await send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f'**Personagem __"{character_name}"__ não encontrado ou você não tem permissão para distribuir pontos.**', discord.Color.red())
        return

    current_points, *attrs = character
    if points > current_points:
        await send_embed(ctx, "**__```𝐏𝐎𝐍𝐓𝐎𝐒 𝐈𝐍𝐒𝐔𝐅𝐈𝐂𝐈𝐄𝐍𝐓𝐄𝐒```__**", f'**Você não tem pontos suficientes. Pontos disponíveis: __{current_points}__.**', discord.Color.red())
        return

    updated_attributes = dict(zip(valid_attributes, attrs))
    updated_attributes[attribute.lower()] += points
    current_points -= points

    c.execute('''
        UPDATE character_progression
        SET points_available=?, forca=?, resistencia=?, agilidade=?, sentidos=?, vitalidade=?, inteligencia=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE character_id=?
    ''', (current_points, *updated_attributes.values(), character_id))
    conn.commit()

    await send_embed(ctx, "**__```𝐏𝐎𝐍𝐓𝐎𝐒 𝐃𝐈𝐒𝐓𝐑𝐈𝐁𝐔𝐈́𝐃𝐎𝐒```__**", f'**🎉 __{points}__ pontos distribuídos para __{attribute}__ de __{character_name}__. Pontos restantes: __{current_points}__.**', discord.Color.green(), next_step="use `kill!details NomeDoPersonagem` para acompanhar o build")


async def setup(bot):
    bot.add_command(xp)
    bot.add_command(setlevel)
    bot.add_command(evolve)
    bot.add_command(points)
    bot.add_command(rebirth)
