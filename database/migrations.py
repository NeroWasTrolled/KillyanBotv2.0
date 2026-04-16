import sqlite3


def ensure_column(cursor: sqlite3.Cursor, table_name: str, column_name: str, ddl: str) -> None:
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}")


def ensure_soul_runtime_schema(
    conn: sqlite3.Connection,
    cursor: sqlite3.Cursor,
    *,
    schema_version: int = 2,
) -> None:
    cursor.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    cursor.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version")
    current_version = int(cursor.fetchone()[0] or 0)

    def migration_v1() -> None:
        # techniques
        ensure_column(cursor, "techniques", "power_system", "TEXT DEFAULT 'reiatsu'")
        ensure_column(cursor, "techniques", "reiatsu_category", "TEXT")
        ensure_column(cursor, "techniques", "technique_role", "TEXT DEFAULT 'offense'")
        ensure_column(cursor, "techniques", "progression_weight", "REAL DEFAULT 1.0")
        ensure_column(cursor, "techniques", "energy_cost", "REAL DEFAULT 10.0")

        # character_reiryoku
        ensure_column(cursor, "character_reiryoku", "load_ratio", "REAL DEFAULT 0.0")
        ensure_column(cursor, "character_reiryoku", "control_score", "REAL DEFAULT 50.0")

        # character_reiatsu_affinities
        ensure_column(cursor, "character_reiatsu_affinities", "primary_type", "TEXT")
        ensure_column(cursor, "character_reiatsu_affinities", "fortification_xp", "REAL DEFAULT 0.0")
        ensure_column(cursor, "character_reiatsu_affinities", "transmutation_xp", "REAL DEFAULT 0.0")
        ensure_column(cursor, "character_reiatsu_affinities", "conjuration_xp", "REAL DEFAULT 0.0")
        ensure_column(cursor, "character_reiatsu_affinities", "emission_xp", "REAL DEFAULT 0.0")
        ensure_column(cursor, "character_reiatsu_affinities", "manipulation_xp", "REAL DEFAULT 0.0")
        ensure_column(cursor, "character_reiatsu_affinities", "specialization_xp", "REAL DEFAULT 0.0")

    def migration_v2() -> None:
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS characteristic_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                rarity TEXT NOT NULL,
                description TEXT
            )
            '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS character_characteristics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                characteristic_id INTEGER NOT NULL,
                FOREIGN KEY(character_id) REFERENCES characters(character_id) ON DELETE CASCADE,
                FOREIGN KEY(characteristic_id) REFERENCES characteristic_definitions(id) ON DELETE CASCADE,
                UNIQUE(character_id, characteristic_id)
            )
            '''
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_char_characteristics_char ON character_characteristics(character_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_char_characteristics_def ON character_characteristics(characteristic_id)")

        seed_definitions = [
            ("2x Mastery", "progression", "epic", "Multiplica o ganho de mastery de tecnicas."),
            ("Reiryoku Aumentado", "reiatsu", "rare", "Aumenta o limite efetivo de reiryoku sem alterar base salva."),
            ("Especialista", "reiatsu", "legendary", "Permite uso e progressao da categoria Specialization."),
            ("Master Class", "class", "legendary", "Altera slots para 2 classes principais e 1 subclasse."),
            ("Forca Aumentada", "combat", "rare", "Concede bonus passivo de forca."),
            ("Velocidade Aumentada", "combat", "rare", "Concede bonus passivo de agilidade."),
            ("Resistencia Aumentada", "combat", "rare", "Concede bonus passivo de resistencia."),
        ]

        cursor.executemany(
            "INSERT OR IGNORE INTO characteristic_definitions (name, type, rarity, description) VALUES (?, ?, ?, ?)",
            seed_definitions,
        )

    migrations = {
        1: migration_v1,
        2: migration_v2,
    }

    for version in range(current_version + 1, schema_version + 1):
        migration = migrations.get(version)
        if migration:
            migration()
        cursor.execute("DELETE FROM schema_version")
        cursor.execute("INSERT INTO schema_version(version) VALUES (?)", (version,))

    conn.commit()
