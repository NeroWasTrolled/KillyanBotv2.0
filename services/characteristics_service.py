import sqlite3
from typing import Dict, List, Tuple
from database.connection import create_connection

DB_PATH = "characters.db"

CHARACTERISTIC_EFFECTS = {
    "2x mastery": {"mastery_multiplier": 2.0},
    "reiryoku aumentado": {"reiryoku_multiplier": 1.25},
    "especialista": {"allows_specialization": True},
    "master class": {"class_slots": {"main": 2, "sub": 1}},
    "forca aumentada": {"attribute": "forca", "bonus": 15},
    "velocidade aumentada": {"attribute": "agilidade", "bonus": 15},
    "resistencia aumentada": {"attribute": "resistencia", "bonus": 15},
}

ATTRIBUTE_KEYS = {
    "forca": "forca",
    "forca aumentada": "forca",
    "strength": "forca",
    "resistencia": "resistencia",
    "resistance": "resistencia",
    "agilidade": "agilidade",
    "velocidade": "agilidade",
    "speed": "agilidade",
    "sentidos": "sentidos",
    "vitalidade": "vitalidade",
    "inteligencia": "inteligencia",
}


def _normalize_name(name: str) -> str:
    return (name or "").strip().lower()


def _create_db_connection() -> sqlite3.Connection:
    return create_connection(DB_PATH)


def get_characteristics(character_id: int) -> List[Dict[str, str]]:
    if not character_id:
        return []

    with _create_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT d.name, d.type, d.rarity, d.description
            FROM character_characteristics cc
            JOIN characteristic_definitions d ON d.id = cc.characteristic_id
            WHERE cc.character_id = ?
            """,
            (character_id,),
        )
        rows = cursor.fetchall()

    return [
        {
            "name": row[0],
            "type": row[1],
            "rarity": row[2],
            "description": row[3],
        }
        for row in rows
    ]


def _get_characteristic_name_set(character_id: int) -> set[str]:
    return {_normalize_name(item["name"]) for item in get_characteristics(character_id)}


def get_mastery_multiplier(character_id: int) -> float:
    names = _get_characteristic_name_set(character_id)
    effect = CHARACTERISTIC_EFFECTS.get("2x mastery", {})
    return float(effect.get("mastery_multiplier", 1.0)) if "2x mastery" in names else 1.0


def get_reiryoku_multiplier(character_id: int) -> float:
    names = _get_characteristic_name_set(character_id)
    effect = CHARACTERISTIC_EFFECTS.get("reiryoku aumentado", {})
    return float(effect.get("reiryoku_multiplier", 1.0)) if "reiryoku aumentado" in names else 1.0


def allows_specialization(character_id: int) -> bool:
    names = _get_characteristic_name_set(character_id)
    return "especialista" in names


def get_class_slots(character_id: int) -> Dict[str, int]:
    names = _get_characteristic_name_set(character_id)
    if "master class" in names:
        return {"main": 2, "sub": 1}
    return {"main": 1, "sub": 2}


def get_class_assignment_schema(character_id: int) -> Dict[str, List[str]]:
    slots = get_class_slots(character_id)
    if slots["main"] == 2:
        return {
            "input_roles": ["main", "main", "sub_primary"],
            "stored_columns": ["main_class", "sub_class1", "sub_class2"],
        }
    return {
        "input_roles": ["main", "sub_primary", "sub_secondary"],
        "stored_columns": ["main_class", "sub_class1", "sub_class2"],
    }


def get_class_role_multiplier(role: str) -> float:
    if role == "main":
        return 1.0
    if role == "sub_primary":
        return 0.5
    if role == "sub_secondary":
        return 0.25
    return 0.0


def get_attribute_bonus(character_id: int, attribute_name: str) -> int:
    normalized_attr = ATTRIBUTE_KEYS.get(_normalize_name(attribute_name))
    if not normalized_attr:
        return 0

    names = _get_characteristic_name_set(character_id)
    total_bonus = 0

    for characteristic_name in names:
        effect = CHARACTERISTIC_EFFECTS.get(characteristic_name, {})
        if effect.get("attribute") == normalized_attr:
            total_bonus += int(effect.get("bonus", 0))

    return total_bonus


def get_effective_attribute(character_id: int, attribute_name: str, base_value: int) -> int:
    return int(base_value or 0) + get_attribute_bonus(character_id, attribute_name)


def get_effective_reiryoku_values(
    character_id: int,
    base_pool: float,
    current_pool: float,
) -> Tuple[float, float, float]:
    multiplier = max(1.0, float(get_reiryoku_multiplier(character_id) or 1.0))
    base_pool = float(base_pool or 0.0)
    current_pool = float(current_pool or 0.0)

    if base_pool <= 0:
        return 0.0, 0.0, multiplier

    effective_max = base_pool * multiplier
    effective_current = max(0.0, min(effective_max, current_pool * multiplier))
    return effective_max, effective_current, multiplier
