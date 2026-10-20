"""
CineBook - Indian Cinema Poster & Promotional Banner Generator Script
Generates beautiful 2:3 aspect-ratio cinema posters and wide promotional banner
for the Indian Movie catalogue (Telugu, Tamil, Hindi, Malayalam, Kannada).
"""

from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont


def create_gradient_canvas(width: int, height: int, top_color: tuple, bottom_color: tuple) -> Image.Image:
    base = Image.new("RGBA", (width, height), top_color)
    top_r, top_g, top_b = top_color[:3]
    bot_r, bot_g, bot_b = bottom_color[:3]

    draw = ImageDraw.Draw(base)
    for y in range(height):
        factor = y / float(height)
        r = int(top_r + (bot_r - top_r) * factor)
        g = int(top_g + (bot_g - top_g) * factor)
        b = int(top_b + (bot_b - top_b) * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    return base


def generate_indian_movie_posters():
    output_dir = Path(__file__).resolve().parent / "assets" / "posters"
    output_dir.mkdir(parents=True, exist_ok=True)

    w, h = 400, 600  # Exactly 2:3 aspect ratio

    movies_art = [
        # 1. RRR (Telugu)
        {
            "filename": "rrr.png",
            "title": "RRR",
            "subtitle": "RISE  •  ROAR  •  REVOLT",
            "industry": "TELUGU CINEMA",
            "genre": "ACTION / EPIC",
            "director": "S.S. RAJAMOULI",
            "cast": "NTR JR  •  RAM CHARAN  •  ALIA BHATT",
            "tagline": "Two legendary revolutionaries. One glorious war.",
            "top_color": (90, 15, 20),
            "bottom_color": (15, 5, 8),
            "accent": (245, 158, 11),       # Fire Gold
            "badge_color": (220, 38, 38),   # Flame Red
            "theme": "fire_water"
        },
        # 2. Baahubali 2 (Telugu)
        {
            "filename": "baahubali_2.png",
            "title": "BAAHUBALI 2",
            "subtitle": "THE CONCLUSION",
            "industry": "TELUGU CINEMA",
            "genre": "ACTION / FANTASY",
            "director": "S.S. RAJAMOULI",
            "cast": "PRABHAS  •  RANA  •  ANUSHKA SHETTY",
            "tagline": "Why Kattappa killed Baahubali.",
            "top_color": (120, 53, 15),
            "bottom_color": (24, 15, 10),
            "accent": (251, 191, 36),
            "badge_color": (180, 83, 9),
            "theme": "throne"
        },
        # 3. Pushpa 2 (Telugu)
        {
            "filename": "pushpa_2.png",
            "title": "PUSHPA 2",
            "subtitle": "THE RULE",
            "industry": "TELUGU CINEMA",
            "genre": "ACTION / CRIME",
            "director": "SUKUMAR",
            "cast": "ALLU ARJUN  •  FAHADH FAASIL  •  RASHMIKA",
            "tagline": "Pushpa ante flower anukuntiva? Wildfire!",
            "top_color": (113, 63, 18),
            "bottom_color": (28, 15, 8),
            "accent": (239, 68, 68),
            "badge_color": (185, 28, 28),
            "theme": "sandalwood"
        },
        # 4. Kalki 2898 AD (Telugu)
        {
            "filename": "kalki_2898_ad.png",
            "title": "KALKI",
            "subtitle": "2898 AD",
            "industry": "TELUGU CINEMA",
            "genre": "SCI-FI / MYTHOLOGY",
            "director": "NAG ASHWIN",
            "cast": "PRABHAS  •  AMITABH  •  KAMAL HAASAN",
            "tagline": "The future of mankind awaits the tenth avatar.",
            "top_color": (20, 20, 50),
            "bottom_color": (8, 10, 25),
            "accent": (56, 189, 248),
            "badge_color": (99, 102, 241),
            "theme": "cyber_myth"
        },
        # 5. Leo (Tamil)
        {
            "filename": "leo.png",
            "title": "LEO",
            "subtitle": "BLOODY SWEET",
            "industry": "TAMIL CINEMA",
            "genre": "ACTION / THRILLER",
            "director": "LOKESH KANAGARAJ",
            "cast": "THALAPATHY VIJAY  •  TRISHA  •  SANJAY DUTT",
            "tagline": "Keep calm and prepare for the battle.",
            "top_color": (69, 10, 10),
            "bottom_color": (15, 3, 3),
            "accent": (248, 113, 113),
            "badge_color": (220, 38, 38),
            "theme": "hyena"
        },
        # 6. Vikram (Tamil)
        {
            "filename": "vikram.png",
            "title": "VIKRAM",
            "subtitle": "HITLIST",
            "industry": "TAMIL CINEMA",
            "genre": "ACTION / THRILLER",
            "director": "LOKESH KANAGARAJ",
            "cast": "KAMAL HAASAN  •  VIJAY SETHUPATHI  •  FAHADH",
            "tagline": "Once upon a time there lived a ghost...",
            "top_color": (15, 23, 42),
            "bottom_color": (2, 6, 23),
            "accent": (245, 158, 11),
            "badge_color": (217, 119, 6),
            "theme": "mask"
        },
        # 7. Jailer (Tamil)
        {
            "filename": "jailer.png",
            "title": "JAILER",
            "subtitle": "HUKUM — TIGER KA HUKUM",
            "industry": "TAMIL CINEMA",
            "genre": "ACTION / DRAMA",
            "director": "NELSON DILIPKUMAR",
            "cast": "SUPERSTAR RAJINIKANTH  •  MOHANLAL",
            "tagline": "A retired warden. An unstoppable storm.",
            "top_color": (46, 16, 70),
            "bottom_color": (15, 5, 25),
            "accent": (217, 70, 239),
            "badge_color": (168, 85, 247),
            "theme": "tiger"
        },
        # 8. Ponniyin Selvan 1 (Tamil)
        {
            "filename": "ponniyin_selvan_1.png",
            "title": "PONNIYIN SELVAN",
            "subtitle": "PART ONE — CHOLA PRIDE",
            "industry": "TAMIL CINEMA",
            "genre": "HISTORICAL / EPIC",
            "director": "MANI RATNAM",
            "cast": "VIKRAM  •  AISHWARYA RAI  •  KARTHI",
            "tagline": "The golden age of the mighty Chola dynasty.",
            "top_color": (113, 63, 18),
            "bottom_color": (25, 15, 8),
            "accent": (245, 158, 11),
            "badge_color": (202, 138, 4),
            "theme": "chola"
        },
        # 9. Jawan (Hindi)
        {
            "filename": "jawan.png",
            "title": "JAWAN",
            "subtitle": "READY?",
            "industry": "HINDI / BOLLYWOOD",
            "genre": "ACTION / THRILLER",
            "director": "ATLEE",
            "cast": "SHAH RUKH KHAN  •  NAYANTHARA  •  VIJAY SETHUPATHI",
            "tagline": "Good evening ladies and gentlemen!",
            "top_color": (69, 10, 10),
            "bottom_color": (15, 5, 8),
            "accent": (239, 68, 68),
            "badge_color": (220, 38, 38),
            "theme": "bandages"
        },
        # 10. 12th Fail (Hindi)
        {
            "filename": "12th_fail.png",
            "title": "12th FAIL",
            "subtitle": "#RESTART",
            "industry": "HINDI / BOLLYWOOD",
            "genre": "BIOGRAPHY / DRAMA",
            "director": "VIDHU VINOD CHOPRA",
            "cast": "VIKRANT MASSEY  •  MEDHA SHANKR",
            "tagline": "Haar nahi maanunga, restart karunga!",
            "top_color": (6, 78, 59),
            "bottom_color": (3, 20, 16),
            "accent": (52, 211, 153),
            "badge_color": (16, 185, 129),
            "theme": "lamp"
        },
        # 11. Dangal (Hindi)
        {
            "filename": "dangal.png",
            "title": "DANGAL",
            "subtitle": "GOLD IS GOLD",
            "industry": "HINDI / BOLLYWOOD",
            "genre": "BIOGRAPHY / SPORT",
            "director": "NITESH TIWARI",
            "cast": "AAMIR KHAN  •  FATIMA SANA SHAIKH  •  SANYA",
            "tagline": "Mhaari chhoriyan chhoron se kam hain ke?",
            "top_color": (120, 53, 15),
            "bottom_color": (28, 15, 10),
            "accent": (251, 191, 36),
            "badge_color": (217, 119, 6),
            "theme": "akhada"
        },
        # 12. Stree 2 (Hindi)
        {
            "filename": "stree_2.png",
            "title": "STREE 2",
            "subtitle": "SARKATE KA AATANK",
            "industry": "HINDI / BOLLYWOOD",
            "genre": "COMEDY / HORROR",
            "director": "AMAR KAUSHIK",
            "cast": "RAJKUMMAR RAO  •  SHRADDHA KAPOOR",
            "tagline": "O Stree kal aana... nahi, abhi aao!",
            "top_color": (49, 46, 129),
            "bottom_color": (10, 12, 35),
            "accent": (244, 63, 94),
            "badge_color": (225, 29, 72),
            "theme": "braid"
        },
        # 13. Manjummel Boys (Malayalam)
        {
            "filename": "manjummel_boys.png",
            "title": "MANJUMMEL BOYS",
            "subtitle": "THE DEVIL'S KITCHEN",
            "industry": "MALAYALAM CINEMA",
            "genre": "SURVIVAL / DRAMA",
            "director": "CHIDAMBARAM",
            "cast": "SOUBIN SHAHIR  •  SREENATH BHASI",
            "tagline": "No man left behind in the deep abyss.",
            "top_color": (15, 118, 110),
            "bottom_color": (4, 47, 46),
            "accent": (45, 212, 191),
            "badge_color": (13, 148, 136),
            "theme": "cave"
        },
        # 14. Aavesham (Malayalam)
        {
            "filename": "aavesham.png",
            "title": "AAVESHAM",
            "subtitle": "RANGA BHAI MASS",
            "industry": "MALAYALAM CINEMA",
            "genre": "ACTION / COMEDY",
            "director": "JITHU MADHAVAN",
            "cast": "FAHADH FAASIL  •  HIPZSTER  •  MITHUN",
            "tagline": "Eda mwone! Welcome to Bengaluru city!",
            "top_color": (133, 77, 14),
            "bottom_color": (28, 18, 5),
            "accent": (250, 204, 21),
            "badge_color": (202, 138, 4),
            "theme": "mustache"
        },
        # 15. Lucifer (Malayalam)
        {
            "filename": "lucifer.png",
            "title": "LUCIFER",
            "subtitle": "STEPHEN NEDUMPALLY",
            "industry": "MALAYALAM CINEMA",
            "genre": "ACTION / CRIME",
            "director": "PRITHVIRAJ SUKUMARAN",
            "cast": "LALETTAN MOHANLAL  •  VIVEK OBEROI",
            "tagline": "Blood runs thicker than politics.",
            "top_color": (15, 23, 42),
            "bottom_color": (2, 6, 23),
            "accent": (239, 68, 68),
            "badge_color": (185, 28, 28),
            "theme": "cross"
        },
        # 16. KGF: Chapter 2 (Kannada)
        {
            "filename": "kgf_chapter_2.png",
            "title": "K.G.F 2",
            "subtitle": "ROCKY BHAI'S EMPIRE",
            "industry": "KANNADA CINEMA",
            "genre": "ACTION / PERIOD",
            "director": "PRASHANTH NEEL",
            "cast": "ROCKING STAR YASH  •  SANJAY DUTT",
            "tagline": "Violence violence violence! I don't like it!",
            "top_color": (113, 63, 18),
            "bottom_color": (25, 15, 8),
            "accent": (251, 191, 36),
            "badge_color": (217, 119, 6),
            "theme": "gold_mine"
        },
        # 17. Kantara (Kannada)
        {
            "filename": "kantara.png",
            "title": "KANTARA",
            "subtitle": "A LEGEND",
            "industry": "KANNADA CINEMA",
            "genre": "ACTION / FOLKLORE",
            "director": "RISHAB SHETTY",
            "cast": "RISHAB SHETTY  •  SAPTHAMI GOWDA",
            "tagline": "The roar of the divine Daivaradhane spirit.",
            "top_color": (124, 45, 18),
            "bottom_color": (35, 12, 5),
            "accent": (249, 115, 22),
            "badge_color": (194, 65, 12),
            "theme": "kola"
        },
        # 18. 777 Charlie (Kannada)
        {
            "filename": "777_charlie.png",
            "title": "777 CHARLIE",
            "subtitle": "JOURNEY OF UNCONDITIONAL LOVE",
            "industry": "KANNADA CINEMA",
            "genre": "ADVENTURE / COMEDY",
            "director": "KIRANRAJ K",
            "cast": "RAKSHIT SHETTY  •  CHARLIE (LABRADOR)",
            "tagline": "A tail of hope across the snow-clad peaks.",
            "top_color": (6, 95, 70),
            "bottom_color": (3, 30, 25),
            "accent": (52, 211, 153),
            "badge_color": (16, 185, 129),
            "theme": "paw"
        },
        # 19. Kantara Chapter 1 Prequel (Upcoming)
        {
            "filename": "kantara_prequel.png",
            "title": "KANTARA",
            "subtitle": "CHAPTER 1 [PREQUEL]",
            "industry": "KANNADA CINEMA",
            "genre": "MYTHOLOGY / ACTION",
            "director": "RISHAB SHETTY",
            "cast": "RISHAB SHETTY  •  RUKMINI VASANTH",
            "tagline": "[Sample Upcoming] The mythological genesis.",
            "top_color": (131, 24, 67),
            "bottom_color": (28, 8, 15),
            "accent": (251, 146, 60),
            "badge_color": (225, 29, 72),
            "theme": "flame_trident"
        },
        # 20. SSMB29 Jungle Adventure (Upcoming)
        {
            "filename": "ssmb29.png",
            "title": "SSMB 29",
            "subtitle": "GLOBE-TROTTING JUNGLE ADVENTURE",
            "industry": "TELUGU CINEMA",
            "genre": "ACTION / ADVENTURE",
            "director": "S.S. RAJAMOULI",
            "cast": "SUPERSTAR MAHESH BABU",
            "tagline": "[Sample Upcoming] The wild expedition begins.",
            "top_color": (20, 83, 45),
            "bottom_color": (5, 35, 18),
            "accent": (74, 222, 128),
            "badge_color": (22, 163, 74),
            "theme": "jungle"
        },
    ]

    for item in movies_art:
        img = create_gradient_canvas(w, h, item["top_color"], item["bottom_color"])
        draw = ImageDraw.Draw(img)
        theme = item["theme"]
        accent = item["accent"]

        # Thematic Center Graphics
        cx, cy = w // 2, 220
        if theme == "fire_water":
            # RRR dual flame and splash
            draw.polygon([(cx - 70, cy + 50), (cx, cy - 80), (cx + 20, cy + 50)], fill=(239, 68, 68, 180))
            draw.polygon([(cx - 20, cy + 50), (cx + 70, cy - 60), (cx + 50, cy + 60)], fill=(56, 189, 248, 180))
            draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=accent + (220,))
        elif theme == "throne":
            # Baahubali shield and golden sun
            draw.ellipse([cx - 65, cy - 65, cx + 65, cy + 65], outline=accent, width=4)
            draw.polygon([(cx, cy - 80), (cx + 50, cy + 40), (cx - 50, cy + 40)], fill=accent + (160,))
            draw.ellipse([cx - 25, cy - 25, cx + 25, cy + 25], fill=(245, 158, 11))
        elif theme == "sandalwood":
            # Axe and wildfire trees
            draw.line([(cx - 60, cy + 60), (cx + 60, cy - 60)], fill=accent, width=5)
            draw.polygon([(cx + 30, cy - 80), (cx + 80, cy - 50), (cx + 40, cy - 30)], fill=(220, 38, 38, 220))
        elif theme == "cyber_myth":
            # Futuristic halo with celestial bow
            draw.ellipse([cx - 75, cy - 75, cx + 75, cy + 75], outline=accent, width=3)
            draw.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], outline=(255, 255, 255, 160), width=2)
            draw.line([(cx - 90, cy), (cx + 90, cy)], fill=accent, width=3)
        elif theme == "hyena":
            # Bloody claw slash & silhouette
            for off in [-40, -10, 20]:
                draw.line([(cx + off - 30, cy - 60), (cx + off + 30, cy + 60)], fill=(239, 68, 68, 220), width=6)
        elif theme == "mask":
            # Vikram skull-eagle insignia
            draw.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], outline=accent, width=3)
            draw.polygon([(cx - 60, cy), (cx, cy - 50), (cx + 60, cy), (cx, cy + 50)], outline=accent, width=2)
            draw.ellipse([cx - 15, cy - 10, cx + 15, cy + 20], fill=(245, 158, 11))
        elif theme == "tiger":
            # Jailer medallion & glasses
            draw.ellipse([cx - 55, cy - 55, cx + 55, cy + 55], outline=(217, 70, 239), width=4)
            draw.rectangle([cx - 40, cy - 12, cx - 5, cy + 12], outline=accent, width=3)
            draw.rectangle([cx + 5, cy - 12, cx + 40, cy + 12], outline=accent, width=3)
            draw.line([(cx - 5, cy), (cx + 5, cy)], fill=accent, width=2)
        elif theme == "chola":
            # Chola tiger banner and spear
            draw.polygon([(cx - 70, cy + 60), (cx, cy - 80), (cx + 70, cy + 60)], outline=accent, width=4)
            draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=accent)
        elif theme == "bandages":
            # Masked vigilante wrapping
            for idx in range(6):
                y_pos = cy - 50 + idx * 20
                draw.line([(cx - 70, y_pos), (cx + 70, y_pos + 10)], fill=(240, 240, 240, 160), width=8)
        elif theme == "lamp":
            # Study lamp and open book
            draw.polygon([(cx - 40, cy + 40), (cx + 40, cy + 40), (cx, cy + 20)], fill=(255, 255, 255, 200))
            draw.ellipse([cx - 25, cy - 40, cx + 25, cy + 10], fill=accent + (220,))
            draw.line([(cx, cy + 10), (cx, cy + 35)], fill=(255, 255, 255), width=3)
        elif theme == "akhada":
            # Wrestling medal and clay ring
            draw.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], outline=accent, width=5)
            draw.ellipse([cx - 35, cy - 35, cx + 35, cy + 35], fill=(217, 119, 6), outline=(255, 255, 255), width=2)
        elif theme == "braid":
            # Mystic moonlight
            draw.ellipse([cx - 55, cy - 55, cx + 55, cy + 55], fill=(244, 63, 94, 180), outline=(255, 255, 255), width=2)
            draw.line([(cx, cy + 30), (cx, cy + 90)], fill=(200, 200, 240, 200), width=4)
        elif theme == "cave":
            # Deep vertical gorge ropes
            draw.polygon([(cx - 80, cy - 70), (cx - 20, cy + 70), (cx - 90, cy + 70)], fill=(13, 148, 136))
            draw.polygon([(cx + 80, cy - 70), (cx + 20, cy + 70), (cx + 90, cy + 70)], fill=(13, 148, 136))
            draw.line([(cx - 10, cy - 70), (cx - 5, cy + 70)], fill=accent, width=3)
        elif theme == "mustache":
            # Ranga's iconic sunglasses & white shirt mass
            draw.rectangle([cx - 50, cy - 20, cx - 10, cy + 10], fill=(250, 204, 21), outline=(0, 0, 0), width=2)
            draw.rectangle([cx + 10, cy - 20, cx + 50, cy + 10], fill=(250, 204, 21), outline=(0, 0, 0), width=2)
            draw.line([(cx - 10, cy - 5), (cx + 10, cy - 5)], fill=(0, 0, 0), width=3)
            # Mustache curve
            draw.arc([cx - 45, cy + 15, cx + 45, cy + 45], start=0, end=180, fill=(255, 255, 255), width=6)
        elif theme == "cross":
            # Shadow political cross
            draw.line([(cx, cy - 70), (cx, cy + 70)], fill=accent, width=7)
            draw.line([(cx - 45, cy - 25), (cx + 45, cy - 25)], fill=accent, width=7)
        elif theme == "gold_mine":
            # KGF hammer & gold block
            draw.rectangle([cx - 45, cy - 10, cx + 45, cy + 30], fill=accent, outline=(255, 255, 255), width=2)
            draw.line([(cx, cy - 60), (cx, cy + 60)], fill=(240, 240, 240), width=5)
        elif theme == "kola":
            # Daiva mask & divine fire
            draw.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], outline=accent, width=4)
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                fx = int(cx + 65 * math.cos(rad))
                fy = int(cy + 65 * math.sin(rad))
                draw.ellipse([fx - 6, fy - 6, fx + 6, fy + 6], fill=(249, 115, 22))
        elif theme == "paw":
            # Dog paw print & friendship path
            draw.ellipse([cx - 20, cy - 10, cx + 20, cy + 25], fill=(255, 255, 255, 220))
            draw.ellipse([cx - 32, cy - 35, cx - 14, cy - 17], fill=(255, 255, 255, 220))
            draw.ellipse([cx - 10, cy - 45, cx + 10, cy - 27], fill=(255, 255, 255, 220))
            draw.ellipse([cx + 14, cy - 35, cx + 32, cy - 17], fill=(255, 255, 255, 220))
        elif theme == "flame_trident":
            # Sacred Trishul
            draw.line([(cx, cy - 75), (cx, cy + 75)], fill=accent, width=5)
            draw.arc([cx - 40, cy - 60, cx + 40, cy - 20], start=0, end=180, fill=accent, width=5)
        elif theme == "jungle":
            # Tropical compass and safari expedition
            draw.ellipse([cx - 55, cy - 55, cx + 55, cy + 55], outline=accent, width=4)
            draw.polygon([(cx, cy - 65), (cx + 18, cy), (cx, cy + 65), (cx - 18, cy)], fill=accent)

        # Top Badge: Industry Name (e.g. TELUGU CINEMA, TAMIL CINEMA, etc.)
        draw.rounded_rectangle([25, 25, 25 + len(item["industry"]) * 8 + 24, 52], radius=6, fill=(15, 23, 42, 220), outline=(255, 255, 255, 60))
        draw.text((36, 33), item["industry"], fill=(255, 255, 255))

        # Bottom shade gradient
        overlay = Image.new("RGBA", (w, 230), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for y in range(230):
            alpha = int(250 * (y / 230.0) ** 1.4)
            overlay_draw.line([(0, y), (w, y)], fill=(10, 14, 22, alpha))
        img.paste(overlay, (0, h - 230), overlay)

        draw = ImageDraw.Draw(img)
        # Genre Badge
        draw.rounded_rectangle([25, h - 205, 25 + len(item["genre"]) * 7 + 24, h - 182], radius=5, fill=item["badge_color"])
        draw.text((35, h - 200), item["genre"], fill=(255, 255, 255))

        # Main Title
        draw.text((25, h - 175), item["title"], fill=(255, 255, 255))
        # Subtitle
        if item.get("subtitle"):
            draw.text((25, h - 150), item["subtitle"], fill=accent)
        # Tagline
        draw.text((25, h - 122), f'"{item["tagline"]}"', fill=(226, 232, 240))
        # Director and Cast
        draw.text((25, h - 94), f'Dir: {item["director"]}', fill=(203, 213, 225))
        draw.text((25, h - 74), item["cast"], fill=(148, 163, 184))
        # Divider line
        draw.line([(25, h - 50), (w - 25, h - 50)], fill=(255, 255, 255, 50), width=1)
        draw.text((25, h - 40), "IMAX LASER  •  DOLBY ATMOS  •  CINEBOOK VIP", fill=(148, 163, 184))

        target_file = output_dir / item["filename"]
        img.save(target_file, "PNG")
        print(f"Generated poster: {target_file}")


def generate_promo_banner():
    """Generates wide cinema promotional banner in assets/promos."""
    promos_dir = Path(__file__).resolve().parent / "assets" / "promos"
    promos_dir.mkdir(parents=True, exist_ok=True)

    w, h = 1120, 200
    top_color = (26, 16, 37)       # Deep rich violet/plum
    bot_color = (13, 17, 23)       # Midnight charcoal

    base = create_gradient_canvas(w, h, top_color, bot_color)
    draw = ImageDraw.Draw(base)

    # Stylized background accent curves / lights
    draw.ellipse([-50, -50, 300, 250], outline=(248, 68, 100, 35), width=24)
    draw.ellipse([w - 250, -40, w + 120, 240], outline=(245, 166, 35, 40), width=16)

    # Left content:
    # Tag badge
    draw.rounded_rectangle([40, 28, 250, 54], radius=6, fill=(248, 68, 100, 230))
    draw.text((52, 35), "★ PAN-INDIA CINEMA FESTIVAL", fill=(255, 255, 255))

    # Main Headline
    draw.text((40, 72), "Celebrate the Magic of Indian Cinema.", fill=(255, 255, 255))
    draw.text((40, 108), "Telugu • Tamil • Hindi • Malayalam • Kannada Blockbusters with 0% Convenience Fee on VIP Passes.",
              fill=(190, 195, 208))

    # CTA Button
    draw.rounded_rectangle([40, 142, 245, 178], radius=6, fill=(248, 68, 100), outline=(255, 255, 255, 60))
    draw.text((58, 151), "Explore Blockbusters  ›", fill=(255, 255, 255))

    # Secondary link
    draw.text((265, 152), "Multi-Language Audio & Subtitles in All Audis", fill=(148, 163, 184))

    # Right side: Stylized Cinema Reel & Tickets Graphics
    cx, cy = w - 160, h // 2
    # Film Reel
    draw.ellipse([cx - 55, cy - 55, cx + 55, cy + 55], fill=(30, 41, 59, 220), outline=(245, 166, 35), width=4)
    draw.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=(15, 23, 42), outline=(248, 68, 100), width=3)
    for angle_deg in [0, 60, 120, 180, 240, 300]:
        rad = math.radians(angle_deg)
        hx = int(cx + 36 * math.cos(rad))
        hy = int(cy + 36 * math.sin(rad))
        draw.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=(15, 23, 42))

    # Ticket Graphic
    tx, ty = cx - 110, cy - 35
    draw.rounded_rectangle([tx, ty, tx + 65, ty + 75], radius=6, fill=(248, 68, 100, 230), outline=(255, 255, 255))
    draw.text((tx + 10, ty + 15), "DESI", fill=(255, 255, 255))
    draw.text((tx + 10, ty + 38), "PASS", fill=(255, 255, 255))

    target = promos_dir / "promo_banner.png"
    base.save(target, "PNG")
    print(f"Generated banner: {target}")


if __name__ == "__main__":
    generate_indian_movie_posters()
    generate_promo_banner()
