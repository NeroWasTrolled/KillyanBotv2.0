import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import sqlite3
import re
import aiohttp  

conn = sqlite3.connect('characters.db')
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

async def generate_ability_image(character_name, technique_name, passive, rank, mastery, xp, xp_needed, description, image_url=None):
    image = Image.open("image.png")  

    draw = ImageDraw.Draw(image)

    font_path = "DejaVuSans-Bold.ttf" 
    title_font = ImageFont.truetype(font_path, 30)  
    main_font = ImageFont.truetype(font_path, 30)  
    mastery_xp_font = ImageFont.truetype(font_path, 16)  
    description_font = ImageFont.truetype(font_path, 18)  

    text_color = "#FFE162"

    technique_name = clean_discord_formatting(technique_name)
    description = clean_discord_formatting(description)

    passive = passive if passive and passive.strip() else "NENHUMA"

    draw.text((225, 70), f"HABILIDADE: {technique_name}", font=title_font, fill=text_color) 
    draw.text((225, 120), f"RANK: {rank}", font=main_font, fill=text_color)  
    draw.text((225, 170), f"PASSIVA: {passive}", font=description_font, fill=text_color)

    max_description_width = 550  
    wrapped_description = wrap_text(description, description_font, max_description_width, draw)
    draw.text((70, 260), wrapped_description, font=description_font, fill=text_color) 

    draw.text((660, 450), f"MASTERY: {mastery}/600", font=mastery_xp_font, fill=text_color) 
    draw.text((720, 250), f"{xp}/{xp_needed} XP", font=mastery_xp_font, fill=text_color)  

    if image_url:
        technique_image = await download_image(image_url)
        if technique_image:
            technique_image = technique_image.resize((124, 124))  
            image.paste(technique_image, (86, 76))  

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer

def wrap_text(text, font, max_width, draw):
    lines = []
    words = text.split(' ')
    current_line = ""

    for word in words:
        bbox = draw.textbbox((0, 0), current_line + word, font=font)
        text_width = bbox[2] - bbox[0] 
        if text_width <= max_width:
            current_line += f"{word} "
        else:
            lines.append(current_line)
            current_line = f"{word} "

    lines.append(current_line) 
    return "\n".join(lines)

@commands.command(name='showability')
async def show_ability_image(ctx, character_name: commands.clean_content, *, technique_name: commands.clean_content):
    character_name = clean_quotes(character_name)
    technique_name = clean_quotes(technique_name)

    c.execute("""
    SELECT xp, mastery, passive, rank, description, image_url FROM techniques 
    WHERE technique_name COLLATE NOCASE=? 
    AND character_id=(SELECT character_id FROM characters WHERE name COLLATE NOCASE=?)
    """, (technique_name, character_name))

    technique = c.fetchone()

    if not technique:
        await ctx.send(f"Personagem ou técnica não encontrados.\nPersonagem: {character_name}\nTécnica: {technique_name}")
        return

    xp, mastery, passive, rank, description, image_url = technique
    xp_needed = 100 + (mastery * 20)
    level = mastery 

    image_buffer = await generate_ability_image(character_name, technique_name, passive, rank, mastery, xp, xp_needed, description, image_url)

    file = discord.File(fp=image_buffer, filename="ability_image.png")
    await ctx.send(file=file)

async def setup(bot):
    bot.add_command(show_ability_image)
