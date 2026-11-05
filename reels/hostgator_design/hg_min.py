# Minimal horizontal floating screens (HostGator AllPass look): big logos/icons, 1-3 big words, no small text.
from hg_h import *
DJB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def sym(ch, size, col=WHITE):
    f = ImageFont.truetype(DJB, size); im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((size, size), ch, font=f, fill=col, anchor="mm"); return im.crop(im.getbbox())
def wordmark(size=60):
    # "AllPass" in white with the gradient on "Pass" (no small print)
    f = F(size, 800); a = grad_text("All", f, WHITE, WHITE); b = grad_text("Pass", f)
    im = Image.new("RGBA", (a.width + b.width - 4, max(a.height, b.height)), (0, 0, 0, 0)); im.alpha_composite(a, (0, 0)); im.alpha_composite(b, (a.width - 4, 0)); return im
def plus_circle(d):
    b = Image.new("RGBA", (d, d), (0, 0, 0, 0)); ImageDraw.Draw(b).ellipse((0, 0, d - 1, d - 1), fill=(255, 255, 255, 24), outline=(255, 255, 255, 80), width=3)
    b.alpha_composite(sym("+", int(d * 0.5)), (d // 2 - sym("+", int(d * 0.5)).width // 2, d // 2 - sym("+", int(d * 0.5)).height // 2)); return b

# 1 "AllPass, que tiene todas las IAs: ChatGPT, Claude, Grok, todas las chinas"
def m_allias(k, beats):
    im = hpanel(); wm = wordmark(64); pop_in(im, wm, CW / 2, 92, k)
    items = ["chatgpt", "claude", "grok", None]
    for i, n in enumerate(items):
        b = logo(n, 132) if n else plus_circle(132)
        pop_in(im, b, 130 + i * 180, 280, k - beats[i])
    return im

# 2 "mucho más barata que una sola... que ChatGPT, que Claude"
def coin(d, col=(240, 110, 100)):
    b = Image.new("RGBA", (d, d), (0, 0, 0, 0)); ImageDraw.Draw(b).ellipse((0, 0, d - 1, d - 1), fill=col)
    s = sym("$", int(d * 0.62), (20, 22, 30)); b.alpha_composite(s, ((d - s.width) // 2, (d - s.height) // 2)); return b
def m_barata(k, beats):
    im = hpanel()
    for i, n in enumerate(["chatgpt", "claude", "grok"]):
        kk = k - ([0] + beats)[min(i, len(beats))]; y = 92 + i * 128
        pop_in(im, logo(n, 96), 110, y, kk); pop_in(im, coin(56), 196, y + 26, kk - 2)
    kk = k - beats[-1] - 4
    if kk > 0:
        pop_in(im, sym("→", 70, (150, 160, 255)), 330, 220, kk)
        pop_in(im, wordmark(70), 580, 170, kk)
        pop_in(im, coin(84, YEL), 580, 290, kk - 3)
    return im

# 3 "puedes poner que un modelo cuestione la respuesta del otro"
def bubble(w, h, col, tail_left=True):
    b = Image.new("RGBA", (w, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=(255, 255, 255, 18), outline=col + (200,), width=3)
    x = 40 if tail_left else w - 70; d.polygon([(x, h - 2), (x + 30, h - 2), (x + (0 if tail_left else 30), h + 18)], fill=(255, 255, 255, 18), outline=None)
    return b
def m_compara(k, beats):
    im = hpanel()
    kk = k - beats[0]
    if kk > 0:
        pop_in(im, logo("chatgpt", 120), 150, 300, kk)
        b = bubble(200, 110, (90, 160, 255)); dots = sym("•••", 40, (200, 210, 230)); b.alpha_composite(dots, ((200 - dots.width) // 2, (110 - dots.height) // 2))
        pop_in(im, b, 190, 130, kk - 3)
    kk = k - beats[1]
    if kk > 0:
        pop_in(im, logo("claude", 120), CW - 150, 300, kk)
        b = bubble(200, 110, VIOLET, False); q = sym("?", 64, (190, 170, 255)); b.alpha_composite(q, ((200 - q.width) // 2, (110 - q.height) // 2))
        pop_in(im, b, CW - 190, 130, kk - 3)
        pop_in(im, sym("⇄", 74, (150, 160, 255)), CW / 2, 300, kk - 5)
    return im

# 4 "crear tu propio agente, dejarlo guardado... pones al agente en la conversación"
def m_agente(k, beats):
    im = hpanel(); d = ImageDraw.Draw(im)
    kk = k - beats[0]
    if kk > 0:
        av = grad(150, 150); mm = Image.new("L", (150, 150), 0); ImageDraw.Draw(mm).ellipse((0, 0, 149, 149), fill=255); av.putalpha(mm)
        st = sym("✦", 70); av.alpha_composite(st, ((150 - st.width) // 2, (150 - st.height) // 2))
        pop_in(im, glow(av, (90, 110, 255), 18, 150, 30), 190, 180, kk)
        if kk > 3: d.text((190, 320), "Tu agente", font=F(46, 700), fill=WHITE, anchor="mm")
    kk = k - beats[1]
    if kk > 0:   # saved
        g = Image.new("RGBA", (64, 64), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((0, 0, 63, 63), fill=(60, 200, 120)); c = sym("✓", 38); g.alpha_composite(c, ((64 - c.width) // 2, (64 - c.height) // 2))
        pop_in(im, g, 250, 120, kk)
    kk = k - beats[2]
    if kk > 0:   # called into the chat with @
        ib = Image.new("RGBA", (330, 96), (0, 0, 0, 0)); di = ImageDraw.Draw(ib)
        di.rounded_rectangle((0, 0, 329, 95), 48, fill=(255, 255, 255, 20), outline=(120, 140, 255, 190), width=3)
        txt = "@agente"; n = min(len(txt), int(kk * 0.9) + 1); di.text((36, 48), txt[:n], font=F(44, 700), fill=(130, 175, 255), anchor="lm")
        im.alpha_composite(ib, (420, 172))
    return im

# 5 "todas las IAs en un único lugar y además por 10 veces menos el precio"
def m_10x(k, beats):
    im = hpanel(); d = ImageDraw.Draw(im)
    st = logo_stack(["gemini", "claude", "chatgpt", "grok"], 96, 66); slide_in(im, st, 60, 170, k)
    kk = k - beats[0]
    if kk > 0:
        g = glow(grad_text("10x", F(190, 800)), (90, 110, 255), 20, 140, 30); pop_in(im, g, 590, 185, kk, 8)
        if kk > 6: d.text((590, 345), "más barato", font=F(46, 700), fill=WHITE, anchor="mm")
    return im
