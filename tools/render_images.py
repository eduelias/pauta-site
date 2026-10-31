"""Render the site's link-preview card (site/og.png, 1200x630) and the launch campaign images
(campaign/*.png). Same drawing as the app's tools/render_images.py in eduelias/pauta: the
gradient logo and the board's request cards on the dark background.

macOS only (uses the system SF font). Run: make images
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SF = "/System/Library/Fonts/SFNS.ttf"
VIOLET, ORANGE = (123, 92, 255), (255, 106, 61)
BG = (14, 14, 18)
INK, INK2, MUTED = (242, 242, 247), (200, 199, 210), (150, 148, 162)
S = 2  # supersample

TODO, DOING, WAITING, DONE = (163, 177, 198), (122, 167, 255), (245, 166, 91), (95, 211, 139)
CARDS = {
    "padaria": ("Padaria Trigo de Ouro", "Novos criativos do panetone", "A fazer", TODO, "Hoje",
                (110, 74, 30)),
    "clinica": ("Clínica Bem Estar", "Campanha de limpeza de pele", "Em andamento", DOING,
                "Amanhã", (64, 46, 140)),
    "studio": ("Studio Lume Pilates", "Aprovar arte da aula", "Aguardando", WAITING, "Cliente",
               (34, 92, 60)),
    "cafe": ("Café Grão Mineiro", "Relatório de outubro", "Concluído", DONE, "✓", (92, 52, 140)),
    "pet": ("Pet Shop Amigo Fiel", "Vídeo curto para os Reels", "Em andamento", DOING, "8 nov",
            (140, 30, 80)),
}


def font(size, weight="Bold"):
    f = ImageFont.truetype(SF, int(size * S))
    f.set_variation_by_name(weight)
    return f


def gradient(w, h, a=VIOLET, b=ORANGE):
    """Diagonal gradient, built small and scaled up (smooth enough, and fast)."""
    small = Image.new("RGB", (64, 64))
    px = small.load()
    for y in range(64):
        for x in range(64):
            t = (x / 63 + y / 63) / 2
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return small.resize((w, h), Image.BILINEAR)


def logo(size):
    """The app icon: gradient rounded square, three bars and a dot (icon.svg)."""
    k = size / 64
    tile = gradient(size, size)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=16 * k, fill=255)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img.paste(tile, (0, 0), mask)
    d = ImageDraw.Draw(img)
    for x, y, w, op in ((15, 17, 34, 255), (15, 29, 24, 217), (15, 41, 14, 178)):
        d.rounded_rectangle(
            [x * k, y * k, (x + w) * k, (y + 6) * k], radius=3 * k, fill=(255, 255, 255, op)
        )
    d.ellipse([40 * k, 39 * k, 50 * k, 49 * k], fill=(255, 255, 255, 255))
    return img


def canvas(w, h, glows):
    """Dark background with blurred violet/orange glows: [(x0, y0, x1, y1, colour), ...]."""
    img = Image.new("RGB", (w * S, h * S), BG)
    d = ImageDraw.Draw(img)
    for x0, y0, x1, y1, c in glows:
        d.ellipse([x0 * S, y0 * S, x1 * S, y1 * S], fill=c)
    return img.filter(ImageFilter.GaussianBlur(150 * S))


def card(img, key, x, y, w=440, rot=0, k=1.0, highlight=False):
    """One request card, like the board's, pasted at (x, y) in 1x pixels."""
    client, what, status, color, due, av = CARDS[key]
    cw, ch = int(w * k * S), int(166 * k * S)
    pad = int(40 * k * S)
    layer = Image.new("RGBA", (cw + 2 * pad, ch + 2 * pad), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([pad, pad + 10 * S, pad + cw, pad + ch + 10 * S], radius=22 * k * S,
                         fill=(0, 0, 0, 110))
    layer = layer.filter(ImageFilter.GaussianBlur(14 * S))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([pad, pad, pad + cw, pad + ch], radius=22 * k * S, fill=(28, 28, 36, 255),
                         outline=(139, 123, 255, 255) if highlight else (52, 52, 64, 255),
                         width=int((3 if highlight else 2) * S))

    def u(v):
        return v * k * S

    ld.rounded_rectangle([pad + u(24), pad + u(24), pad + u(60), pad + u(60)], radius=u(10),
                         fill=av)
    initials = "".join(p[0] for p in client.split() if p[0].isupper())[:2]
    ld.text((pad + u(42), pad + u(42)), initials, font=font(15 * k, "Bold"), fill=INK, anchor="mm")
    ld.text((pad + u(74), pad + u(42)), client, font=font(21 * k, "Semibold"), fill=(205, 204, 214),
            anchor="lm")
    ld.text((pad + u(24), pad + u(76)), what, font=font(25 * k, "Semibold"), fill=INK)
    pf = font(18 * k, "Semibold")
    tw = ld.textlength(status, font=pf)
    px, py = pad + u(24), pad + u(134)
    pill = tuple(int(c * 0.22 + 28 * 0.78) for c in color)
    ld.rounded_rectangle([px, py - u(15), px + tw + u(44), py + u(15)], radius=u(15), fill=pill)
    ld.ellipse([px + u(13), py - u(4), px + u(21), py + u(4)], fill=color)
    ld.text((px + u(30), py), status, font=pf, fill=color, anchor="lm")
    due_color = WAITING if due in ("Hoje", "Amanhã") else (140, 138, 150)
    ld.text((pad + cw - u(24), py), due, font=pf, fill=due_color, anchor="rm")
    if rot:
        layer = layer.rotate(rot, resample=Image.BICUBIC, expand=False)
    img.paste(layer, (int(x * S - pad), int(y * S - pad)), layer)


def wordmark(img, x, y, size):
    lg = logo(int(size * S))
    img.paste(lg, (int(x * S), int(y * S)), lg)
    d = ImageDraw.Draw(img)
    d.text(((x + size * 1.28) * S, (y + size / 2) * S), "pauta", font=font(size * 0.95, "Heavy"),
           fill=INK, anchor="lm")


def text(img, xy, s, size, weight="Bold", fill=INK, anchor="la", spacing=1.18):
    d = ImageDraw.Draw(img)
    f = font(size, weight)
    x, y = xy
    for i, line in enumerate(s.split("\n")):
        d.text((x * S, (y + i * size * spacing) * S), line, font=f, fill=fill, anchor=anchor)


def gradient_text(img, xy, s, size, weight="Heavy"):
    """Text filled with the logo gradient."""
    f = font(size, weight)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text((xy[0] * S, xy[1] * S), s, font=f, fill=255)
    bbox = mask.getbbox()
    g = gradient(bbox[2] - bbox[0], bbox[3] - bbox[1])
    img.paste(g, bbox[:2], mask.crop(bbox))


def pill(img, xy, s, size=26, fg=(255, 255, 255), bg=(255, 106, 61)):
    d = ImageDraw.Draw(img)
    f = font(size, "Bold")
    x, y = xy
    tw = d.textlength(s, font=f) / S
    h = size * 1.9
    d.rounded_rectangle([x * S, y * S, (x + tw + size * 1.4) * S, (y + h) * S], radius=h / 2 * S,
                        fill=bg)
    d.text(((x + size * 0.7) * S, (y + h / 2) * S), s, font=f, fill=fg, anchor="lm")


def save(img, w, h, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.resize((w, h), Image.LANCZOS).save(path, optimize=True)
    print("wrote", path.relative_to(ROOT))


def og():
    W, H = 1200, 630
    img = canvas(W, H, [(-260, -300, 520, 420, (62, 46, 140)), (760, 300, 1500, 980, (120, 52, 34))])
    wordmark(img, 88, 96, 84)
    text(img, (90, 236), "A fila de pedidos\ndo seu time de\nmarketing.", 52, "Heavy")
    text(img, (92, 452), "Pedidos por cliente, quadro, financeiro\ne arquivos num lugar só.", 26,
         "Medium", INK2, spacing=1.35)
    text(img, (92, 556), "www.pauta.cc", 24, "Semibold", MUTED)
    for i, (key, rot, dx) in enumerate((("padaria", -4, 10), ("clinica", 2, 60), ("cafe", -1, 25))):
        card(img, key, 660 + dx, 40 + i * 182, rot=rot, highlight=key == "clinica")
    save(img, W, H, ROOT / "site" / "og.png")


def post():
    """Instagram feed post, 4:5."""
    W, H = 1080, 1350
    img = canvas(W, H, [(-300, -260, 600, 560, (70, 50, 160)), (560, 900, 1400, 1700, (130, 56, 34))])
    wordmark(img, 80, 80, 64)
    text(img, (80, 230), "Chega de pedido\nperdido no", 82, "Heavy", spacing=1.1)
    gradient_text(img, (80, 230 + 82 * 2.2), "WhatsApp.", 82)
    text(img, (82, 535), "Cada pedido com briefing, prazo e histórico,\norganizado por cliente.",
         32, "Medium", INK2, spacing=1.35)
    for i, (key, rot, dx) in enumerate((("padaria", -1.5, 0), ("clinica", 1, 90), ("studio", -1, 30))):
        card(img, key, 100 + dx, 690 + i * 182, w=820, rot=rot, k=0.95, highlight=key == "clinica")
    pill(img, (80, 1242), "Beta fechado", 24)
    text(img, (1000, 1263), "pauta.cc", 34, "Bold", INK, anchor="rm")
    save(img, W, H, ROOT / "campaign" / "ig-post.png")


def story():
    """Instagram story, 9:16. Keeps the top 250 px and bottom 340 px clear for the app's UI
    and the link sticker."""
    W, H = 1080, 1920
    img = canvas(W, H, [(-300, -100, 700, 900, (70, 50, 160)), (500, 1200, 1500, 2200, (130, 56, 34))])
    wordmark(img, 80, 260, 64)
    text(img, (80, 420), "O seu time ainda\ncontrola os pedidos\nnuma planilha?", 76, "Heavy",
         spacing=1.12)
    for i, (key, rot, dx) in enumerate((("padaria", -3, 0), ("clinica", 2, 110), ("studio", -2, 30),
                                        ("cafe", 1, 90))):
        card(img, key, 100 + dx, 770 + i * 172, w=760, k=0.92, rot=rot / 2, highlight=key == "clinica")
    text(img, (80, 1470), "Pauta: os pedidos do time,", 46, "Bold")
    gradient_text(img, (80, 1470 + 46 * 1.25), "num lugar só.", 46, "Heavy")
    text(img, (82, 1610), "Beta fechado · entre em pauta.cc", 32, "Semibold", INK2)
    save(img, W, H, ROOT / "campaign" / "ig-story.png")


def stages():
    """Square carousel slide: the four stages of a request and what each person sees."""
    W, H = 1080, 1080
    img = canvas(W, H, [(-260, -260, 560, 560, (70, 50, 160)), (620, 640, 1360, 1360, (130, 56, 34))])
    wordmark(img, 80, 80, 56)
    text(img, (80, 200), "Quem atende pede.\nQuem executa entrega.", 62, "Heavy", spacing=1.12)
    gradient_text(img, (80, 200 + 62 * 2.24), "Todo mundo vê.", 62)
    d = ImageDraw.Draw(img)
    stages_ = (("A fazer", TODO), ("Em andamento", DOING), ("Aguardando", WAITING),
               ("Concluído", DONE))
    y = 520
    for i, (label, color) in enumerate(stages_):
        cy = y + i * 112
        d.ellipse([(96) * S, (cy - 18) * S, (132) * S, (cy + 18) * S], fill=color)
        if i < 3:
            d.line([(114 * S, (cy + 22) * S), (114 * S, (cy + 90) * S)], fill=(60, 60, 72),
                   width=4 * S)
        d.text((160 * S, cy * S), label, font=font(44, "Bold"), fill=color, anchor="lm")
    notes = ("o pedido chega com o briefing", "alguém assumiu", "esperando o cliente",
             "na linha do tempo, para sempre")
    for i, n in enumerate(notes):
        d.text((1000 * S, (y + i * 112) * S), n, font=font(26, "Medium"), fill=MUTED, anchor="rm")
    text(img, (80, 990), "pauta.cc", 34, "Bold")
    pill(img, (788, 984), "Beta fechado", 22)
    save(img, W, H, ROOT / "campaign" / "ig-etapas.png")


og()
post()
story()
stages()
