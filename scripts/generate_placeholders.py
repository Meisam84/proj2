from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'runbook', 'assets')
os.makedirs(OUT_DIR, exist_ok=True)

images = [
    ('schedule_list_filters.png', 'Schedule list filters placeholder'),
    ('schedule_bulk_action_menu.png', 'Bulk actions placeholder'),
    ('schedule_change_form.png', 'Schedule change form placeholder'),
]

W, H = 1200, 600
bg_color = (240, 248, 255)
text_color = (30, 30, 30)

try:
    font = ImageFont.truetype('arial.ttf', 36)
except Exception:
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 36)
    except Exception:
        from PIL import ImageFont
        font = ImageFont.load_default()

for name, label in images:
    path = os.path.join(OUT_DIR, name)
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    try:
        bbox = draw.textbbox((0, 0), label, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except Exception:
        try:
            w, h = font.getsize(label)
        except Exception:
            w, h = (len(label) * 10, 20)
    draw.text(((W-w)/2, (H-h)/2), label, fill=text_color, font=font)
    img.save(path)
    print('Wrote', path)
