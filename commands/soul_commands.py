"""
soul_commands.py

Comandos fundamentais para gerenciar sistemas Soul Wandering:
- /race: Gerir raça e estágio racial
- /reiryoku: Ver estado do Reiryoku
- /reiatsu: Gerenciar categoria de Reiatsu
- /awaken-skill: Despertar técnicas-base
- /core: Verificar núcleo de Reiryoku

Autor: Refatoração Soul Wandering v1.0
Data: 16/04/2026
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
from typing import Optional
from database.connection import create_connection
from services.characteristics_service import allows_specialization, get_effective_reiryoku_values

# Conexão com BD
conn = create_connection()
c = conn.cursor()

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

VALID_STAGES = ['Base', 'V1', 'V2', 'V3', 'Awakening']
VALID_CATEGORIES = ['Fortification', 'Transmutation', 'Conjuration', 'Emission', 'Manipulation', 'Specialization']
REIRYOKU_SKILLS = ['Ten', 'Zetsu', 'Ren', 'Hatsu', 'Gyo', 'Shu', 'Ko', 'Ken', 'En', 'Ryu']

STAGE_CHOICES = [app_commands.Choice(name=stage, value=stage) for stage in VALID_STAGES]
REIATSU_CATEGORY_CHOICES = [app_commands.Choice(name=category, value=category) for category in VALID_CATEGORIES]
SKILL_CHOICES = [app_commands.Choice(name=skill, value=skill) for skill in REIRYOKU_SKILLS]

DEFAULT_RACE_SUGGESTIONS = [
    'Shinigami',
    'Vaizard',
    'FullBringer',
    'Quincy',
    'Human',
    'Youkai',
    'Elfo',
    'Hollow',
    'Bount',
    'Ghoul',
    'Monster',
]

CATEGORY_ALIASES = {
    'fortificacao': 'Fortification',
    'fortificação': 'Fortification',
    'fortification': 'Fortification',
    'transmutacao': 'Transmutation',
    'transmutação': 'Transmutation',
    'transmutation': 'Transmutation',
    'conjuracao': 'Conjuration',
    'conjuração': 'Conjuration',
    'conjuration': 'Conjuration',
    'emissao': 'Emission',
    'emissão': 'Emission',
    'emission': 'Emission',
    'manipulacao': 'Manipulation',
    'manipulação': 'Manipulation',
    'manipulation': 'Manipulation',
    'especialista': 'Specialization',
    'specialization': 'Specialization'
}


def to_bold_sans_serif(text: str) -> str:
    """Converte texto para bold sans-serif Unicode."""
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
    return ''.join(bold_sans_serif[ch] if ch in bold_sans_serif else ch for ch in text.upper())


async def send_standard_embed(interaction: discord.Interaction, title: str, description: str, color: discord.Color):
    embed = discord.Embed(title=title, description=description, color=color)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VALIDAÇÕES
# ═══════════════════════════════════════════════════════════════════════════════

async def get_character_id(ctx, character_name: str) -> Optional[int]:
    """Retorna character_id se o personagem existe e pertence ao usuário."""
    user_id = getattr(getattr(ctx, 'user', None), 'id', None) or getattr(getattr(ctx, 'author', None), 'id', None)
    if user_id is None:
        return None
    c.execute(
        "SELECT character_id FROM characters WHERE name COLLATE NOCASE = ? AND user_id = ?",
        (character_name, user_id)
    )
    result = c.fetchone()
    return result[0] if result else None

# ═══════════════════════════════════════════════════════════════════════════════
# COG: SOUL COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

class SoulCommands(commands.Cog):
    """Comandos de gerenciamento de sistema Soul Wandering."""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COMANDO: RACE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    @app_commands.choices(
        action=[
            app_commands.Choice(name='Ver', value='view'),
            app_commands.Choice(name='Definir', value='set'),
            app_commands.Choice(name='Evoluir', value='evolve'),
        ],
        stage=STAGE_CHOICES,
    )
    @app_commands.command(name='race', description='Mostra ou define raça do personagem')
    @app_commands.describe(
        character_name="Nome do personagem",
        action="view, set ou evolve",
        race="Raça (nome livre; sugestões baseadas no banco)",
        stage="Estágio (Base, V1, V2, V3, Awakening, Transcendence)"
    )
    async def race_cmd(
        self,
        interaction: discord.Interaction,
        character_name: str,
        action: str = "view",
        race: Optional[str] = None,
        stage: Optional[str] = None
    ):
        """
        Gerencia raça e estágio racial do personagem.
        
        ACTION:
        - view: Mostra raça atual
        - set: Define raça e estágio
        - evolve: Avança para próximo estágio (requires conditions)
        """
        
        char_id = await get_character_id(interaction, character_name)
        if not char_id:
            await interaction.response.send_message(
                f"❌ Personagem '{character_name}' não encontrado.",
                ephemeral=True
            )
            return
        
        action = action.lower()
        
        if action == "view":
            # Mostrar raça atual
            c.execute(
                "SELECT race_name, race_stage, race_stage_level FROM character_race_progression WHERE character_id = ?",
                (char_id,)
            )
            result = c.fetchone()
            
            if not result:
                embed = discord.Embed(
                    title="**__```𝐑𝐀𝐂̧𝐀 𝐍𝐀̃𝐎 𝐃𝐄𝐅𝐈𝐍𝐈𝐃𝐀```__**",
                    description="- > **Este personagem ainda não tem raça definida. Use action:set para definir.**",
                    color=discord.Color.red()
                )
            else:
                race_name, stage, stage_level = result
                embed = discord.Embed(
                    title="**__```𝐑𝐀𝐂̧𝐀```__**",
                    description=f"- > **Raça:** {race_name}\n- > **Estágio:** {stage} ({stage_level}%)",
                    color=discord.Color.purple()
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        elif action == "set":
            # Definir raça
            if not race or not stage:
                embed = discord.Embed(
                    title="**__```𝐏𝐀𝐑𝐀̂𝐌𝐄𝐓𝐑𝐎𝐒 𝐈𝐍𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐎𝐒```__**",
                    description="- > **Você deve especificar raça e estágio.**",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            race = race.strip()
            if not race:
                embed = discord.Embed(
                    title="**__```𝐑𝐀𝐂̧𝐀 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐀```__**",
                    description="- > **Informe um nome de raça válido.**",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if stage not in VALID_STAGES:
                embed = discord.Embed(
                    title="**__```𝐄𝐒𝐓𝐀́𝐆𝐈𝐎 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐎```__**",
                    description=f"- > **Válidos:** {', '.join(VALID_STAGES)}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            try:
                c.execute(
                    """
                    INSERT INTO character_race_progression (character_id, race_name, race_stage)
                    VALUES (?, ?, ?)
                    ON CONFLICT(character_id)
                    DO UPDATE SET race_name = excluded.race_name, race_stage = excluded.race_stage, updated_at = CURRENT_TIMESTAMP
                    """,
                    (char_id, race, stage)
                )
                conn.commit()
                
                embed = discord.Embed(
                    title="**__```𝐑𝐀𝐂̧𝐀 𝐃𝐄𝐅𝐈𝐍𝐈𝐃𝐀```__**",
                    description=f"- > **{character_name}** agora é **{race}** - Estágio: **{stage}**",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            except Exception as e:
                embed = discord.Embed(
                    title="**__```𝐄𝐑𝐑𝐎```__**",
                    description=f"- > **Erro ao definir raça:** {str(e)}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action == "evolve":
            # Evoluir para próximo estágio
            c.execute(
                "SELECT race_stage, race_stage_level FROM character_race_progression WHERE character_id = ?",
                (char_id,)
            )
            result = c.fetchone()

            if not result:
                embed = discord.Embed(
                    title="**__```𝐑𝐀𝐂̧𝐀 𝐍𝐀̃𝐎 𝐃𝐄𝐅𝐈𝐍𝐈𝐃𝐀```__**",
                    description="- > **Use action:set para definir a raça antes de evoluir.**",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            current_stage, stage_level = result
            stage_idx = VALID_STAGES.index(current_stage) if current_stage in VALID_STAGES else 0

            if stage_level < 100:
                embed = discord.Embed(
                    title="**__```𝐄𝐒𝐓𝐀́𝐆𝐈𝐎 𝐈𝐍𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐎```__**",
                    description=f"- > **Progresso:** {stage_level}%",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if stage_idx >= len(VALID_STAGES) - 1:
                embed = discord.Embed(
                    title="**__```𝐀𝐏𝐈𝐂𝐄 𝐀𝐋𝐂𝐀𝐍Ç𝐀𝐃𝐎```__**",
                    description="- > **Já está no estágio máximo (Awakening).**",
                    color=discord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            next_stage = VALID_STAGES[stage_idx + 1]

            try:
                c.execute(
                    """
                    UPDATE character_race_progression
                    SET race_stage = ?, race_stage_level = 0, evolution_count = evolution_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE character_id = ?
                    """,
                    (next_stage, char_id)
                )
                conn.commit()

                embed = discord.Embed(
                    title="**__```𝐄𝐕𝐎𝐋𝐔Ç𝐀̃𝐎 𝐑𝐀𝐂𝐈𝐀𝐋```__**",
                    description=f"- > **{character_name}** evoluiu para **{next_stage}**!",
                    color=discord.Color.gold()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

            except Exception as e:
                embed = discord.Embed(
                    title="**__```𝐄𝐑𝐑𝐎```__**",
                    description=f"- > **Erro ao evoluir:** {str(e)}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @race_cmd.autocomplete('race')
    async def race_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            c.execute(
                """
                SELECT DISTINCT race_name
                FROM character_race_progression
                WHERE race_name IS NOT NULL AND TRIM(race_name) <> ''
                ORDER BY race_name COLLATE NOCASE
                """
            )
            db_races = [row[0] for row in c.fetchall() if row and row[0]]
        except Exception:
            db_races = []

        # Mantem sugestões úteis, mas prioriza o que já existe no banco.
        merged = []
        seen = set()
        for race_name in db_races + DEFAULT_RACE_SUGGESTIONS:
            key = race_name.lower()
            if key not in seen:
                seen.add(key)
                merged.append(race_name)

        term = (current or '').lower()
        if term:
            merged = [race_name for race_name in merged if term in race_name.lower()]

        return [app_commands.Choice(name=race_name, value=race_name) for race_name in merged[:25]]
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COMANDO: REIRYOKU
    # ═══════════════════════════════════════════════════════════════════════════════
    
    @app_commands.command(name='reiryoku', description='Mostra estado do Reiryoku')
    @app_commands.describe(character_name="Nome do personagem")
    async def reiryoku_cmd(self, interaction: discord.Interaction, character_name: str):
        """
        Mostra detalhes do Reiryoku (reservatório de energia).
        """
        
        char_id = await get_character_id(interaction, character_name)
        if not char_id:
            await send_standard_embed(
                interaction,
                "**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐍𝐀𝐎 𝐄𝐍𝐂𝐎𝐍𝐓𝐑𝐀𝐃𝐎```__**",
                f"- > **'{character_name}' não existe ou pertence a outro usuário.**",
                discord.Color.red(),
            )
            return
        
        c.execute(
            """
            SELECT core_color, core_stage, reiryoku_base_pool, reiryoku_current,
                   core_stability, core_purity, control_rating
            FROM character_reiryoku
            WHERE character_id = ?
            """,
            (char_id,)
        )
        
        result = c.fetchone()
        if not result:
            await send_standard_embed(
                interaction,
                "**__```𝐑𝐄𝐈𝐑𝐘𝐎𝐊𝐔 𝐍𝐀𝐎 𝐈𝐍𝐈𝐂𝐈𝐀𝐋𝐈𝐙𝐀𝐃𝐎```__**",
                "- > **Reiryoku não foi inicializado. Contate o administrador.**",
                discord.Color.orange(),
            )
            return
        
        color, stage, base_pool, current, stability, purity, control_rating = result
        effective_max_pool, effective_current_pool, _ = get_effective_reiryoku_values(
            character_id=char_id,
            base_pool=base_pool,
            current_pool=current,
        )
        
        # Criar barras de progresso
        def make_bar(val, max_val, length=15):
            if max_val == 0:
                filled = 0
            else:
                filled = min(int(val / max_val * length), length)
            return "█" * filled + "░" * (length - filled)
        
        pool_bar = make_bar(effective_current_pool, effective_max_pool)
        stability_bar = make_bar(stability, 100)
        purity_bar = make_bar(purity, 100)
        
        description = (
            f"- > **Cor:** {color}\n"
            f"- > **Estágio:** {stage}\n"
            f"- > **Pool:** {pool_bar} {effective_current_pool:.1f}/{effective_max_pool:.1f}\n"
            f"- > **Estabilidade:** {stability_bar} {stability}%\n"
            f"- > **Pureza:** {purity_bar} {purity}%\n"
            f"- > **Controle:** {control_rating}"
        )

        await send_standard_embed(
            interaction,
            "**__```𝐑𝐄𝐈𝐑𝐘𝐎𝐊𝐔```__**",
            description,
            discord.Color.from_rgb(150, 100, 200),
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COMANDO: REIATSU
    # ═══════════════════════════════════════════════════════════════════════════════
    
    @app_commands.choices(
        action=[
            app_commands.Choice(name='Ver', value='view'),
            app_commands.Choice(name='Definir', value='set'),
        ],
        category=REIATSU_CATEGORY_CHOICES,
    )
    @app_commands.command(name='reiatsu', description='Mostra ou define categoria de Reiatsu')
    @app_commands.describe(
        character_name="Nome do personagem",
        action="view ou set",
        category="Categoria (Fortification, Transmutation, Conjuration, Emission, Manipulation, Specialization)"
    )
    async def reiatsu_cmd(
        self,
        interaction: discord.Interaction,
        character_name: str,
        action: str = "view",
        category: Optional[str] = None
    ):
        """
        Mostra categoria primária e afinidades secundárias de Reiatsu.
        """
        
        char_id = await get_character_id(interaction, character_name)
        if not char_id:
            await send_standard_embed(
                interaction,
                "**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐍𝐀𝐎 𝐄𝐍𝐂𝐎𝐍𝐓𝐑𝐀𝐃𝐎```__**",
                f"- > **'{character_name}' não existe ou pertence a outro usuário.**",
                discord.Color.red(),
            )
            return
        
        action = action.lower()

        if action == "set":
            if not category:
                await send_standard_embed(
                    interaction,
                    "**__```𝐏𝐀𝐑𝐀̂𝐌𝐄𝐓𝐑𝐎 𝐈𝐍𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐎```__**",
                    "- > **Informe a categoria para definir o Reiatsu.**",
                    discord.Color.orange(),
                )
                return

            normalized = CATEGORY_ALIASES.get(category.strip().lower())
            if not normalized:
                await send_standard_embed(
                    interaction,
                    "**__```𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐀```__**",
                    f"- > **Válidas:** {', '.join(VALID_CATEGORIES)}",
                    discord.Color.red(),
                )
                return

            if normalized == "Specialization" and not allows_specialization(char_id):
                await send_standard_embed(
                    interaction,
                    "**__```𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐈𝐀 𝐁𝐋𝐎𝐐𝐔𝐄𝐀𝐃𝐀```__**",
                    "- > **Specialization requer a característica 'Especialista'.**",
                    discord.Color.red(),
                )
                return

            c.execute(
                """
                INSERT INTO character_reiatsu_affinities (character_id, primary_category, primary_category_level)
                VALUES (?, ?, 1)
                ON CONFLICT(character_id)
                DO UPDATE SET primary_category = excluded.primary_category,
                              primary_category_level = CASE
                                  WHEN character_reiatsu_affinities.primary_category_level = 0 THEN 1
                                  ELSE character_reiatsu_affinities.primary_category_level
                              END,
                              specialization_unlocked = CASE
                                  WHEN excluded.primary_category = 'Specialization' THEN 1
                                  ELSE character_reiatsu_affinities.specialization_unlocked
                              END,
                              updated_at = CURRENT_TIMESTAMP
                """,
                (char_id, normalized)
            )
            conn.commit()

            await send_standard_embed(
                interaction,
                "**__```𝐑𝐄𝐈𝐀𝐓𝐒𝐔 𝐃𝐄𝐅𝐈𝐍𝐈𝐃𝐎```__**",
                f"- > **{character_name}** agora possui **{normalized}** como categoria primária.",
                discord.Color.green(),
            )
            return

        c.execute(
            """
            SELECT primary_category, primary_category_level,
                   fortification_affinity, transmutation_affinity, conjuration_affinity,
                   emission_affinity, manipulation_affinity, specialization_affinity
            FROM character_reiatsu_affinities
            WHERE character_id = ?
            """,
            (char_id,)
        )
        
        result = c.fetchone()
        if not result:
            await send_standard_embed(
                interaction,
                "**__```𝐑𝐄𝐈𝐀𝐓𝐒𝐔 𝐍𝐀𝐎 𝐈𝐍𝐈𝐂𝐈𝐀𝐋𝐈𝐙𝐀𝐃𝐎```__**",
                "- > **Reiatsu não foi inicializado. Contate o administrador.**",
                discord.Color.orange(),
            )
            return
        
        primary, primary_level, fort, trans, conj, emis, manip, spec = result
        
        description = (
            f"- > **Categoria Primária:** {primary} (Nível {primary_level})\n"
            f"- > **Fortification:** {fort}%\n"
            f"- > **Transmutation:** {trans}%\n"
            f"- > **Conjuration:** {conj}%\n"
            f"- > **Emission:** {emis}%\n"
            f"- > **Manipulation:** {manip}%\n"
            f"- > **Specialization:** {spec}%"
        )

        await send_standard_embed(
            interaction,
            "**__```𝐑𝐄𝐈𝐀𝐓𝐒𝐔```__**",
            description,
            discord.Color.from_rgb(255, 200, 50),
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COMANDO: AWAKEN-SKILL
    # ═══════════════════════════════════════════════════════════════════════════════
    
    @app_commands.choices(skill_name=SKILL_CHOICES)
    @app_commands.command(name='awaken-skill', description='Desperta uma técnica-base')
    @app_commands.describe(
        character_name="Nome do personagem",
        skill_name="Nome da técnica (Ten, Zetsu, Ren, etc)"
    )
    async def awaken_skill_cmd(
        self,
        interaction: discord.Interaction,
        character_name: str,
        skill_name: str
    ):
        """
        Desperta uma técnica-base de Reiryoku.
        A técnica deve ser descoberta primeiro.
        """
        
        char_id = await get_character_id(interaction, character_name)
        if not char_id:
            await send_standard_embed(
                interaction,
                "**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐍𝐀𝐎 𝐄𝐍𝐂𝐎𝐍𝐓𝐑𝐀𝐃𝐎```__**",
                f"- > **'{character_name}' não existe ou pertence a outro usuário.**",
                discord.Color.red(),
            )
            return
        
        skill_name = skill_name.capitalize()
        
        if skill_name not in REIRYOKU_SKILLS:
            valid = ", ".join(REIRYOKU_SKILLS)
            await send_standard_embed(
                interaction,
                "**__```𝐓𝐄𝐂𝐍𝐈𝐂𝐀 𝐈𝐍𝐕𝐀́𝐋𝐈𝐃𝐀```__**",
                f"- > **Válidas:** {valid}",
                discord.Color.red(),
            )
            return
        
        c.execute(
            """
            SELECT is_awakened FROM character_reiryoku_skills
            WHERE character_id = ? AND skill_name = ?
            """,
            (char_id, skill_name)
        )
        
        result = c.fetchone()
        if not result:
            # Criar skill se não existir
            c.execute(
                """
                INSERT INTO character_reiryoku_skills (character_id, skill_name)
                VALUES (?, ?)
                """,
                (char_id, skill_name)
            )
            conn.commit()
            is_awakened = False
        else:
            is_awakened = bool(result[0])
        
        if is_awakened:
            await send_standard_embed(
                interaction,
                "**__```𝐉𝐀́ 𝐃𝐄𝐒𝐏𝐄𝐑𝐓𝐀𝐃𝐀```__**",
                f"- > **{skill_name}** já está despertada.",
                discord.Color.orange(),
            )
            return
        
        # Despertar
        c.execute(
            """
            UPDATE character_reiryoku_skills
            SET is_awakened = 1, awakened_at = CURRENT_TIMESTAMP
            WHERE character_id = ? AND skill_name = ?
            """,
            (char_id, skill_name)
        )
        conn.commit()
        
        await send_standard_embed(
            interaction,
            "**__```𝐓𝐄𝐂𝐍𝐈𝐂𝐀 𝐃𝐄𝐒𝐏𝐄𝐑𝐓𝐀𝐃𝐀```__**",
            f"- > **{character_name}** despertou **{skill_name}**.",
            discord.Color.gold(),
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COMANDO: CORE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    @app_commands.command(name='core', description='Mostra núcleo de Reiryoku')
    @app_commands.describe(character_name="Nome do personagem")
    async def core_cmd(self, interaction: discord.Interaction, character_name: str):
        """
        Mostra informações detalhadas do núcleo de Reiryoku
        (cor e estágio).
        """
        
        char_id = await get_character_id(interaction, character_name)
        if not char_id:
            await send_standard_embed(
                interaction,
                "**__```𝐏𝐄𝐑𝐒𝐎𝐍𝐀𝐆𝐄𝐌 𝐍𝐀𝐎 𝐄𝐍𝐂𝐎𝐍𝐓𝐑𝐀𝐃𝐎```__**",
                f"- > **'{character_name}' não existe ou pertence a outro usuário.**",
                discord.Color.red(),
            )
            return
        
        c.execute(
            """
            SELECT core_color, core_stage, core_stability, core_purity
            FROM character_reiryoku
            WHERE character_id = ?
            """,
            (char_id,)
        )
        
        result = c.fetchone()
        if not result:
            await send_standard_embed(
                interaction,
                "**__```𝐍𝐔́𝐂𝐋𝐄𝐎 𝐍𝐀𝐎 𝐈𝐍𝐈𝐂𝐈𝐀𝐋𝐈𝐙𝐀𝐃𝐎```__**",
                "- > **Núcleo de Reiryoku não inicializado. Contate o administrador.**",
                discord.Color.orange(),
            )
            return
        
        color, stage, stability, purity = result
        
        color_descriptions = {
            'Black': '⚫ Preto - O núcleo básico, ainda incompleto',
            'Red': '🔴 Vermelho - Primeiras manifestações de poder',
            'Orange': '🟠 Laranja - Energia mais refinada',
            'Yellow': '🟡 Amarelo - Pureza significativa',
            'Silver': '⚪ Prateado - Próximo ao auge',
            'White': '✨ Branco - Núcleo perfeito'
        }
        
        stage_descriptions = {
            'Dark Stage': 'Escuridão e caos - controle mínimo',
            'Solid Stage': 'Núcleo solidificado - base estável',
            'Light Stage': 'Brilho emergente - força crescente',
            'Initial Stage': 'Começo do desenvolvimento',
            'Mid Stage': 'Desenvolvimento em progresso',
            'High Stage': 'Desenvolvimento avançado'
        }
        
        description = (
            f"- > **Cor:** {color_descriptions.get(color, f'{color} - Desconhecido')}\n"
            f"- > **Estágio:** {stage_descriptions.get(stage, f'{stage} - Desconhecido')}\n"
            f"- > **Integridade:** Estabilidade {stability}% | Pureza {purity}%"
        )

        await send_standard_embed(
            interaction,
            "**__```𝐍𝐔́𝐂𝐋𝐄𝐎 𝐃𝐄 𝐑𝐄𝐈𝐑𝐘𝐎𝐊𝐔```__**",
            description,
            discord.Color.from_rgb(100, 50, 150),
        )

async def setup(bot):
    """Setup do cog."""
    await bot.add_cog(SoulCommands(bot))
