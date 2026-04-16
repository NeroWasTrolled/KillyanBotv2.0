"""
soul_details.py

Sistema de detalhes do personagem refatorado para Soul Wandering.
Exibe informações estruturadas com foco em Reiryoku, Reiatsu e progressão racial.

Autor: Refatoração Soul Wandering v1.0
Data: 16/04/2026
"""

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import json
from typing import Optional, Dict, Tuple, List
from database.connection import create_connection

# Conexão com BD
conn = create_connection()
c = conn.cursor()

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES E CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════════════════════

RANK_UP_LEVELS = {
    1: 'F-', 15: 'F', 30: 'F+', 45: 'E-', 60: 'E', 75: 'E+',
    90: 'D-', 105: 'D', 120: 'D+', 135: 'C-', 150: 'C', 165: 'C+',
    180: 'B-', 195: 'B', 210: 'B+', 225: 'A-', 240: 'A', 255: 'A+',
    270: 'S', 285: 'S+', 300: 'SS', 315: 'SS+', 330: 'SSS', 345: 'SSS+', 360: 'Z'
}

REIRYOKU_SKILLS_ORDER = ['Ten', 'Zetsu', 'Ren', 'Hatsu', 'Gyo', 'Shu', 'Ko', 'Ken', 'En', 'Ryu']

REIATSU_CATEGORIES = {
    'Fortificação': '🛡️',
    'Transmutação': '⚗️',
    'Conjuração': '📖',
    'Emissão': '✨',
    'Manipulação': '🔗',
    'Especialista': '⭐',
    'Fortification': '🛡️',
    'Transmutation': '⚗️',
    'Conjuration': '📖',
    'Emission': '✨',
    'Manipulation': '🔗',
    'Specialization': '⭐',
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE BUSCA DE DADOS
# ═══════════════════════════════════════════════════════════════════════════════

def get_character_data(character_name: str, user_id: int) -> Optional[Dict]:
    """
    Retorna dicionário com todos os dados do personagem.
    Retorna None se personagem não existir.
    """
    
    # 1. Dados básicos
    c.execute("""
        SELECT character_id, name, image_url, soul_tier
        FROM characters
        WHERE name COLLATE NOCASE = ? AND user_id = ?
    """, (character_name, user_id))
    
    char_row = c.fetchone()
    if not char_row:
        return None
    
    character_id, name, image_url, soul_tier = char_row
    
    # 2. Raça
    c.execute("""
        SELECT race_name, race_stage, race_stage_level, evolution_count
        FROM character_race_progression
        WHERE character_id = ?
    """, (character_id,))
    race_row = c.fetchone()
    race_data = {
        'name': race_row[0] if race_row else 'Unknown',
        'stage': race_row[1] if race_row else 'Base',
        'stage_level': race_row[2] if race_row else 0,
        'evolutions': race_row[3] if race_row else 0
    }
    
    # 3. Reiryoku
    c.execute("""
        SELECT core_color, core_stage, reiryoku_base_pool, reiryoku_current,
               core_stability, core_purity
        FROM character_reiryoku
        WHERE character_id = ?
    """, (character_id,))
    reiryoku_row = c.fetchone()
    reiryoku_data = {
        'core_color': reiryoku_row[0] if reiryoku_row else 'Black',
        'core_stage': reiryoku_row[1] if reiryoku_row else 'Dark Stage',
        'base_pool': reiryoku_row[2] if reiryoku_row else 100,
        'current': reiryoku_row[3] if reiryoku_row else 100,
        'stability': reiryoku_row[4] if reiryoku_row else 50,
        'purity': reiryoku_row[5] if reiryoku_row else 50
    }
    
    # 4. Técnicas-Base de Reiryoku
    c.execute("""
        SELECT skill_name, mastery_level, is_awakened, control_level
        FROM character_reiryoku_skills
        WHERE character_id = ?
        ORDER BY 
            CASE skill_name
                WHEN 'Ten' THEN 1 WHEN 'Zetsu' THEN 2 WHEN 'Ren' THEN 3
                WHEN 'Hatsu' THEN 4 WHEN 'Gyo' THEN 5 WHEN 'Shu' THEN 6
                WHEN 'Ko' THEN 7 WHEN 'Ken' THEN 8 WHEN 'En' THEN 9
                WHEN 'Ryu' THEN 10 ELSE 11 END
    """, (character_id,))
    
    reiryoku_skills = []
    for skill_row in c.fetchall():
        reiryoku_skills.append({
            'name': skill_row[0],
            'mastery': skill_row[1],
            'awakened': skill_row[2],
            'control': skill_row[3]
        })
    
    # 5. Reiatsu
    c.execute("""
        SELECT primary_category, primary_category_level,
               fortification_affinity, transmutation_affinity, conjuration_affinity,
               emission_affinity, manipulation_affinity, specialization_affinity
        FROM character_reiatsu_affinities
        WHERE character_id = ?
    """, (character_id,))
    reiatsu_row = c.fetchone()

    secondary_affinities = {}
    if reiatsu_row:
        secondary_affinities = {
            'Fortification': reiatsu_row[2] or 0,
            'Transmutation': reiatsu_row[3] or 0,
            'Conjuration': reiatsu_row[4] or 0,
            'Emission': reiatsu_row[5] or 0,
            'Manipulation': reiatsu_row[6] or 0,
            'Specialization': reiatsu_row[7] or 0,
        }

    reiatsu_data = {
        'primary': reiatsu_row[0] if reiatsu_row else 'Especialista',
        'primary_level': reiatsu_row[1] if reiatsu_row else 1,
        'secondary': secondary_affinities
    }
    
    # 6. Progressão
    c.execute("""
        SELECT level, experience, points_available, rank, limit_break, xp_multiplier,
               rebirth_count, forca, resistencia, agilidade, sentidos, vitalidade, inteligencia
        FROM character_progression
        WHERE character_id = ?
    """, (character_id,))
    prog_row = c.fetchone()
    
    if prog_row:
        progression_data = {
            'level': prog_row[0],
            'xp': prog_row[1],
            'points': prog_row[2],
            'rank': prog_row[3],
            'limit_break': prog_row[4],
            'xp_multiplier': prog_row[5],
            'rebirth_count': prog_row[6],
            'attributes': {
                'forca': prog_row[7],
                'resistencia': prog_row[8],
                'agilidade': prog_row[9],
                'sentidos': prog_row[10],
                'vitalidade': prog_row[11],
                'inteligencia': prog_row[12]
            }
        }
    else:
        progression_data = {
            'level': 1, 'xp': 0, 'points': 0, 'rank': 'F-', 'limit_break': 0,
            'xp_multiplier': 1.0, 'rebirth_count': 0,
            'attributes': {'forca': 1, 'resistencia': 1, 'agilidade': 1, 
                          'sentidos': 1, 'vitalidade': 1, 'inteligencia': 1}
        }
    
    # 7. Sistemas especiais (opcionais)
    c.execute("SELECT zanpakuto_name, form FROM character_zanpakuto WHERE character_id = ? LIMIT 1", 
              (character_id,))
    zanpakuto = c.fetchone()
    
    c.execute("SELECT COUNT(*) FROM character_grimoire WHERE character_id = ?", (character_id,))
    has_grimoire = c.fetchone()[0] > 0
    
    c.execute("SELECT COUNT(*) FROM character_noble_phantasm WHERE character_id = ?", (character_id,))
    has_phantasm = c.fetchone()[0] > 0
    
    c.execute("SELECT COUNT(*) FROM character_runes WHERE character_id = ? AND is_inscribed = 1", (character_id,))
    active_runes = c.fetchone()[0]
    
    special_systems = {
        'zanpakuto': {'name': zanpakuto[0], 'form': zanpakuto[1]} if zanpakuto else None,
        'grimoire': has_grimoire,
        'phantasm': has_phantasm,
        'active_runes': active_runes
    }
    
    return {
        'character_id': character_id,
        'name': name,
        'image_url': image_url,
        'soul_tier': soul_tier,
        'race': race_data,
        'reiryoku': reiryoku_data,
        'reiryoku_skills': reiryoku_skills,
        'reiatsu': reiatsu_data,
        'progression': progression_data,
        'special_systems': special_systems
    }

def _parse_affinities(json_str: str) -> Dict:
    """Parse JSON de afinidades secundárias."""
    try:
        if not json_str or json_str == '{}':
            return {}
        return json.loads(json_str)
    except:
        return {}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE FORMATAÇÃO DE EMBEDS
# ═══════════════════════════════════════════════════════════════════════════════

def _format_progress_bar(current: int, max_val: int, length: int = 10) -> str:
    """Cria barra de progressão visual."""
    if max_val == 0:
        return "▮" * length
    percentage = min(current / max_val, 1.0)
    filled = int(length * percentage)
    bar = "▮" * filled + "▯" * (length - filled)
    return f"{bar} {int(percentage * 100)}%"

def _get_racial_bonus(race_name: str, stage: str) -> Dict[str, int]:
    """
    Calcula bônus de atributo por raça e estágio.
    Pode ser expandido conforme necessário.
    """
    bonuses = {
        'forca': 0, 'resistencia': 0, 'agilidade': 0,
        'sentidos': 0, 'vitalidade': 0, 'inteligencia': 0
    }
    
    # Bônus por raça
    race_bonuses = {
        'Shinigami': {'forca': 2, 'resistencia': 3, 'sentidos': 3},
        'Hollow': {'vitalidade': 4, 'agilidade': 2, 'forca': 3},
        'Quincy': {'inteligencia': 3, 'agilidade': 3, 'sentidos': 2},
        'Arrancar': {'forca': 4, 'resistencia': 3, 'vitalidade': 2},
        'Human': {'inteligencia': 2},
    }
    
    race_bonus = race_bonuses.get(race_name, {})
    for attr, val in race_bonus.items():
        bonuses[attr] = val
    
    # Bônus adicional por estágio
    stage_multiplier = {
        'Base': 1.0, 'V1': 1.2, 'V2': 1.4, 'V3': 1.6,
        'Awakening': 2.0
    }
    multiplier = stage_multiplier.get(stage, 1.0)
    
    for attr in bonuses:
        bonuses[attr] = int(bonuses[attr] * multiplier)
    
    return bonuses

def create_soul_details_embed(char_data: Dict) -> discord.Embed:
    """
    Cria embed completo com informações Soul Wandering do personagem.
    """
    
    embed = discord.Embed(color=discord.Color.from_rgb(100, 50, 150))
    
    # Header com nome e imagem
    embed.title = f"𝐃𝐄𝐓𝐀𝐋𝐇𝐞𝐬 𝖘𝖔𝖜𝖑: {char_data['name']}"
    if char_data['image_url']:
        embed.set_image(url=char_data['image_url'])
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 1: IDENTIDADE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    race = char_data['race']
    identity_text = (
        f"**𐦙𝐀𝐂𝐄:**\n"
        f"→ {race['name']} | Estágio: {race['stage']} ({race['stage_level']}%)\n"
        f"→ Evoluções: {race['evolutions']}\n\n"
        f"**𝐒𝐎𝐔𝐋 𝐓𝐈𝐄𝐑:**\n"
        f"→ {char_data['soul_tier']}/100"
    )
    embed.add_field(name="═══ 𝐈𝐃𝐄𝐍𝐓𝐈𝐃𝐀𝐃𝐄 ═══", value=identity_text, inline=False)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 2: REIRYOKU
    # ═══════════════════════════════════════════════════════════════════════════════
    
    reiryoku = char_data['reiryoku']
    pool_bar = _format_progress_bar(reiryoku['current'], reiryoku['base_pool'])
    stability_bar = _format_progress_bar(reiryoku['stability'], 100, 8)
    purity_bar = _format_progress_bar(reiryoku['purity'], 100, 8)
    
    reiryoku_text = (
        f"**𐦙𝐍𝐔́𝐂𝐋𝐄𝐎:** {reiryoku['core_color']} Core | {reiryoku['core_stage']}\n"
        f"**𝐏𝐀𝐂𝐈𝐅𝐈𝐂𝐀𝐃𝐄:** {pool_bar}\n"
        f"→ {reiryoku['current']}/{reiryoku['base_pool']} Reiryoku\n\n"
        f"**𝐐𝐔𝐀𝐋𝐈𝐃𝐀𝐃𝐄 𝐃𝐎 𝐍𝐔́𝐂𝐋𝐄𝐎:**\n"
        f"→ Estabilidade: {stability_bar}\n"
        f"→ Pureza: {purity_bar}"
    )
    embed.add_field(name="═══ 𝐑𝐄𝐈𝐑𝐘𝐎𝐊𝐔 ═══", value=reiryoku_text, inline=False)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 3: TÉCNICAS-BASE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    skills_text = ""
    for skill in char_data['reiryoku_skills']:
        status = "✅" if skill['awakened'] else "⏸️"
        mastery_bar = _format_progress_bar(skill['mastery'], 100, 8)
        skills_text += f"→ {status} {skill['name']:8} {mastery_bar}\n"
    
    if not skills_text:
        skills_text = "Nenhuma técnica-base descoberta ainda."
    
    embed.add_field(name="═══ 𝐓𝐄́𝐂𝐍𝐈𝐂𝐀𝐒-𝐁𝐀𝐒𝐄 ═══", value=skills_text, inline=False)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 4: REIATSU
    # ═══════════════════════════════════════════════════════════════════════════════
    
    reiatsu = char_data['reiatsu']
    primary_icon = REIATSU_CATEGORIES.get(reiatsu['primary'], '⭐')
    
    reiatsu_text = f"**𐦙𝐏𝐑𝐈𝐌𝐀́𝐑𝐈𝐀:** {primary_icon} {reiatsu['primary']} (Nível {reiatsu['primary_level']})\n\n"
    
    if reiatsu['secondary']:
        reiatsu_text += "**𝐀𝐅𝐈𝐍𝐈𝐃𝐀𝐃𝐄𝐒 𝐒𝐄𝐂𝐔𝐍𝐃𝐀́𝐑𝐈𝐀𝐒:**\n"
        for secondary, affinity in reiatsu['secondary'].items():
            sec_icon = REIATSU_CATEGORIES.get(secondary, '⭐')
            reiatsu_text += f"→ {sec_icon} {secondary}: {affinity}%\n"
    else:
        reiatsu_text += "**𝐀𝐅𝐈𝐍𝐈𝐃𝐀𝐃𝐄𝐒:** Nenhuma desenvolvida ainda."
    
    embed.add_field(name="═══ 𝐑𝐄𝐈𝐀𝐓𝐒𝐔 ═══", value=reiatsu_text, inline=False)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 5: PROGRESSÃO
    # ═══════════════════════════════════════════════════════════════════════════════
    
    prog = char_data['progression']
    
    # Calcular XP para próximo nível
    def xp_for_next(level):
        import math
        return int(100 * level * math.log(level + 1))
    
    xp_needed = xp_for_next(prog['level'])
    xp_bar = _format_progress_bar(prog['xp'], xp_needed, 10)
    
    progression_text = (
        f"**𐦙𝐋𝐄𝐕𝐀𝐓𝐎:**\n"
        f"→ Level {prog['level']} | Rank {prog['rank']}\n"
        f"→ XP: {xp_bar}\n"
        f"→ {prog['xp']}/{xp_needed}\n\n"
        f"**𝐀𝐓𝐑𝐈𝐁𝐔𝐓𝐎𝐒 (+ Racial Bonus):**\n"
    )
    
    racial_bonuses = _get_racial_bonus(char_data['race']['name'], char_data['race']['stage'])
    attrs = prog['attributes']
    
    for attr_name in ['forca', 'resistencia', 'agilidade', 'sentidos', 'vitalidade', 'inteligencia']:
        base_val = attrs[attr_name]
        bonus = racial_bonuses.get(attr_name, 0)
        total = base_val + bonus
        progression_text += f"→ {attr_name.capitalize():15} {base_val:2d} (+{bonus:1d} = {total:2d})\n"
    
    progression_text += f"\n**𐦙𝐏𝐎𝐍𝐓𝐎𝐒:** {prog['points']} disponíveis"
    
    if prog['limit_break'] > 0:
        progression_text += f"\n**𐦙𝐋𝐈𝐌𝐈𝐓𝐄 𝐝𝐞 𝐍𝐈𝐕𝐄𝐋:** {prog['limit_break']}"
    
    if prog['xp_multiplier'] != 1.0:
        progression_text += f"\n**𐦙𝐌𝐔𝐋𝐓𝐈𝐏𝐋𝐈𝐂𝐀𝐃𝐎𝐑 𝐗𝐏:** {prog['xp_multiplier']}x"
    
    if prog['rebirth_count'] > 0:
        progression_text += f"\n**𐦙𝐗𝐔𝐓𝐒𝐔𝐊𝐎𝐑𝐀:** {prog['rebirth_count']} rebirths"
    
    embed.add_field(name="═══ 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒𝐀̃𝐎 ═══", value=progression_text, inline=False)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SEÇÃO 6: SISTEMAS ESPECIAIS (se existirem)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    special = char_data['special_systems']
    special_text = ""
    
    if special['zanpakuto']:
        special_text += f"⚔️  **Zanpakutō:** {special['zanpakuto']['name']} ({special['zanpakuto']['form']})\n"
    
    if special['grimoire']:
        special_text += f"📖 **Grimório:** Possui\n"
    
    if special['phantasm']:
        special_text += f"🔱 **Noble Phantasm:** Desbloqueado\n"
    
    if special['active_runes'] > 0:
        special_text += f"⚛️  **Runas Ativas:** {special['active_runes']}\n"
    
    if special_text:
        embed.add_field(name="═══ 𝐒𝐈𝐒𝐓𝐄𝐌𝐀𝐒 𝐄𝐒𝐏𝐄𝐂𝐈𝐀𝐈𝐒 ═══", value=special_text, inline=False)
    
    embed.set_footer(text="Soul Wandering Character Details System")
    
    return embed

# ═══════════════════════════════════════════════════════════════════════════════
# COMANDO DISCORD
# ═══════════════════════════════════════════════════════════════════════════════

class SoulDetails(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='soul_details', aliases=['sd', 'sdetails'])
    async def soul_details_cmd(self, ctx, *, character_name: str):
        """
        Mostra detalhes do personagem no sistema Soul Wandering.
        
        Uso: !soul_details <nome do personagem>
        """
        
        char_data = get_character_data(character_name, ctx.author.id)
        
        if not char_data:
            error_embed = discord.Embed(
                title="❌ PERSONAGEM NÃO ENCONTRADO",
                description=f"Nenhum personagem chamado '{character_name}' foi encontrado.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)
            return
        
        embed = create_soul_details_embed(char_data)
        await ctx.send(embed=embed)
    
    @app_commands.command(name='soul_details', description='Mostra detalhes Soul Wandering do personagem')
    async def soul_details_slash(self, interaction: discord.Interaction, character_name: str):
        """Mostra detalhes do personagem no sistema Soul Wandering."""
        
        char_data = get_character_data(character_name, interaction.user.id)
        
        if not char_data:
            error_embed = discord.Embed(
                title="❌ PERSONAGEM NÃO ENCONTRADO",
                description=f"Nenhum personagem chamado '{character_name}' foi encontrado.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return
        
        embed = create_soul_details_embed(char_data)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SoulDetails(bot))
