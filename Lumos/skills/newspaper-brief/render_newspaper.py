from PIL import Image, ImageDraw, ImageFont
import json

def create_newspaper(input_path, output_path, theme="classic"):
    """Create newspaper-style image with customizable themes."""
    with open(input_path, "r", encoding="utf-8") as f:
        news = json.load(f)

    image_width, image_height = 800, 2000
    themes = {
        "classic": {"bg_color": "white", "text_color": "black"},
        "dark": {"bg_color": "black", "text_color": "white"},
        "gray": {"bg_color": "#f0f0f0", "text_color": "#333"}
    }

    theme_config = themes.get(theme, themes["classic"])
    img = Image.new('RGB', (image_width, image_height), color=theme_config['bg_color'])
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 30)
        font_body = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        print("Fallback to default font loading...")
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    x, y = 50, 50
    spacing = 30
    for article in news:
        draw.text((x, y), f"Title: {article['title']}", fill=theme_config['text_color'], font=font_title)
        y += 2 * spacing
        draw.text((x, y), f"Summary: {article['summary']}", fill=theme_config['text_color'], font=font_body)
        y += 4 * spacing
        if y > image_height - 200:
            break

    img.save(output_path)
    print(f"Newspaper image saved to {output_path} with {theme} theme")

if __name__ == "__main__":
    input_path = "output/aggregated_news.json"
    output_path = "output/newspaper_theme_classic.png"
    create_newspaper(input_path, output_path, theme="classic")