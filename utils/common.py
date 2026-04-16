import re
import discord
from database.connection import create_connection


def sanitize_input(input_str: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9\s]*$", str(input_str or "")))


def parse_quoted_args(args: str) -> list[str]:
    pattern = r"'(.*?)'|(\S+)"
    matches = re.findall(pattern, args or "")
    return [match[0] if match[0] else match[1] for match in matches]


def to_bold_sans_serif(text: str) -> str:
    bold_sans_serif = {
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆',
        'H': '𝐇', 'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍',
        'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓', 'U': '𝐔',
        'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠',
        'h': '𝐡', 'i': '𝐢', 'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧',
        'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫', 's': '𝐬', 't': '𝐭', 'u': '𝐮',
        'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳',
    }
    return ''.join(bold_sans_serif.get(ch, ch) for ch in str(text or "").upper())


def apply_layout(user_id: int, title: str, description: str, *, default_title: str, default_description: str) -> tuple[str, str]:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title_layout, description_layout FROM layout_settings WHERE user_id=?", (user_id,))
    layout = cursor.fetchone()

    if layout:
        title_layout, description_layout = layout
    else:
        title_layout = default_title
        description_layout = default_description

    formatted_title = title_layout.replace("{title}", title)
    formatted_description = description_layout.replace("{description}", description)
    return formatted_title, formatted_description


async def send_embed(ctx, title, description, color=discord.Color.blue(), image_url=None, next_step=None):
    if next_step:
        description = f"{description}\n\n- > **Próximo passo:** {next_step}"
    embed = discord.Embed(title=title, description=description, color=color)
    if image_url:
        embed.set_image(url=image_url)
    await ctx.send(embed=embed)
