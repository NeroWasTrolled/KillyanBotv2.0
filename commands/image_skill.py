import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import re
import os
import aiohttp  
from database.connection import create_connection
from utils.common import send_embed, to_bold_sans_serif

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATE_IMAGE_PATH = os.path.join(BASE_DIR, "assets", "images", "image.png")
FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "DejaVuSans-Bold.ttf")
IMAGE_TEMPLATE_DIR = os.path.join(BASE_DIR, "assets", "images")

RACE_TEMPLATE_MAP = {
    "bount": "bount.png",
    "elf": "elf.png",
    "fullbringer": "fullbringer.png",
    "ghoul": "ghoul.png",
    "hollow": "hollow.png",
    "human": "human.png",
    "monster": "monster.png",
    "quincy": "quincy.png",
    "shinigami": "shinigami.png",
    "unknown": "unknown.png",
    "vaizard": "vaizard.png",
    "youkai": "youkai.png",
}

RACE_COLORS = {
    "bount": "#F0E4B6",
    "elf": "#94F7D8",
    "fullbringer": "#9AC7FF",
    "ghoul": "#FF7373",
    "hollow": "#D7E1FF",
    "human": "#FFD36D",
    "monster": "#FF986B",
    "quincy": "#8ED1FF",
    "shinigami": "#FFE162",
    "unknown": "#E3E8F0",
    "vaizard": "#FFB86C",
    "youkai": "#C8A8FF",
}

LABEL_COLOR = "#E8EEF9"
DESCRIPTION_COLOR = "#D4DEEC"
REFERENCE_SIZE = (1670, 942)
PANEL_FILL = (4, 6, 10, 230)
PANEL_BORDER = (255, 190, 102, 210)

# Ajuste fino do layout.
# Se quiser mover algo, altere estes números primeiro.
# Valores maiores em X vão para a direita. Valores menores em X vão para a esquerda.
# Valores maiores em Y vão para baixo. Valores menores em Y vão para cima.
ABILITY_TEXT_X = 650
ABILITY_TEXT_Y = 80

RANK_TEXT_X = 650
RANK_TEXT_Y = 185

PASSIVE_TEXT_X = 650
PASSIVE_TEXT_Y = 290

# Coluna única para os valores de habilidade/rank/passiva.
# Isso evita desalinhamento visual entre linhas com rótulos de tamanhos diferentes.
INFO_VALUE_COLUMN_X = 840

TEXT_VALUE_GAP = 14

ABILITY_IMAGE_X = 22
ABILITY_IMAGE_Y = 28
ABILITY_IMAGE_W = 235
ABILITY_IMAGE_H = 235
ABILITY_IMAGE_RADIUS = 16

XP_TEXT_RIGHT_X = 1610
XP_TEXT_Y = 545

MASTERY_TEXT_RIGHT_X = 1610
MASTERY_TEXT_Y = 902

DESCRIPTION_X = 120
DESCRIPTION_Y = 650
DESCRIPTION_MAX_WIDTH = 1380

conn = create_connection()
c = conn.cursor()

def clean_discord_formatting(text):
    return re.sub(r'[*_>~-]', '', text)

def clean_quotes(text):
    return text.strip("'\"")

async def download_image(image_url):
    """Baixa a imagem a partir de um URL e retorna um objeto PIL Image."""
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status != 200:
                return None
            image_data = await response.read()
            image = Image.open(io.BytesIO(image_data))
            return image


def normalize_race_key(raw_race_name):
    if not raw_race_name:
        return "unknown"

    key = str(raw_race_name).strip().lower()
    key = key.replace(" ", "")
    key = key.replace("ã", "a").replace("á", "a").replace("à", "a")
    key = key.replace("é", "e").replace("ê", "e")
    key = key.replace("í", "i")
    key = key.replace("ó", "o").replace("ô", "o")
    key = key.replace("ú", "u")
    key = key.replace("ç", "c")

    if key in RACE_TEMPLATE_MAP:
        return key
    return "unknown"


def get_template_for_race(race_key):
    race_filename = RACE_TEMPLATE_MAP.get(race_key, RACE_TEMPLATE_MAP["unknown"])
    race_template_path = os.path.join(IMAGE_TEMPLATE_DIR, race_filename)

    if os.path.exists(race_template_path):
        return race_template_path

    unknown_path = os.path.join(IMAGE_TEMPLATE_DIR, RACE_TEMPLATE_MAP["unknown"])
    if os.path.exists(unknown_path):
        return unknown_path

    return TEMPLATE_IMAGE_PATH


def fit_cover(image, target_size):
    target_w, target_h = target_size
    src_w, src_h = image.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h

    if src_ratio > target_ratio:
        new_h = target_h
        new_w = int(new_h * src_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / src_ratio)

    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def draw_labeled_value(draw, label, value, xy, label_font, value_font, label_color, value_color):
    x, y = xy
    draw.text((x, y), label, font=label_font, fill=label_color)
    label_bbox = draw.textbbox((x, y), label, font=label_font)
    value_x = label_bbox[2] + TEXT_VALUE_GAP
    draw.text((value_x, y), value, font=value_font, fill=value_color)


def draw_right_aligned_text(draw, text, right_x, y, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text((right_x - text_width, y), text, font=font, fill=fill)


def paste_rounded_panel(base_image, image_to_paste, position, size, radius=20):
    content = fit_cover(image_to_paste.convert("RGBA"), size)
    mask = Image.new("L", size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    layer.paste(content, (0, 0))
    base_image.paste(layer, position, mask)

async def generate_ability_image(character_name, technique_name, passive, rank, mastery, xp, xp_needed, description, race_name, image_url=None):
    race_key = normalize_race_key(race_name)
    template_path = get_template_for_race(race_key)
    image = Image.open(template_path).convert("RGBA")

    draw = ImageDraw.Draw(image)

    ref_w, ref_h = REFERENCE_SIZE
    img_w, img_h = image.size
    scale_x = img_w / ref_w
    scale_y = img_h / ref_h
    scale = min(scale_x, scale_y)

    def sx(v):
        return int(v * scale_x)

    def sy(v):
        return int(v * scale_y)

    def sf(v):
        return max(12, int(v * scale))

    label_font = ImageFont.truetype(FONT_PATH, sf(38))
    value_font = ImageFont.truetype(FONT_PATH, sf(38))
    stat_font = ImageFont.truetype(FONT_PATH, sf(30))
    description_font = ImageFont.truetype(FONT_PATH, sf(28))

    accent_color = RACE_COLORS.get(race_key, RACE_COLORS["unknown"])

    technique_name = clean_discord_formatting(technique_name)
    description = clean_discord_formatting(description)

    passive = passive if passive and passive.strip() else "NENHUMA"
    rank = (rank or "F-").upper()

    draw.text((sx(ABILITY_TEXT_X), sy(ABILITY_TEXT_Y)), "HABILIDADE:", font=label_font, fill=LABEL_COLOR)
    draw.text((sx(INFO_VALUE_COLUMN_X), sy(ABILITY_TEXT_Y)), technique_name, font=value_font, fill=accent_color)

    draw.text((sx(RANK_TEXT_X), sy(RANK_TEXT_Y)), "RANK:", font=label_font, fill=LABEL_COLOR)
    draw.text((sx(INFO_VALUE_COLUMN_X), sy(RANK_TEXT_Y)), rank, font=value_font, fill=accent_color)

    draw.text((sx(PASSIVE_TEXT_X), sy(PASSIVE_TEXT_Y)), "PASSIVA:", font=label_font, fill=LABEL_COLOR)
    draw.text((sx(INFO_VALUE_COLUMN_X), sy(PASSIVE_TEXT_Y)), passive, font=value_font, fill=accent_color)

    max_description_width = sx(DESCRIPTION_MAX_WIDTH)
    wrapped_description = wrap_text(description, description_font, max_description_width, draw)
    draw.text((sx(DESCRIPTION_X), sy(DESCRIPTION_Y)), wrapped_description, font=description_font, fill=DESCRIPTION_COLOR)

    draw_right_aligned_text(draw, f"{xp}/{xp_needed} XP", sx(XP_TEXT_RIGHT_X), sy(XP_TEXT_Y), stat_font, accent_color)
    draw_right_aligned_text(draw, f"MASTERY: {mastery}/600", sx(MASTERY_TEXT_RIGHT_X), sy(MASTERY_TEXT_Y), stat_font, accent_color)

    if image_url:
        technique_image = await download_image(image_url)
        if technique_image:
            slot_size = (sx(ABILITY_IMAGE_W), sy(ABILITY_IMAGE_H))
            slot_position = (sx(ABILITY_IMAGE_X), sy(ABILITY_IMAGE_Y))
            paste_rounded_panel(image, technique_image, slot_position, slot_size, radius=sx(ABILITY_IMAGE_RADIUS))

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer

def wrap_text(text, font, max_width, draw):
    lines = []
    words = text.split(' ')
    current_line = ""

    for word in words:
        test_text = f"{current_line}{word}".strip()
        bbox = draw.textbbox((0, 0), test_text, font=font)
        text_width = bbox[2] - bbox[0] 
        if text_width <= max_width:
            current_line += f"{word} "
        else:
            lines.append(current_line.strip())
            current_line = f"{word} "

    lines.append(current_line.strip())
    return "\n".join(lines)

@commands.command(name='showability')
async def show_ability_image(ctx, character_name: commands.clean_content, *, technique_name: commands.clean_content):
    character_name = clean_quotes(character_name)
    technique_name = clean_quotes(technique_name)

    c.execute("""
    SELECT
        t.xp,
        t.mastery,
        t.passive,
        t.rank,
        t.description,
        t.image_url,
        COALESCE(r.race_name, 'Unknown')
    FROM techniques t
    JOIN characters ch ON ch.character_id = t.character_id
    LEFT JOIN character_race_progression r ON r.character_id = ch.character_id
    WHERE t.technique_name COLLATE NOCASE=?
      AND ch.name COLLATE NOCASE=?
    """, (technique_name, character_name))

    technique = c.fetchone()

    if not technique:
        formatted_character = to_bold_sans_serif(str(character_name))
        formatted_technique = to_bold_sans_serif(str(technique_name))
        await send_embed(
            ctx,
            "**__```𝐄𝐑𝐑𝐎```__**",
            f"- > **Personagem ou técnica não encontrados.**\n- > **Personagem:** {formatted_character}\n- > **Técnica:** {formatted_technique}",
            discord.Color.red(),
        )
        return

    xp, mastery, passive, rank, description, image_url, race_name = technique
    xp_needed = 100 + (mastery * 20)

    image_buffer = await generate_ability_image(
        character_name,
        technique_name,
        passive,
        rank,
        mastery,
        xp,
        xp_needed,
        description,
        race_name,
        image_url,
    )

    file = discord.File(fp=image_buffer, filename="ability_image.png")
    await ctx.send(file=file)

async def setup(bot):
    bot.add_command(show_ability_image)
