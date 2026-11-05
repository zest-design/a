# Horizontal floating screens in the HostGator AllPass look (reuses colours, type, logos and helpers of hg_design).
from hg_design import *
CW, CH = 800, 440
def hpanel():
    S = 2; im = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0))
    mk = Image.new("L", im.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, CW * S - 1, CH * S - 1), 40 * S, fill=255)
    bg = grad(CW * S, CH * S, BG1, BG0, 0.9); bg.putalpha(mk); im.alpha_composite(bg)
    lt = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(lt).ellipse((-200 * S, -260 * S, 520 * S, 220 * S), fill=(60, 90, 220, 75))
    lt = lt.filter(ImageFilter.GaussianBlur(70 * S)); lm = Image.new("L", im.size, 0); lm.paste(lt.getchannel("A"), (0, 0), mk); lt.putalpha(lm); im.alpha_composite(lt)
    bd = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(bd).rounded_rectangle((1, 1, CW * S - 2, CH * S - 2), 40 * S, outline=(120, 140, 255, 120), width=3 * S)
    im.alpha_composite(bd); return im.resize((CW, CH), Image.LANCZOS)
def ltitle(im, x, y, a, b, size=44, tail=None):
    # left-aligned: white line + gradient line (+ white tail)
    d = ImageDraw.Draw(im); f = F(size, 700); d.text((x, y), a, font=f, fill=WHITE, anchor="la")
    g = grad_text(b, f); y2 = y + int(size * 1.12); im.alpha_composite(g, (x, y2))
    if tail: d.text((x + g.width + f.getlength(" "), y2), tail, font=f, fill=WHITE, anchor="la")
def fade(img, a):
    if a >= 1: return img
    img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * max(0, a)))); return img
def slide_in(im, part, x, y, kk, dy=18):
    if kk <= 0: return
    im.alpha_composite(fade(part, min(1, kk / 4)), (int(x), int(y + (1 - ease_out_cubic(kk / 8)) * dy)))

def h_allias(k, beats):
    im = hpanel(); d = ImageDraw.Draw(im)
    im.alpha_composite(chip("HostGator AllPass"), (48, 48))
    ltitle(im, 48, 110, "Todas las IAs en", "una sola", 46, "suscripción")
    if k > beats[-1] + 6: pop_in(im, ytbutton("Quiero mi AllPass"), 48 + 120, 330, k - beats[-1] - 6)
    items = [("chatgpt", "ChatGPT"), ("claude", "Claude"), ("grok", "Grok"), ("chinas", "IAs chinas")]
    for i, (n, lab) in enumerate(items):
        cx = 560 + (i % 2) * 150; cy = 140 + (i // 2) * 170
        if n == "chinas":
            b = Image.new("RGBA", (100, 100), (0, 0, 0, 0)); ImageDraw.Draw(b).ellipse((0, 0, 99, 99), fill=(255, 255, 255, 22), outline=(255, 255, 255, 70), width=2)
            ImageDraw.Draw(b).text((50, 50), "+", font=F(54, 500), fill=WHITE, anchor="mm")
        else: b = logo(n, 100)
        kk = k - beats[i]; pop_in(im, b, cx, cy, kk)
        if kk > 2: d.text((cx, cy + 72), lab, font=F(23, 600), fill=WHITE, anchor="mm")
    return im

def h_barata(k, beats):
    im = hpanel(); d = ImageDraw.Draw(im)
    d.text((48, 52), "Sin AllPass", font=F(26, 500), fill=MUTED, anchor="la")
    for i, (n, lab) in enumerate([("chatgpt", "ChatGPT"), ("claude", "Claude"), ("grok", "Grok")]):
        kk = k - ([0] + beats)[min(i, len(beats))]
        row = Image.new("RGBA", (380, 72), (0, 0, 0, 0)); dr = ImageDraw.Draw(row)
        dr.rounded_rectangle((0, 0, 379, 71), 20, fill=(255, 255, 255, 14), outline=(255, 255, 255, 34))
        row.alpha_composite(logo(n, 48), (14, 12)); dr.text((76, 36), lab, font=F(25, 600), fill=WHITE, anchor="lm")
        dr.text((362, 36), "1 suscripción", font=F(20, 500), fill=(240, 120, 110), anchor="rm")
        slide_in(im, row, 48, 102 + i * 92, kk)
    kk = k - beats[-1] - 4
    if kk > 0:
        d.line((470, 70, 470, 370), fill=(255, 255, 255, 40), width=2)
        d.text((630, 110), "Con AllPass", font=F(28, 700), fill=WHITE, anchor="mm")
        pop_in(im, grad_text("1 suscripción", F(48, 800)), 630, 190, kk)
        if kk > 5: st = logo_stack(["gemini", "claude", "chatgpt", "grok"], 56, 38); slide_in(im, st, 630 - st.width / 2, 260, kk - 5)
    return im

def h_compara(k, beats):
    im = hpanel(); d = ImageDraw.Draw(im)
    f = F(36, 700); a = "Compara respuestas. "; g = grad_text("Decide mejor.", f); tw = f.getlength(a) + g.width
    d.text(((CW - tw) / 2, 44), a, font=f, fill=WHITE, anchor="la"); im.alpha_composite(g, (int((CW - tw) / 2 + f.getlength(a)), 44))
    def bubble(n, name, lines, col):
        h = 196; b = Image.new("RGBA", (330, h), (0, 0, 0, 0)); db = ImageDraw.Draw(b)
        db.rounded_rectangle((0, 0, 329, h - 1), 22, fill=(255, 255, 255, 16), outline=col + (160,), width=2)
        b.alpha_composite(logo(n, 40), (16, 16)); db.text((66, 36), name, font=F(23, 700), fill=WHITE, anchor="lm")
        for j, l in enumerate(lines): db.text((20, 84 + j * 30), l, font=F(20, 400), fill=(205, 210, 222), anchor="lm")
        return b
    slide_in(im, bubble("chatgpt", "ChatGPT", ["La mejor opción es la A,", "por costo y rapidez."], (90, 160, 255)), 48, 130, k - beats[0])
    kk = k - beats[1]
    if kk > 0:
        c = chip("cuestiona", F(19, 600), dot=VIOLET); pop_in(im, c, CW / 2, 228, kk)
        d.text((CW / 2, 268), "→", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30), fill=(150, 140, 255), anchor="mm")
    slide_in(im, bubble("claude", "Claude", ["Revisé la respuesta de", "ChatGPT: la B escala", "mejor a largo plazo."], VIOLET), CW - 48 - 330, 130, k - beats[1] - 3)
    return im

def h_agente(k, beats):
    im = hpanel(); d = ImageDraw.Draw(im)
    ltitle(im, 48, 44, "Crea tu propio", "agente", 40)
    kk = k - beats[0]
    if kk > 0:
        cd = Image.new("RGBA", (330, 150), (0, 0, 0, 0)); dc = ImageDraw.Draw(cd)
        dc.rounded_rectangle((0, 0, 329, 149), 22, fill=(255, 255, 255, 16), outline=(255, 255, 255, 40))
        av = grad(64, 64); mm = Image.new("L", (64, 64), 0); ImageDraw.Draw(mm).ellipse((0, 0, 63, 63), fill=255); av.putalpha(mm); cd.alpha_composite(av, (18, 20))
        dc.text((50, 52), "✦", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30), fill=WHITE, anchor="mm")
        dc.text((96, 38), "Mi agente", font=F(25, 700), fill=WHITE, anchor="lm"); dc.text((96, 68), "Ventas · Responde dudas", font=F(18, 400), fill=MUTED, anchor="lm")
        if kk > 10: cd.alpha_composite(chip("Guardado", F(18, 600)), (18, 98))
        pop_in(im, cd, 48 + 165, 250, kk)
    kk = k - beats[1]
    if kk > 0:
        d.text((420, 74), "En la conversación", font=F(22, 500), fill=MUTED, anchor="la")
        ib = Image.new("RGBA", (334, 66), (0, 0, 0, 0)); di = ImageDraw.Draw(ib)
        di.rounded_rectangle((0, 0, 333, 65), 33, fill=(255, 255, 255, 20), outline=(120, 140, 255, 160), width=2)
        txt = "@Mi agente ayúdame"; n = min(len(txt), int(kk * 1.4)); f = F(22, 500)
        tg = txt[:min(n, 10)]; rest = txt[10:n] if n > 10 else ""
        di.text((24, 33), tg, font=f, fill=(120, 170, 255), anchor="lm"); di.text((24 + f.getlength(tg), 33), rest, font=f, fill=WHITE, anchor="lm")
        sb = grad(44, 44); ms = Image.new("L", (44, 44), 0); ImageDraw.Draw(ms).ellipse((0, 0, 43, 43), fill=255); sb.putalpha(ms); ib.alpha_composite(sb, (278, 11))
        di.text((300, 33), "↑", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22), fill=WHITE, anchor="mm")
        im.alpha_composite(ib, (420, 112))
    kk = k - beats[2]
    if kk > 0:
        b = Image.new("RGBA", (334, 110), (0, 0, 0, 0)); db = ImageDraw.Draw(b)
        db.rounded_rectangle((0, 0, 333, 109), 22, fill=(255, 255, 255, 14), outline=(255, 255, 255, 34))
        db.text((20, 32), "Mi agente", font=F(21, 700), fill=(150, 180, 255), anchor="lm")
        db.text((20, 70), "El envío sale hoy mismo.", font=F(20, 400), fill=(210, 214, 226), anchor="lm")
        slide_in(im, b, 420, 210, kk)
    return im

def h_10x(k, beats):
    im = hpanel(); d = ImageDraw.Draw(im)
    ltitle(im, 48, 70, "Todas las IAs en", "un único lugar", 42)
    st = logo_stack(["gemini", "claude", "chatgpt", "grok"], 76, 52); slide_in(im, st, 48, 250, k)
    kk = k - beats[0]
    if kk > 0:
        g = glow(grad_text("10x", F(170, 800)), (90, 110, 255), 20, 140, 30); pop_in(im, g, 620, 190, kk, 8)
        if kk > 6: d.text((620, 330), "menos precio", font=F(34, 700), fill=WHITE, anchor="mm")
    return im
