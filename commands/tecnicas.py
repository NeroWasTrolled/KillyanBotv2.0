import sqlite3
import discord
from discord.ext import commands, tasks
from commands.logs import Logs
import random
import re
import asyncio
import math
import sys
import unicodedata
from database.connection import create_connection
from services.characteristics_service import (
    allows_specialization,
    get_effective_reiryoku_values,
    get_mastery_multiplier,
)

SQLITE_LOCK_RETRIES = 3
SQLITE_LOCK_DELAY_SECONDS = 0.05


def create_db_connection():
    return create_connection()


conn = create_db_connection()
c = conn.cursor()

GAIN_BASE = 10.0
BASE_XP_PER_CAP = 40.0
BASE_REGEN = 5.0
REGEN_INTERVAL_SECONDS = 10.0

VALID_POWER_SYSTEMS = {
    "reiatsu",
    "reishi",
    "ego",
    "zanpakuto",
    "grimorio",
    "runa",
    "estilo_de_luta",
}

VALID_REIATSU_CATEGORIES = [
    "Fortification",
    "Transmutation",
    "Conjuration",
    "Emission",
    "Manipulation",
    "Specialization",
]

REIRYOKU_BASE_SKILLS = [
    "Ten",
    "Zetsu",
    "Ren",
    "Hatsu",
    "Gyo",
    "Shu",
    "Ko",
    "Ken",
    "En",
    "Ryu",
]

PROGRESSION_WEIGHT_PRESETS = {
    "slow": 0.75,
    "normal": 1.0,
    "fast": 1.25,
}

ARCHETYPE_CAPS = {
    "Fortification": {
        "Fortification": 100,
        "Transmutation": 80,
        "Conjuration": 60,
        "Emission": 80,
        "Manipulation": 60,
        "Specialization": 0,
    },
    "Transmutation": {
        "Fortification": 80,
        "Transmutation": 100,
        "Conjuration": 80,
        "Emission": 60,
        "Manipulation": 40,
        "Specialization": 0,
    },
    "Conjuration": {
        "Fortification": 60,
        "Transmutation": 80,
        "Conjuration": 100,
        "Emission": 40,
        "Manipulation": 60,
        "Specialization": 0,
    },
    "Emission": {
        "Fortification": 80,
        "Transmutation": 60,
        "Conjuration": 40,
        "Emission": 100,
        "Manipulation": 80,
        "Specialization": 0,
    },
    "Manipulation": {
        "Fortification": 60,
        "Transmutation": 40,
        "Conjuration": 60,
        "Emission": 80,
        "Manipulation": 100,
        "Specialization": 0,
    },
    "Specialization": {
        "Fortification": 40,
        "Transmutation": 60,
        "Conjuration": 80,
        "Emission": 60,
        "Manipulation": 80,
        "Specialization": 100,
    },
}

REIATSU_COL_MAP = {
    "Fortification": ("fortification_affinity", "fortification_xp"),
    "Transmutation": ("transmutation_affinity", "transmutation_xp"),
    "Conjuration": ("conjuration_affinity", "conjuration_xp"),
    "Emission": ("emission_affinity", "emission_xp"),
    "Manipulation": ("manipulation_affinity", "manipulation_xp"),
    "Specialization": ("specialization_affinity", "specialization_xp"),
}

def sanitize_input(input_str):
    if not re.match(r"^[a-zA-Z0-9\s]*$", input_str):
        return False
    return True

def apply_layout(user_id, title, description):
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


def extract_first_int(text, default=0):
    match = re.search(r"\d+", text or "")
    if not match:
        return default
    return int(match.group())


def normalize_lookup_text(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())

passives = {
    "Rare": [
        "Aumenta o XP ganho em 5%", 
        "Reduz o tempo de recarga em 3%", 
        "Aumenta a precisão em 2%", 
        "Chance de evasão aumentada em 3%", 
        "Efeito garantido em 10% dos usos",
        "Aumenta a chance de sucesso de efeitos de controle em 5%",
        "Aumenta a recuperação de energia em 2%"
    ],
    "Epic": [
        "Aumenta o XP ganho em 10%", 
        "Reduz o tempo de recarga em 5%", 
        "Dano crítico aumenta em 15%", 
        "Chance de golpe crítico aumenta em 10%", 
        "Aumenta a chance de aplicar debuffs em 8%", 
        "Reduz efeitos negativos sofridos em 5%", 
        "Ataques ignoram 5% da defesa do oponente"
    ],
    "Legendary": [
        "Duplica o XP ganho por uso", 
        "Reduz o tempo de recarga em 10%", 
        "Chance de golpe crítico aumenta em 25%", 
        "Todos os debuffs têm efeito garantido uma vez por combate",
        "Aumenta a resistência a controle de grupo em 15%", 
        "Chance de aplicar efeitos negativos adicionais em 10%", 
        "Recupera 5% da energia após usar uma habilidade"
    ],
    "Mythical": [
        "Triplica o XP ganho por uso", 
        "Reduz o tempo de recarga em 20%", 
        "Dano crítico aumenta em 50%", 
        "Efeitos de controle e debuffs são ineficazes por 5 segundos após o uso",
        "Chance de anular efeitos negativos do oponente em 25%", 
        "Aumenta todos os atributos temporariamente em 10% após usar uma habilidade",
        "Chance de recarregar instantaneamente uma habilidade ao usá-la"
    ]
}

rarity_probabilities = {
    "F-": {"Rare": 100, "Epic": 0, "Legendary": 0, "Mythical": 0},
    "F": {"Rare": 90, "Epic": 10, "Legendary": 0, "Mythical": 0},
    "E-": {"Rare": 80, "Epic": 15, "Legendary": 5, "Mythical": 0},
    "D-": {"Rare": 70, "Epic": 20, "Legendary": 10, "Mythical": 0},
    "C": {"Rare": 50, "Epic": 35, "Legendary": 15, "Mythical": 0},
    "B": {"Rare": 40, "Epic": 40, "Legendary": 20, "Mythical": 0},
    "A": {"Rare": 30, "Epic": 30, "Legendary": 30, "Mythical": 10},
    "S-": {"Rare": 20, "Epic": 30, "Legendary": 35, "Mythical": 15},
    "S": {"Rare": 10, "Epic": 20, "Legendary": 35, "Mythical": 35},
    "Z": {"Rare": 0, "Epic": 20, "Legendary": 30, "Mythical": 50},
}

class Techniques(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = False
        self.ensure_runtime_schema()
        self._ensure_webhook_toggle_table()
        self._load_webhook_toggle_state()

    async def cog_load(self):
        if not self.reiryoku_regen_loop.is_running():
            self.reiryoku_regen_loop.start()

    async def cog_unload(self):
        if self.reiryoku_regen_loop.is_running():
            self.reiryoku_regen_loop.cancel()

    @tasks.loop(seconds=REGEN_INTERVAL_SECONDS)
    async def reiryoku_regen_loop(self):
        for attempt in range(SQLITE_LOCK_RETRIES):
            try:
                updated_rows = 0
                with create_db_connection() as regen_conn:
                    regen_cursor = regen_conn.cursor()
                    regen_cursor.execute(
                        """
                        SELECT character_id, reiryoku_base_pool, reiryoku_current, core_stability, control_score
                        FROM character_reiryoku
                        """
                    )
                    rows = regen_cursor.fetchall()

                    for row in rows:
                        if not row or len(row) < 5:
                            continue

                        character_id, max_pool, current_pool, stability, control_score = row

                        if max_pool is None:
                            continue

                        try:
                            max_pool = float(max_pool)
                            current_pool = float(current_pool or 0.0)
                            stability = self._clamp(float(stability or 0.0), 0.0, 100.0)
                            control_score = self._clamp(float(control_score or 0.0), 0.0, 100.0)
                        except (TypeError, ValueError):
                            continue

                        if max_pool <= 0:
                            continue

                        effective_max_pool, effective_current_pool, reiryoku_multiplier = get_effective_reiryoku_values(
                            character_id=character_id,
                            base_pool=max_pool,
                            current_pool=current_pool,
                        )
                        
                        # Cap em 150 se tem "reiryoku aumentado"
                        from services.characteristics_service import get_reiryoku_multiplier
                        if get_reiryoku_multiplier(character_id) > 1.0:
                            effective_max_pool = min(effective_max_pool, 150.0)
                        
                        if effective_max_pool <= 0:
                            continue

                        stability_factor = 0.7 + (stability / 100.0) * 0.3
                        regen = BASE_REGEN * (0.5 + control_score / 200.0) * stability_factor
                        new_effective_pool = min(effective_max_pool, effective_current_pool + regen)

                        if abs(new_effective_pool - effective_current_pool) < 0.01:
                            continue

                        new_stored_pool = new_effective_pool / max(1.0, reiryoku_multiplier)
                        new_stored_pool = self._clamp(new_stored_pool, 0.0, max_pool)

                        regen_cursor.execute(
                            """
                            UPDATE character_reiryoku
                            SET reiryoku_current=?, updated_at=CURRENT_TIMESTAMP
                            WHERE character_id=?
                            """,
                            (new_stored_pool, character_id),
                        )
                        updated_rows += 1

                    regen_conn.commit()

                if updated_rows:
                    print(f"[tecnicas] regen atualizado para {updated_rows} personagens")
                return
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower() or attempt >= SQLITE_LOCK_RETRIES - 1:
                    print(f"[tecnicas] erro no regen: {exc}")
                    raise
                print(f"[tecnicas] banco travado no regen, retry {attempt + 1}/{SQLITE_LOCK_RETRIES}")
                await asyncio.sleep(SQLITE_LOCK_DELAY_SECONDS * (attempt + 1))

    @reiryoku_regen_loop.before_loop
    async def before_reiryoku_regen_loop(self):
        await self.bot.wait_until_ready()

    def ensure_runtime_schema(self):
        main_module = sys.modules.get("__main__")
        ensure_schema = getattr(main_module, "ensure_soul_runtime_schema", None)
        if callable(ensure_schema):
            ensure_schema()
        self._ensure_column("character_reiryoku_skills", "skill_xp", "REAL DEFAULT 0.0")
        conn.commit()

    def _ensure_webhook_toggle_table(self):
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_runtime_flags (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.commit()

    def _load_webhook_toggle_state(self):
        c.execute("SELECT value FROM bot_runtime_flags WHERE key='techniques_webhook_active'")
        row = c.fetchone()
        self.active = bool(row and str(row[0]).strip() == "1")

    def _save_webhook_toggle_state(self):
        c.execute(
            """
            INSERT INTO bot_runtime_flags (key, value)
            VALUES ('techniques_webhook_active', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            ("1" if self.active else "0",),
        )
        conn.commit()

    def _find_character_by_webhook_name(self, webhook_name):
        webhook_name = (webhook_name or "").strip()
        if not webhook_name:
            return None

        c.execute(
            """
            SELECT c.character_id, c.user_id, COALESCE(p.message_count, 0), c.name
            FROM characters c
            LEFT JOIN character_progression p ON c.character_id = p.character_id
            WHERE c.name COLLATE NOCASE=?
            """,
            (webhook_name,),
        )
        row = c.fetchone()
        if row:
            return row

        normalized_webhook = normalize_lookup_text(webhook_name)
        c.execute(
            """
            SELECT c.character_id, c.user_id, COALESCE(p.message_count, 0), c.name
            FROM characters c
            LEFT JOIN character_progression p ON c.character_id = p.character_id
            """
        )
        for candidate in c.fetchall():
            if normalize_lookup_text(candidate[3]) == normalized_webhook:
                return candidate

        return None

    def _ensure_column(self, table_name, column_name, ddl):
        c.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in c.fetchall()]
        if column_name not in columns:
            c.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}")

    def _clamp(self, value, min_value, max_value):
        return max(min_value, min(max_value, value))

    def _normalize_category(self, category):
        if not category:
            return None
        cat = str(category).strip().lower()
        mapping = {
            "fortification": "Fortification",
            "fortificacao": "Fortification",
            "fortificação": "Fortification",
            "transmutation": "Transmutation",
            "transmutacao": "Transmutation",
            "transmutação": "Transmutation",
            "conjuration": "Conjuration",
            "conjuracao": "Conjuration",
            "conjuração": "Conjuration",
            "emission": "Emission",
            "emissao": "Emission",
            "emissão": "Emission",
            "manipulation": "Manipulation",
            "manipulacao": "Manipulation",
            "manipulação": "Manipulation",
            "specialization": "Specialization",
            "especialista": "Specialization",
            "especialização": "Specialization",
            "especializacao": "Specialization",
        }
        return mapping.get(cat)

    def _get_cap(self, primary_type, target_category, specialization_unlocked, character_id=None):
        primary = self._normalize_category(primary_type) or "Fortification"
        target = self._normalize_category(target_category)
        if not target:
            return 0

        caps = ARCHETYPE_CAPS.get(primary, ARCHETYPE_CAPS["Fortification"])
        cap = int(caps.get(target, 0))

        if target == "Specialization" and not int(specialization_unlocked or 0) and not allows_specialization(character_id or 0):
            return 0

        return max(0, cap)

    def _compatibility_coef_from_cap(self, cap):
        if cap >= 100:
            return 1.0
        if cap >= 80:
            return 0.75
        if cap >= 60:
            return 0.5
        if cap >= 40:
            return 0.25
        return 0.0

    def _compute_reiatsu_xp_gain(self, mastery, progression_weight, control_score, stability, load_ratio, coef_compatibilidade):
        if coef_compatibilidade <= 0:
            return 0

        progression_weight = self._clamp(float(progression_weight or 1.0), 0.5, 1.5)
        control_score = self._clamp(float(control_score or 0.0), 0.0, 100.0)
        stability = self._clamp(float(stability or 0.0), 0.0, 100.0)
        load_ratio = self._clamp(float(load_ratio or 0.0), 0.0, 2.0)

        coef_mastery = max(0.75, 1.0 - (float(mastery or 0.0) / 3000.0))
        control_factor = 0.5 + (control_score / 200.0)
        stability_factor = 0.7 + (stability / 100.0) * 0.3
        load_penalty = max(0.7, 1.0 - load_ratio)

        xp_gain = GAIN_BASE
        xp_gain *= coef_compatibilidade
        xp_gain *= coef_mastery
        xp_gain *= progression_weight
        xp_gain *= control_factor
        xp_gain *= stability_factor
        xp_gain *= load_penalty
        xp_gain = min(xp_gain, GAIN_BASE * 2.0)

        return max(1, int(round(xp_gain)))

    def _ensure_reiatsu_profile(self, character_id):
        c.execute(
            """
            SELECT primary_category, primary_type
            FROM character_reiatsu_affinities
            WHERE character_id=?
            """,
            (character_id,),
        )
        row = c.fetchone()

        if not row:
            c.execute(
                """
                INSERT INTO character_reiatsu_affinities (
                    character_id, primary_category, primary_type, primary_category_level
                ) VALUES (?, 'Fortification', 'Fortification', 1)
                """,
                (character_id,),
            )
            return

        primary_category, primary_type = row
        if not primary_type:
            primary_type = self._normalize_category(primary_category) or "Fortification"
            c.execute(
                "UPDATE character_reiatsu_affinities SET primary_type=?, updated_at=CURRENT_TIMESTAMP WHERE character_id=?",
                (primary_type, character_id),
            )

    def _get_default_reiatsu_category(self, character_id):
        c.execute(
            "SELECT primary_type, primary_category FROM character_reiatsu_affinities WHERE character_id=?",
            (character_id,),
        )
        row = c.fetchone()
        if not row:
            return "Fortification"
        return self._normalize_category(row[0]) or self._normalize_category(row[1]) or "Fortification"

    def _apply_reiatsu_progression(self, character_id, mastery, reiatsu_category, progression_weight):
        target_category = self._normalize_category(reiatsu_category)
        if not target_category:
            return 0

        self._ensure_reiatsu_profile(character_id)

        c.execute(
            """
            SELECT primary_type, specialization_unlocked,
                   fortification_affinity, transmutation_affinity, conjuration_affinity,
                   emission_affinity, manipulation_affinity, specialization_affinity,
                   fortification_xp, transmutation_xp, conjuration_xp,
                   emission_xp, manipulation_xp, specialization_xp
            FROM character_reiatsu_affinities
            WHERE character_id=?
            """,
            (character_id,),
        )
        reiatsu = c.fetchone()
        if not reiatsu:
            return 0

        (
            primary_type,
            specialization_unlocked,
            fortification_affinity,
            transmutation_affinity,
            conjuration_affinity,
            emission_affinity,
            manipulation_affinity,
            specialization_affinity,
            fortification_xp,
            transmutation_xp,
            conjuration_xp,
            emission_xp,
            manipulation_xp,
            specialization_xp,
        ) = reiatsu

        c.execute(
            """
            SELECT reiryoku_base_pool, reiryoku_current, core_stability, control_score, load_ratio
            FROM character_reiryoku
            WHERE character_id=?
            """,
            (character_id,),
        )
        core = c.fetchone()
        if not core:
            return 0

        max_pool, current_pool, stability, control_score, load_ratio = core
        cap = self._get_cap(primary_type, target_category, specialization_unlocked, character_id=character_id)
        coef_compat = self._compatibility_coef_from_cap(cap)
        gained_xp = self._compute_reiatsu_xp_gain(
            mastery=mastery,
            progression_weight=progression_weight,
            control_score=control_score,
            stability=stability,
            load_ratio=load_ratio,
            coef_compatibilidade=coef_compat,
        )

        if cap <= 0 or gained_xp <= 0:
            return 0

        aff_col, xp_col = REIATSU_COL_MAP[target_category]

        xp_values = {
            "fortification_xp": float(fortification_xp or 0.0),
            "transmutation_xp": float(transmutation_xp or 0.0),
            "conjuration_xp": float(conjuration_xp or 0.0),
            "emission_xp": float(emission_xp or 0.0),
            "manipulation_xp": float(manipulation_xp or 0.0),
            "specialization_xp": float(specialization_xp or 0.0),
        }

        old_xp = xp_values.get(xp_col, 0.0)
        new_xp = old_xp + gained_xp
        xp_values[xp_col] = new_xp

        xp_to_cap = BASE_XP_PER_CAP * cap
        new_affinity = int(math.floor(cap * (new_xp / xp_to_cap))) if xp_to_cap > 0 else 0
        new_affinity = int(self._clamp(new_affinity, 0, cap))

        c.execute(
            f"""
            UPDATE character_reiatsu_affinities
            SET {xp_col}=?, {aff_col}=?,
                fortification_xp=?, transmutation_xp=?, conjuration_xp=?,
                emission_xp=?, manipulation_xp=?, specialization_xp=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE character_id=?
            """,
            (
                new_xp,
                new_affinity,
                xp_values["fortification_xp"],
                xp_values["transmutation_xp"],
                xp_values["conjuration_xp"],
                xp_values["emission_xp"],
                xp_values["manipulation_xp"],
                xp_values["specialization_xp"],
                character_id,
            ),
        )

        return gained_xp

    def _apply_core_usage_for_reiatsu(self, character_id, energy_cost, reiatsu_category):
        c.execute(
            """
            SELECT reiryoku_base_pool, reiryoku_current, core_stability, control_score, load_ratio
            FROM character_reiryoku
            WHERE character_id=?
            """,
            (character_id,),
        )
        core = c.fetchone()
        if not core:
            return

        max_pool, current_pool, stability, control_score, load_ratio = core

        try:
            max_pool = float(max_pool or 0.0)
            current_pool = float(current_pool or 0.0)
            stability = float(stability or 0.0)
            control_score = float(control_score or 0.0)
            load_ratio = self._clamp(float(load_ratio or 0.0), 0.0, 2.0)
            energy_cost = float(energy_cost or 0.0)
        except (TypeError, ValueError):
            return

        if max_pool <= 0:
            return

        effective_max_pool, effective_current_pool, reiryoku_multiplier = get_effective_reiryoku_values(
            character_id=character_id,
            base_pool=max_pool,
            current_pool=current_pool,
        )
        
        # Cap em 150 se tem "reiryoku aumentado"
        from services.characteristics_service import get_reiryoku_multiplier
        if get_reiryoku_multiplier(character_id) > 1.0:
            effective_max_pool = min(effective_max_pool, 150.0)
        
        if effective_max_pool <= 0:
            return

        # Decay ocorre somente no uso de técnica de Reiatsu.
        load_ratio = max(0.0, load_ratio * 0.95)
        load_ratio += energy_cost / effective_max_pool

        effective_current_pool = self._clamp(effective_current_pool - energy_cost, 0.0, effective_max_pool)
        current_pool = self._clamp(effective_current_pool / max(1.0, reiryoku_multiplier), 0.0, max_pool)

        target_category = self._normalize_category(reiatsu_category)
        self._ensure_reiatsu_profile(character_id)
        c.execute("SELECT primary_type FROM character_reiatsu_affinities WHERE character_id=?", (character_id,))
        row = c.fetchone()
        primary_type = self._normalize_category(row[0]) if row and row[0] else "Fortification"

        if target_category and target_category == primary_type:
            stability += 0.2
            control_score += 0.3
        elif target_category:
            stability += 0.05
            control_score += 0.1

        if load_ratio > 1.0:
            overload = load_ratio - 1.0
            stability -= overload * 0.5
            control_score -= overload * 0.4

        stability = self._clamp(stability, 0.0, 100.0)
        control_score = self._clamp(control_score, 0.0, 100.0)
        load_ratio = self._clamp(load_ratio, 0.0, 2.0)

        c.execute(
            """
            UPDATE character_reiryoku
            SET reiryoku_current=?, core_stability=?, control_score=?, load_ratio=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE character_id=?
            """,
            (current_pool, stability, control_score, load_ratio, character_id),
        )

    def _apply_core_usage_for_skill(self, character_id, energy_cost):
        c.execute(
            """
            SELECT reiryoku_base_pool, reiryoku_current, core_stability, control_score, load_ratio
            FROM character_reiryoku
            WHERE character_id=?
            """,
            (character_id,),
        )
        core = c.fetchone()
        if not core:
            return

        max_pool, current_pool, stability, control_score, load_ratio = core

        try:
            max_pool = float(max_pool or 0.0)
            current_pool = float(current_pool or 0.0)
            stability = float(stability or 0.0)
            control_score = float(control_score or 0.0)
            load_ratio = self._clamp(float(load_ratio or 0.0), 0.0, 2.0)
            energy_cost = float(energy_cost or 0.0)
        except (TypeError, ValueError):
            return

        if max_pool <= 0:
            return

        effective_max_pool, effective_current_pool, reiryoku_multiplier = get_effective_reiryoku_values(
            character_id=character_id,
            base_pool=max_pool,
            current_pool=current_pool,
        )

        from services.characteristics_service import get_reiryoku_multiplier
        if get_reiryoku_multiplier(character_id) > 1.0:
            effective_max_pool = min(effective_max_pool, 150.0)

        if effective_max_pool <= 0:
            return

        # Uso de skill-base gera menos estresse que técnicas de Reiatsu.
        load_ratio = max(0.0, load_ratio * 0.97)
        load_ratio += energy_cost / effective_max_pool

        effective_current_pool = self._clamp(effective_current_pool - energy_cost, 0.0, effective_max_pool)
        current_pool = self._clamp(effective_current_pool / max(1.0, reiryoku_multiplier), 0.0, max_pool)

        stability += 0.1
        control_score += 0.15

        if load_ratio > 1.0:
            overload = load_ratio - 1.0
            stability -= overload * 0.35
            control_score -= overload * 0.3

        stability = self._clamp(stability, 0.0, 100.0)
        control_score = self._clamp(control_score, 0.0, 100.0)
        load_ratio = self._clamp(load_ratio, 0.0, 2.0)

        c.execute(
            """
            UPDATE character_reiryoku
            SET reiryoku_current=?, core_stability=?, control_score=?, load_ratio=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE character_id=?
            """,
            (current_pool, stability, control_score, load_ratio, character_id),
        )

    def _is_base_skill_used(self, skill_name, bolded_texts, hashtag_texts, normalized_message):
        token = normalize_lookup_text(skill_name)
        if not token:
            return False

        pattern = r"\\b" + re.escape(token) + r"\\b"

        for text in bolded_texts:
            if re.search(pattern, normalize_lookup_text(text)):
                return True

        for text in hashtag_texts:
            if re.search(pattern, normalize_lookup_text(text)):
                return True

        return bool(re.search(pattern, normalized_message or ""))

    def _compute_reiryoku_skill_xp_gain(self, character_id, mastery_level, control_level):
        mastery_level = int(self._clamp(float(mastery_level or 0.0), 0.0, 100.0))
        control_level = int(self._clamp(float(control_level or 0.0), 0.0, 100.0))
        mastery_multiplier = get_mastery_multiplier(character_id)
        base_gain = 6.0 + (mastery_level * 0.14) + (control_level * 0.05)
        return max(1.0, base_gain * mastery_multiplier)

    def _apply_reiryoku_skill_progression(self, character_id, skill_name, mastery_level, control_level, usage_count, skill_xp):
        mastery_level = int(self._clamp(float(mastery_level or 0.0), 0.0, 100.0))
        control_level = int(self._clamp(float(control_level or 0.0), 0.0, 100.0))
        usage_count = int(usage_count or 0)
        skill_xp = float(skill_xp or 0.0)

        usage_count += 1
        gained_xp = self._compute_reiryoku_skill_xp_gain(character_id, mastery_level, control_level)
        skill_xp += gained_xp

        while mastery_level < 100:
            xp_needed = 100 + (mastery_level * 20)
            if skill_xp < xp_needed:
                break
            skill_xp -= xp_needed
            mastery_level += 1

        # Controle acompanha mastery em ritmo mais lento.
        target_control = mastery_level // 2
        if target_control > control_level:
            control_level = int(self._clamp(target_control, 0, 100))

        return {
            "mastery_level": mastery_level,
            "control_level": control_level,
            "usage_count": usage_count,
            "skill_xp": skill_xp,
            "gained_xp": gained_xp,
        }

    async def send_embed(self, ctx, title, description, color=discord.Color.blue(), image_url=None, next_step=None):
        if next_step:
            description = f"{description}\n\n- > **Próximo passo:** {next_step}"
        embed = discord.Embed(title=title, description=description, color=color)
        if image_url:
            embed.set_image(url=image_url)
        await ctx.send(embed=embed)

    def calculate_new_mastery(self, xp, mastery):
        """Calcula a experiência e o nível de mastery"""
        xp_needed = 100 + (mastery * 20)
        while xp >= xp_needed:
            mastery += 1
            xp -= xp_needed
            xp_needed = 100 + (mastery * 20)
        return xp, mastery

    def get_xp_gain(self, mastery, passive=None):
        base_xp = random.randint(5, 15) 
        mastery_multiplier = 1 + (mastery / 200)  
        total_xp = base_xp * mastery_multiplier

        if passive and "XP ganho em" in passive:
            bonus = extract_first_int(passive) / 100
            total_xp *= (1 + bonus)

        return int(total_xp)

    def update_rank(self, mastery):
        """Atualiza o rank de uma técnica com base em seu mastery"""
        RANKS = {
            'F-': 0, 'F': 10, 'F+': 20, 'E-': 40, 'E': 60, 'E+': 80, 'D-': 100, 'D': 150, 'D+': 200, 'C-': 250, 'C': 300, 'C+': 350, 'B-': 400, 'B': 450, 'B+': 500, 'A-': 520, 'A': 540, 'A+': 560, 'S': 580, 'SS': 590, 'SSS': 600
        }

        for rank, mastery_required in sorted(RANKS.items(), key=lambda item: item[1]):
            if mastery < mastery_required:
                return rank
        return 'Z'

    def get_passive_by_rank(self, rank):
        """Obtém uma passiva com base no rank"""
        probabilities = rarity_probabilities[rank]
        rarity = random.choices(
            population=["Rare", "Epic", "Legendary", "Mythical"],
            weights=[probabilities["Rare"], probabilities["Epic"], probabilities["Legendary"], probabilities["Mythical"]],
            k=1
        )[0]
        passive = random.choice(passives[rarity])
        return rarity, passive

    async def process_webhook(self, message):
        """Processa os webhooks e o uso de técnicas"""

        webhook_name = (message.author.name or "").strip()
        text_parts = [message.content or ""]
        for embed in (message.embeds or []):
            if getattr(embed, "title", None):
                text_parts.append(str(embed.title))
            if getattr(embed, "description", None):
                text_parts.append(str(embed.description))
            for field in getattr(embed, "fields", []) or []:
                if getattr(field, "name", None):
                    text_parts.append(str(field.name))
                if getattr(field, "value", None):
                    text_parts.append(str(field.value))

        message_content = "\n".join([part for part in text_parts if part]).strip()

        character_data = self._find_character_by_webhook_name(webhook_name)

        if not character_data:
            return None

        character_id, user_id, message_count, canonical_character_name = character_data
        message_count = int(message_count or 0)
        user = await self.bot.fetch_user(user_id)
        db_cursor = conn.cursor()
        bolded_texts = re.findall(r'\*\*(.*?)\*\*', message_content)
        hashtag_texts = re.findall(r'#\s*(.*)', message_content)
        normalized_message = normalize_lookup_text(message_content)
        processed_techniques = set()
        success_messages = []
        passive_triggered_message = None
        pending_passive_choice = None

        for attempt in range(SQLITE_LOCK_RETRIES):
            try:
                conn.execute("BEGIN IMMEDIATE")

                db_cursor.execute(
                    """
                    INSERT OR IGNORE INTO character_progression (character_id, experience, level, rank, points_available, message_count)
                    VALUES (?, 0, 1, 'F-', 0, 0)
                    """,
                    (character_id,),
                )

                db_cursor.execute(
                    "UPDATE character_progression SET message_count=?, updated_at=CURRENT_TIMESTAMP WHERE character_id=?",
                    (message_count + 1, character_id),
                )

                db_cursor.execute(
                    """
                    SELECT technique_name, xp, mastery, usage_count, passive,
                           COALESCE(power_system, 'reiatsu') AS power_system,
                           reiatsu_category,
                           COALESCE(progression_weight, 1.0) AS progression_weight,
                           COALESCE(energy_cost, 10.0) AS energy_cost
                    FROM techniques
                    WHERE character_id=?
                    """,
                    (character_id,),
                )
                techniques = db_cursor.fetchall()

                for technique_name, xp, mastery, usage_count, current_passive, power_system, reiatsu_category, progression_weight, energy_cost in techniques:
                    technique_found = False
                    normalized_technique_name = normalize_lookup_text(technique_name)

                    for bolded_text in bolded_texts:
                        if normalized_technique_name in normalize_lookup_text(bolded_text):
                            technique_found = True
                            break

                    if not technique_found:
                        for hashtag_text in hashtag_texts:
                            if normalized_technique_name in normalize_lookup_text(hashtag_text):
                                technique_found = True
                                break

                    # Fallback: permite detectar uso da técnica em texto normal
                    # sem exigir markdown em negrito ou hashtag.
                    if not technique_found and normalized_technique_name and normalized_technique_name in normalized_message:
                        technique_found = True

                    if not technique_found or technique_name.lower() in processed_techniques:
                        continue

                    usage_count += 1
                    mastery_multiplier = get_mastery_multiplier(character_id)
                    gained_xp = int(round(self.get_xp_gain(mastery, current_passive) * mastery_multiplier))
                    new_xp = xp + max(1, gained_xp)
                    new_xp, new_mastery = self.calculate_new_mastery(new_xp, mastery)

                    normalized_system = str(power_system or "reiatsu").strip().lower()
                    if normalized_system not in VALID_POWER_SYSTEMS:
                        normalized_system = "reiatsu"

                    if normalized_system == "reiatsu":
                        if not self._normalize_category(reiatsu_category):
                            reiatsu_category = self._get_default_reiatsu_category(character_id)
                        self._apply_reiatsu_progression(
                            character_id=character_id,
                            mastery=mastery,
                            reiatsu_category=reiatsu_category,
                            progression_weight=progression_weight,
                        )
                        self._apply_core_usage_for_reiatsu(
                            character_id=character_id,
                            energy_cost=energy_cost,
                            reiatsu_category=reiatsu_category,
                        )

                    current_rank = self.update_rank(mastery)
                    new_rank = self.update_rank(new_mastery)

                    passive_result = self.check_and_apply_passive(current_passive, technique_name)
                    if passive_result and passive_triggered_message is None:
                        passive_triggered_message = passive_result

                    if new_rank != current_rank:
                        rarity, new_passive = self.get_passive_by_rank(new_rank)
                        if new_passive != current_passive and pending_passive_choice is None:
                            pending_passive_choice = (technique_name, new_passive, rarity, current_passive, new_rank)

                    db_cursor.execute(
                        """
                        UPDATE techniques
                        SET xp=?, mastery=?, usage_count=?, passive=?,
                            power_system=?, reiatsu_category=?, progression_weight=?, energy_cost=?
                        WHERE character_id=? AND technique_name COLLATE NOCASE=?
                        """,
                        (
                            new_xp,
                            new_mastery,
                            usage_count,
                            current_passive,
                            normalized_system,
                            self._normalize_category(reiatsu_category) if normalized_system == "reiatsu" else None,
                            self._clamp(float(progression_weight or 1.0), 0.5, 1.5),
                            float(energy_cost or 10.0),
                            character_id,
                            technique_name,
                        ),
                    )

                    processed_techniques.add(technique_name.lower())
                    success_messages.append(
                        f"- > **Técnica __`{technique_name}`__ usada! __`{canonical_character_name}`__ ganhou XP. Mastery agora é __`{new_mastery}`__, Rank agora é __`{new_rank}`__.**"
                    )

                db_cursor.execute(
                    """
                    SELECT skill_name,
                           COALESCE(mastery_level, 0) AS mastery_level,
                           COALESCE(control_level, 0) AS control_level,
                           COALESCE(usage_count, 0) AS usage_count,
                           COALESCE(skill_xp, 0.0) AS skill_xp,
                           COALESCE(is_awakened, 0) AS is_awakened
                    FROM character_reiryoku_skills
                    WHERE character_id=?
                    """,
                    (character_id,),
                )
                skill_rows = db_cursor.fetchall()
                base_skills_normalized = {normalize_lookup_text(x) for x in REIRYOKU_BASE_SKILLS}

                for skill_name, mastery_level, control_level, usage_count, skill_xp, is_awakened in skill_rows:
                    normalized_skill = normalize_lookup_text(skill_name)
                    if normalized_skill not in base_skills_normalized:
                        continue

                    if not bool(is_awakened):
                        continue

                    if not self._is_base_skill_used(skill_name, bolded_texts, hashtag_texts, normalized_message):
                        continue

                    progression = self._apply_reiryoku_skill_progression(
                        character_id=character_id,
                        skill_name=skill_name,
                        mastery_level=mastery_level,
                        control_level=control_level,
                        usage_count=usage_count,
                        skill_xp=skill_xp,
                    )

                    skill_energy_cost = 4.0 + (progression["mastery_level"] * 0.08)
                    self._apply_core_usage_for_skill(character_id=character_id, energy_cost=skill_energy_cost)

                    db_cursor.execute(
                        """
                        UPDATE character_reiryoku_skills
                        SET mastery_level=?, control_level=?, usage_count=?, skill_xp=?, updated_at=CURRENT_TIMESTAMP
                        WHERE character_id=? AND skill_name=?
                        """,
                        (
                            progression["mastery_level"],
                            progression["control_level"],
                            progression["usage_count"],
                            progression["skill_xp"],
                            character_id,
                            skill_name,
                        ),
                    )

                    success_messages.append(
                        f"- > **Skill-base __`{skill_name}`__ usada! +{progression['gained_xp']:.1f} XP. Mastery: __`{progression['mastery_level']}`__, Controle: __`{progression['control_level']}`__.**"
                    )

                conn.commit()
                break
            except sqlite3.OperationalError as exc:
                conn.rollback()
                if "locked" not in str(exc).lower() or attempt >= SQLITE_LOCK_RETRIES - 1:
                    print(f"[tecnicas] erro em process_webhook: {exc}")
                    raise
                print(f"[tecnicas] banco travado em process_webhook, retry {attempt + 1}/{SQLITE_LOCK_RETRIES}")
                await asyncio.sleep(SQLITE_LOCK_DELAY_SECONDS * (attempt + 1))
            except Exception:
                conn.rollback()
                raise

        if passive_triggered_message:
            await message.channel.send(passive_triggered_message)

        for success_message in success_messages:
            await user.send(success_message)

        if pending_passive_choice:
            technique_name, new_passive, rarity, current_passive, new_rank = pending_passive_choice
            await user.send(
                f"- > **Você evoluiu para o rank {new_rank}! Nova passiva disponível: {new_passive} ({rarity}).**\n"
                f"**Passiva atual: {current_passive or 'Nenhuma'}**.\n"
                f"**Deseja trocar? Responda com 'sim' ou 'não'.**"
            )

            def check(m):
                return m.author == user and m.content.lower() in ['sim', 'não']

            try:
                response = await self.bot.wait_for('message', check=check, timeout=30.0)
                if response.content.lower() == 'sim':
                    try:
                        conn.execute("BEGIN IMMEDIATE")
                        c.execute(
                            "UPDATE techniques SET passive=? WHERE character_id=? AND technique_name COLLATE NOCASE=?",
                            (new_passive, character_id, technique_name),
                        )
                        conn.commit()
                        await user.send(f"- > **Passiva trocada! Agora sua passiva é: {new_passive}**.")
                    except sqlite3.OperationalError as exc:
                        conn.rollback()
                        print(f"[tecnicas] erro ao atualizar passiva: {exc}")
            except asyncio.TimeoutError:
                await user.send("- > **Tempo esgotado. Mantendo a passiva atual.**")

        return None

    def check_and_apply_passive(self, passive, technique_name):
        """Aplica passivas com base em suas chances e retorna mensagens específicas."""
        if passive:
            if "dano crítico" in passive:
                chance = extract_first_int(passive)
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} causou __dano crítico!__**"

            if "Chance de evasão aumentada" in passive:
                chance = extract_first_int(passive)
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} teve __uma evasão incrível!__**"

            if "Efeito garantido" in passive:
                chance = extract_first_int(passive)
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} teve __um acerto garantido!__**"

            if "Chance de aplicar debuffs" in passive:
                chance = extract_first_int(passive)
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} aplicou __um debuff!__**"

            if "Reduz o tempo de recarga" in passive:
                reduction = extract_first_int(passive)
                return f"- > **{technique_name} teve __o tempo de recarga reduzido em {reduction}%!__**"

            if "Aumenta a precisão" in passive:
                precision_increase = extract_first_int(passive)
                return f"- > **{technique_name} teve __a precisão aumentada em {precision_increase}%!__**"

            if "Aumenta a chance de sucesso de efeitos de controle" in passive:
                control_increase = extract_first_int(passive)
                return f"- > **{technique_name} teve __a chance de controle aumentada em {control_increase}%!__**"

            if "Aumenta a recuperação de energia" in passive:
                energy_recovery = extract_first_int(passive)
                return f"- > **{technique_name} recuperou __{energy_recovery}% de energia!__**"

            if "Ataques ignoram" in passive:
                defense_ignored = extract_first_int(passive)
                return f"- > **{technique_name} ignorou __{defense_ignored}% da defesa do oponente!__**"

            if "Recupera" in passive and "energia" in passive:
                energy_recovery = extract_first_int(passive)
                return f"- > **{technique_name} recuperou __{energy_recovery}% de energia após o uso!__**"

            if "Chance de anular efeitos negativos" in passive:
                chance = extract_first_int(passive)
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} __anulou efeitos negativos__ do oponente!**"

            if "Aumenta todos os atributos temporariamente" in passive:
                attribute_increase = extract_first_int(passive)
                return f"- > **{technique_name} aumentou todos os atributos em __{attribute_increase}%__ temporariamente!**"

            if "Chance de recarregar instantaneamente" in passive:
                chance = extract_first_int(passive)
                if random.randint(1, 100) <= chance:
                    return f"- > **{technique_name} foi __recarregada instantaneamente!__**"

        return None

    @commands.command(name='activate', aliases=['webhook'])
    async def activate(self, ctx, mode: str = "toggle"):
        """Ativa, desativa, alterna ou mostra status da leitura de webhooks."""
        mode = (mode or "toggle").strip().lower()

        if mode in {"status", "state", "estado"}:
            status = "𝐀𝐓𝐈𝐕𝐀𝐃𝐎" if self.active else "𝐃𝐄𝐒𝐀𝐓𝐈𝐕𝐀𝐃𝐎"
            await ctx.send(f"- > **Leitura de webhooks está __`{status}`__.**")
            return

        if mode in {"on", "ativar", "true", "1"}:
            self.active = True
        elif mode in {"off", "desativar", "false", "0"}:
            self.active = False
        elif mode in {"toggle", "alternar"}:
            self.active = not self.active
        else:
            await ctx.send("- > **Uso:** `kill!activate [on|off|toggle|status]`")
            return

        self._save_webhook_toggle_state()
        status = "𝐀𝐓𝐈𝐕𝐀𝐃𝐎" if self.active else "𝐃𝐄𝐒𝐀𝐓𝐈𝐕𝐀𝐃𝐎"
        await ctx.send(f"- > **A funcionalidade de leitura de webhooks está agora __`{status}`__.**")

    @commands.command(name='webhookdebug', aliases=['techdebug'])
    async def webhook_debug(self, ctx):
        status = "ATIVADO" if self.active else "DESATIVADO"
        await ctx.send(
            "- > **Webhook debug**\n"
            f"- > Leitura: **{status}**\n"
            "- > O parser considera texto normal, negrito e campos de embed.\n"
            "- > Para um teste rápido, envie no webhook uma frase contendo exatamente o nome da técnica.\n"
            "- > Depois rode: `kill!showtechnique 'NomePersonagem' 'NomeTecnica'`"
        )

    def parse_args(self, args):
        """Função para parsear os argumentos"""
        parts = re.findall(r"'(.*?)'|(\S+)", args)
        return [''.join(filter(None, part)) for part in parts]

    @commands.command(name='addtechnique', aliases=['addtech', 'novatecnica'])
    async def add_technique(self, ctx, *, args: str):
        """Comando para adicionar uma técnica a um personagem"""
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!addtechnique 'Nome do Personagem' 'Nome da Técnica'**", discord.Color.red())
            return

        character_name, technique_name = parsed_args[0], ' '.join(parsed_args[1:])

        passive = "Nenhuma"

        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para adicionar técnicas a ele.**", discord.Color.red())
            return

        character_id = character[0]

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await self.send_embed(ctx, "**DESCRIÇÃO DA TÉCNICA**", "- > **Por favor, forneça a descrição da técnica.**")
        try:
            description_message = await self.bot.wait_for('message', check=check, timeout=60.0)
            description = description_message.content
            image_url = description_message.attachments[0].url if description_message.attachments else None

            power_systems_list = list(VALID_POWER_SYSTEMS)
            power_systems_str = "\n".join([f"**{i+1}. {sys}**" for i, sys in enumerate(power_systems_list)])
            await self.send_embed(ctx, "**TIPO DE PODER**", f"Escolha o tipo de poder:\n{power_systems_str}\n\n**Responda com o número (1-{len(power_systems_list)})**")
            
            power_system_message = await self.bot.wait_for('message', check=check, timeout=60.0)
            try:
                power_system_idx = int(power_system_message.content.strip()) - 1
                if 0 <= power_system_idx < len(power_systems_list):
                    power_system = power_systems_list[power_system_idx]
                else:
                    await self.send_embed(ctx, "**ERRO**", "- > **Número inválido. Usando reiatsu como padrão.**", discord.Color.orange())
                    power_system = "reiatsu"
            except ValueError:
                await self.send_embed(ctx, "**AVISO**", "- > **Resposta inválida. Usando reiatsu como padrão.**", discord.Color.orange())
                power_system = "reiatsu"

            reiatsu_category = None
            if power_system == "reiatsu":
                reiatsu_categories_str = "\n".join([f"**{i+1}. {cat}**" for i, cat in enumerate(VALID_REIATSU_CATEGORIES)])
                await self.send_embed(ctx, "**CATEGORIA DE REIATSU**", f"Escolha a categoria:\n{reiatsu_categories_str}\n\n**Responda com o número (1-{len(VALID_REIATSU_CATEGORIES)})**")
                
                reiatsu_message = await self.bot.wait_for('message', check=check, timeout=60.0)
                try:
                    reiatsu_idx = int(reiatsu_message.content.strip()) - 1
                    if 0 <= reiatsu_idx < len(VALID_REIATSU_CATEGORIES):
                        reiatsu_category = VALID_REIATSU_CATEGORIES[reiatsu_idx]
                    else:
                        reiatsu_category = self._get_default_reiatsu_category(character_id)
                except ValueError:
                    reiatsu_category = self._get_default_reiatsu_category(character_id)
            else:
                reiatsu_category = None

            default_role = "offense"
            default_progression_weight = PROGRESSION_WEIGHT_PRESETS["normal"]
            default_energy_cost = 10.0

            c.execute(
                """
                INSERT INTO techniques (
                    character_id, technique_name, user_id, image_url, description, passive,
                    power_system, reiatsu_category, technique_role, progression_weight, energy_cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    character_id,
                    technique_name,
                    ctx.author.id,
                    image_url,
                    description,
                    passive,
                    power_system,
                    reiatsu_category,
                    default_role,
                    default_progression_weight,
                    default_energy_cost,
                ),
            )
            conn.commit()
            await self.send_embed(
                ctx,
                "**__```𝐓𝐄́𝐂𝐍𝐈𝐂𝐀 𝐀𝐃𝐈𝐂𝐈𝐎𝐍𝐀𝐃𝐀```__**",
                f"- > **Técnica __`{technique_name}`__ adicionada ao personagem __`{character_name}`__.**",
                discord.Color.green(),
                image_url,
                "use `kill!assignability` para vincular em uma habilidade"
            )
        except asyncio.TimeoutError:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Tempo esgotado. Por favor, tente novamente.**", discord.Color.red())

    @commands.command(name='removetechnique', aliases=['deltech'])
    async def remove_technique(self, ctx, *, args: str):
        """Comando para remover uma técnica de um personagem"""
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!removetechnique 'Nome do Personagem' 'Nome da Técnica'**", discord.Color.red())
            return

        character_name, technique_name = parsed_args[0], ' '.join(parsed_args[1:])
        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para remover técnicas dele.**", discord.Color.red())
            return

        character_id = character[0]
        c.execute("DELETE FROM techniques WHERE character_id=? AND technique_name COLLATE NOCASE=?", 
                  (character_id, technique_name))
        if c.rowcount == 0:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada ou você não tem permissão para removê-la.**", discord.Color.red())
        else:
            conn.commit()
            await self.send_embed(ctx, "**__```𝐓𝐄́𝐂𝐍𝐈𝐂𝐀 𝐑𝐄𝐌𝐎𝐕𝐈𝐃𝐀```__**", f"- > **Técnica __`{technique_name}`__ removida do personagem __`{character_name}`__.**", discord.Color.green(), next_step="use `kill!showtechnique` para conferir outras técnicas")

    @commands.command(name='showtechnique', aliases=['tech'])
    async def show_technique(self, ctx, *, args: str):
        """Comando para exibir informações de uma técnica"""
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!showtechnique 'Nome do Personagem' 'Nome da Técnica'**", discord.Color.red())
            return

        character_name, technique_name = parsed_args[0], ' '.join(parsed_args[1:])
        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para visualizar técnicas dele.**", discord.Color.red())
            return

        character_id = character[0]
        c.execute("SELECT technique_name, description, image_url, xp, mastery, passive, COALESCE(power_system, 'reiatsu'), reiatsu_category, COALESCE(technique_role, 'offense'), COALESCE(progression_weight, 1.0), COALESCE(energy_cost, 10.0) FROM techniques WHERE character_id=? AND technique_name COLLATE NOCASE=?", 
                  (character_id, technique_name))
        technique = c.fetchone()
        if not technique:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada ou você não tem permissão para visualizá-la.**", discord.Color.red())
            return

        technique_name, description, image_url, xp, mastery, passive, power_system, reiatsu_category, technique_role, progression_weight, energy_cost = technique
        xp_needed = 100 + (mastery * 20)
        xp_percentage = (xp / xp_needed) * 100
        current_rank = self.update_rank(mastery)

        formatted_title, formatted_description = apply_layout(ctx.author.id, technique_name, description)

        formatted_description += (
            f"\n\n**𝐌𝐀𝐒𝐓𝐄𝐑𝐘:** {mastery}/600"
            f"\n**𝐄𝐗𝐏:** {xp}/{xp_needed} ({xp_percentage:.2f}%)"
            f"\n**𝐑𝐀𝐍𝐊 𝐀𝐓𝐔𝐀𝐋:** {current_rank}"
            f"\n**𝐏𝐀𝐒𝐒𝐈𝐕𝐀:** {passive or 'Nenhuma'}"
            f"\n**𝐏𝐎𝐖𝐄𝐑 𝐒𝐘𝐒𝐓𝐄𝐌:** {power_system}"
            f"\n**𝐑𝐄𝐈𝐀𝐓𝐒𝐔 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐘:** {reiatsu_category or 'N/A'}"
            f"\n**𝐑𝐎𝐋𝐄:** {technique_role}"
            f"\n**𝐖𝐄𝐈𝐆𝐇𝐓:** {float(progression_weight):.2f}"
            f"\n**𝐄𝐍𝐄𝐑𝐆𝐘 𝐂𝐎𝐒𝐓:** {float(energy_cost):.1f}"
        )

        await self.send_embed(ctx, formatted_title, formatted_description, discord.Color.blue(), image_url)

    
    @commands.command(name='settechniquelevel', aliases=['settechlvl'])
    async def set_technique_level(self, ctx, *, args: str):
        """Define o nível de mastery de uma técnica"""
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 3:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!settechniquelevel 'Nome do Personagem' 'Nome da Técnica' <Novo Nível>**", discord.Color.red())
            return

        character_name, technique_name, new_level_str = parsed_args[0], ' '.join(parsed_args[1:-1]), parsed_args[-1]

        try:
            new_mastery_level = int(new_level_str)
            if new_mastery_level <= 0: 
                await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **O nível de mastery deve ser um número inteiro positivo.**", discord.Color.red())
                return
        except ValueError:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **O nível deve ser um número inteiro válido.**", discord.Color.red())
            return

        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para alterar técnicas dele.**", discord.Color.red())
            return

        character_id = character[0]

        c.execute("SELECT technique_name, xp, mastery FROM techniques WHERE character_id=? AND technique_name COLLATE NOCASE=?", (character_id, technique_name))
        technique = c.fetchone()
        if not technique:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada ou você não tem permissão para alterar essa técnica.**", discord.Color.red())
            return

        new_mastery = new_mastery_level
        new_xp = 0

        c.execute("UPDATE techniques SET mastery=?, xp=? WHERE character_id=? AND technique_name COLLATE NOCASE=?", 
                  (new_mastery, new_xp, character_id, technique_name))
        conn.commit()

        await self.send_embed(ctx, "**__```𝐍𝐈́𝐕𝐄𝐋 𝐀𝐉𝐔𝐒𝐓𝐀𝐃𝐎```__**", f"- > **Técnica __`{technique_name}`__ agora está no nível de mastery __`{new_mastery}`__.**", discord.Color.green())

    @commands.has_permissions(administrator=True)
    @commands.command(name='setpassive')
    async def set_passive(self, ctx, *, args: str):
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 3:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso: kill!setpassive 'Nome do Personagem' 'Nome da Técnica' 'Passiva'**", discord.Color.red())
            return

        character_name, technique_name, passive_name = parsed_args[0], parsed_args[1], ' '.join(parsed_args[2:])

        c.execute("SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?", (character_name, ctx.author.id))
        character = c.fetchone()
        if not character:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Personagem não encontrado ou você não tem permissão para alterar passivas dele.**", discord.Color.red())
            return

        character_id = character[0]

        c.execute("SELECT technique_name FROM techniques WHERE character_id=? AND technique_name COLLATE NOCASE=?", (character_id, technique_name))
        technique = c.fetchone()
        if not technique:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Técnica não encontrada para o personagem.**", discord.Color.red())
            return

        c.execute("UPDATE techniques SET passive=? WHERE character_id=? AND technique_name COLLATE NOCASE=?", (passive_name, character_id, technique_name))
        conn.commit()

        await self.send_embed(ctx, "**__```𝐏𝐀𝐒𝐒𝐈𝐕𝐀 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐀```__**", f"- > **A passiva da técnica __`{technique_name}`__ foi atualizada para __`{passive_name}`__**", discord.Color.green())

    @commands.command(name='pfptechnique', aliases=['techimg'])
    async def pfptechnique(self, ctx, *, args: str):
        parsed_args = self.parse_args(args)
        if len(parsed_args) < 2:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Uso correto: `kill!pfptechnique [nome personagem] [nome técnica]`**", discord.Color.red())
            return

        character_name, technique_name = parsed_args[0], ' '.join(parsed_args[1:])

        c.execute("SELECT technique_name FROM techniques WHERE character_id=(SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?) AND technique_name COLLATE NOCASE=?",
                  (character_name, ctx.author.id, technique_name))
        technique = c.fetchone()

        if not technique:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", f"- > **Técnica** **__`{technique_name}`__** **não encontrada para o personagem** **__`{character_name}`__**.", discord.Color.red())
            return

        if ctx.message.attachments:
            image_url = ctx.message.attachments[0].url
            message_id = ctx.message.id

            c.execute("UPDATE techniques SET image_url=?, message_id=? WHERE character_id=(SELECT character_id FROM characters WHERE name COLLATE NOCASE=? AND user_id=?) AND technique_name COLLATE NOCASE=?",
                      (image_url, message_id, character_name, ctx.author.id, technique_name))
            conn.commit()

            await self.send_embed(ctx, "**__```𝐈𝐌𝐀𝐆𝐄𝐌 𝐀𝐓𝐔𝐀𝐋𝐈𝐙𝐀𝐃𝐀```__**", f"- > **Imagem da técnica** **__`{technique_name}`__** **atualizada com sucesso para o personagem** **__`{character_name}`__**.", discord.Color.green(), image_url)
        else:
            await self.send_embed(ctx, "**__```𝐄𝐑𝐑𝐎```__**", "- > **Por favor, anexe uma imagem ao usar este comando para definir o avatar da técnica.**", discord.Color.red())

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listener para processar mensagens recebidas de webhooks"""
        if self.active and message.webhook_id:
            await self.process_webhook(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Listener para processar mensagens editadas"""
        if self.active and after.webhook_id:
            await self.process_webhook(after)

async def setup(bot):
    await bot.add_cog(Techniques(bot))
