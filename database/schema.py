import sqlite3
from database.migrations import ensure_soul_runtime_schema


def migrate_abilities_schema(cursor: sqlite3.Cursor) -> None:
    # Migra a tabela antiga categories para abilities sem perder dados.
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
    has_categories = cursor.fetchone() is not None
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='abilities'")
    has_abilities = cursor.fetchone() is not None

    if has_categories and not has_abilities:
        cursor.execute("ALTER TABLE categories RENAME TO abilities")
        return

    if has_categories and has_abilities:
        cursor.execute(
            '''
            INSERT INTO abilities (category_id, character_id, category_name, description)
            SELECT c.category_id, c.character_id, c.category_name, c.description
            FROM categories c
            WHERE NOT EXISTS (
                SELECT 1 FROM abilities a WHERE a.category_id = c.category_id
            )
            '''
        )
        cursor.execute("DROP TABLE categories")


def create_tables(conn: sqlite3.Connection, cursor: sqlite3.Cursor, *, schema_version: int = 2) -> None:
    """Criar tabelas do banco de dados (Schema Soul Wandering v1.0)."""

    existing_tables = [
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
            passive TEXT DEFAULT 'Nenhuma',
            rank TEXT DEFAULT 'F-',
            message_id INTEGER DEFAULT NULL,
            category_id INTEGER,
            power_system TEXT DEFAULT 'reiatsu',
            reiatsu_category TEXT,
            technique_role TEXT DEFAULT 'offense',
            progression_weight REAL DEFAULT 1.0,
            energy_cost REAL DEFAULT 10.0,
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
        )''',
        '''CREATE TABLE IF NOT EXISTS characteristic_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            rarity TEXT NOT NULL,
            description TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS character_characteristics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            characteristic_id INTEGER NOT NULL,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE,
            FOREIGN KEY(characteristic_id) REFERENCES characteristic_definitions(id) ON DELETE CASCADE,
            UNIQUE(character_id, characteristic_id)
        )''',
        '''CREATE TABLE IF NOT EXISTS log_channel_settings (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            updated_by INTEGER,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''',
    ]

    characters_table = '''CREATE TABLE IF NOT EXISTS characters (
        character_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT COLLATE NOCASE NOT NULL UNIQUE,
        image_url TEXT,
        user_id INTEGER NOT NULL,
        registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
        private INTEGER DEFAULT 0,
        soul_tier TEXT DEFAULT 'Unknown'
    )'''

    soul_tables = [
        '''CREATE TABLE IF NOT EXISTS character_progression (
            progression_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL UNIQUE,
            experience INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            rank TEXT DEFAULT 'F-',
            points_available INTEGER DEFAULT 0,
            limit_break INTEGER DEFAULT 0,
            xp_multiplier REAL DEFAULT 1.0,
            forca INTEGER DEFAULT 1,
            resistencia INTEGER DEFAULT 1,
            agilidade INTEGER DEFAULT 1,
            sentidos INTEGER DEFAULT 1,
            vitalidade INTEGER DEFAULT 1,
            inteligencia INTEGER DEFAULT 1,
            message_count INTEGER DEFAULT 0,
            message_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE,
            CHECK (level >= 1 AND level <= 1000),
            CHECK (xp_multiplier > 0)
        )''',
        '''CREATE TABLE IF NOT EXISTS character_race_progression (
            race_progression_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL UNIQUE,
            race_name TEXT NOT NULL,
            race_path TEXT,
            race_stage INTEGER DEFAULT 0,
            race_stage_level INTEGER DEFAULT 0,
            evolution_count INTEGER DEFAULT 0,
            awakening_unlocked INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE,
            CHECK (race_stage_level >= 0 AND race_stage_level <= 100)
        )''',
        '''CREATE TABLE IF NOT EXISTS character_reiryoku (
            reiryoku_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL UNIQUE,
            core_color TEXT DEFAULT 'Black',
            core_stage TEXT DEFAULT 'Dark Stage',
            reiryoku_base_pool REAL DEFAULT 100.0,
            reiryoku_current REAL DEFAULT 100.0,
            core_stability REAL DEFAULT 50.0,
            core_purity REAL DEFAULT 50.0,
            load_ratio REAL DEFAULT 0.0,
            control_score REAL DEFAULT 50.0,
            control_rating TEXT DEFAULT 'Beginner',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            discovered_at TEXT,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE,
            CHECK (core_stability >= 0 AND core_stability <= 100),
            CHECK (core_purity >= 0 AND core_purity <= 100),
            CHECK (reiryoku_current >= 0 AND reiryoku_current <= reiryoku_base_pool)
        )''',
        '''CREATE TABLE IF NOT EXISTS character_reiryoku_skills (
            reiryoku_skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            mastery_level INTEGER DEFAULT 0,
            control_level INTEGER DEFAULT 0,
            is_awakened INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            discovered_at TEXT,
            awakened_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE,
            UNIQUE(character_id, skill_name),
            CHECK (mastery_level >= 0 AND mastery_level <= 100),
            CHECK (control_level >= 0 AND control_level <= 100),
            CHECK (is_awakened IN (0, 1)),
            CHECK (skill_name IN ('Ten', 'Zetsu', 'Ren', 'Hatsu', 'Gyo', 'Shu', 'Ko', 'Ken', 'En', 'Ryu'))
        )''',
        '''CREATE TABLE IF NOT EXISTS character_reiatsu_affinities (
            reiatsu_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL UNIQUE,
            primary_category TEXT NOT NULL,
            primary_category_level INTEGER DEFAULT 0,
            fortification_affinity INTEGER DEFAULT 0,
            transmutation_affinity INTEGER DEFAULT 0,
            conjuration_affinity INTEGER DEFAULT 0,
            emission_affinity INTEGER DEFAULT 0,
            manipulation_affinity INTEGER DEFAULT 0,
            specialization_affinity INTEGER DEFAULT 0,
            specialization_unlocked INTEGER DEFAULT 0,
            specialization_name TEXT,
            category_xp INTEGER DEFAULT 0,
            affinities_points INTEGER DEFAULT 0,
            primary_type TEXT,
            fortification_xp REAL DEFAULT 0.0,
            transmutation_xp REAL DEFAULT 0.0,
            conjuration_xp REAL DEFAULT 0.0,
            emission_xp REAL DEFAULT 0.0,
            manipulation_xp REAL DEFAULT 0.0,
            specialization_xp REAL DEFAULT 0.0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE,
            CHECK (primary_category IN ('Fortification', 'Transmutation', 'Conjuration', 'Emission', 'Manipulation', 'Specialization')),
            CHECK (primary_category_level >= 0 AND primary_category_level <= 100),
            CHECK (fortification_affinity >= 0 AND fortification_affinity <= 100),
            CHECK (transmutation_affinity >= 0 AND transmutation_affinity <= 100),
            CHECK (conjuration_affinity >= 0 AND conjuration_affinity <= 100),
            CHECK (emission_affinity >= 0 AND emission_affinity <= 100),
            CHECK (manipulation_affinity >= 0 AND manipulation_affinity <= 100),
            CHECK (specialization_affinity >= 0 AND specialization_affinity <= 100)
        )''',
        '''CREATE TABLE IF NOT EXISTS character_zanpakuto (
            zanpakuto_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            zanpakuto_name TEXT NOT NULL,
            spirit_name TEXT,
            release_command TEXT,
            form TEXT,
            awakening_stage TEXT,
            power_level INTEGER DEFAULT 0,
            is_awakened INTEGER DEFAULT 0,
            awakened_at TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        )''',
        '''CREATE TABLE IF NOT EXISTS character_grimoire (
            grimoire_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            grimoire_name TEXT NOT NULL,
            grimoire_type TEXT,
            pages_unlocked INTEGER DEFAULT 1,
            power_level INTEGER DEFAULT 0,
            is_awakened INTEGER DEFAULT 0,
            awakened_at TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        )''',
        '''CREATE TABLE IF NOT EXISTS character_runes (
            rune_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            rune_name TEXT NOT NULL,
            rune_symbol TEXT,
            rune_power TEXT,
            power_level INTEGER DEFAULT 0,
            is_inscribed INTEGER DEFAULT 0,
            inscribed_at TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        )''',
        '''CREATE TABLE IF NOT EXISTS character_noble_phantasm (
            phantasm_id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            phantasm_name TEXT NOT NULL,
            phantasm_class TEXT,
            rank TEXT,
            power_level INTEGER DEFAULT 0,
            is_manifested INTEGER DEFAULT 0,
            manifested_at TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE
        )''',
    ]

    for query in existing_tables:
        try:
            cursor.execute(query)
        except sqlite3.Error as e:
            print(f"Erro ao criar tabela generica: {e}")

    try:
        cursor.execute(characters_table)
    except sqlite3.Error:
        try:
            cursor.execute("ALTER TABLE characters ADD COLUMN soul_tier TEXT DEFAULT 'Unknown'")
        except sqlite3.Error:
            pass

    for query in soul_tables:
        try:
            cursor.execute(query)
        except sqlite3.Error as e:
            print(f"Erro ao criar tabela Soul: {e}")

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_char_race ON character_race_progression(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_race_name ON character_race_progression(race_name)",
        "CREATE INDEX IF NOT EXISTS idx_char_progression ON character_progression(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_level ON character_progression(level)",
        "CREATE INDEX IF NOT EXISTS idx_rank ON character_progression(rank)",
        "CREATE INDEX IF NOT EXISTS idx_char_reiryoku ON character_reiryoku(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_core_color ON character_reiryoku(core_color)",
        "CREATE INDEX IF NOT EXISTS idx_char_skill ON character_reiryoku_skills(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_skill_name ON character_reiryoku_skills(skill_name)",
        "CREATE INDEX IF NOT EXISTS idx_awakened ON character_reiryoku_skills(is_awakened)",
        "CREATE INDEX IF NOT EXISTS idx_char_reiatsu ON character_reiatsu_affinities(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_primary_cat ON character_reiatsu_affinities(primary_category)",
        "CREATE INDEX IF NOT EXISTS idx_char_zanpakuto ON character_zanpakuto(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_char_grimoire ON character_grimoire(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_char_runes ON character_runes(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_char_phantasm ON character_noble_phantasm(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_char_characteristics_char ON character_characteristics(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_char_characteristics_def ON character_characteristics(characteristic_id)",
    ]

    for index_query in indexes:
        try:
            cursor.execute(index_query)
        except sqlite3.Error as e:
            print(f"Erro ao criar indice: {e}")

    migrate_abilities_schema(cursor)
    ensure_soul_runtime_schema(conn, cursor, schema_version=schema_version)
    conn.commit()
