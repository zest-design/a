# HostGator AllPass look: near-black navy panels, blue->violet gradients and glows, Outfit type, yellow buttons, white logo circles.
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = "/tmp/claude-0/-home-user-a/a523e79c-ba27-50f9-be90-91ab18a28e09/scratchpad/derrota/assets"
BLUE = (46, 140, 240); VIOLET = (112, 92, 230); YEL = (255, 200, 0); BG0 = (11, 14, 22); BG1 = (19, 24, 36)
WHITE = (255, 255, 255); MUTED = (160, 168, 186); LINE = (255, 255, 255, 26)
def F(size, w=700):
    f = ImageFont.truetype(f"{A}/Outfit.ttf", int(size)); f.set_variation_by_axes([w]); return f
def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_out_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def grad(w, h, c0=BLUE, c1=VIOLET, ang=0.0):
    x = np.linspace(0, 1, w)[None, :, None]; y = np.linspace(0, 1, h)[:, None, None]
    t = np.clip(x * math.cos(ang) + y * math.sin(ang), 0, 1)
    return Image.fromarray((np.array(c0) * (1 - t) + np.array(c1) * t).astype(np.uint8)).convert("RGBA")
def grad_text(txt, f, c0=BLUE, c1=VIOLET):
    bb = f.getbbox(txt); w, h = bb[2] + 4, bb[3] + 8
    mk = Image.new("L", (w, h), 0); ImageDraw.Draw(mk).text((0, 0), txt, font=f, fill=255)
    g = grad(w, h, c0, c1); g.putalpha(mk); return g
def glow(im, col, rad, alpha=150, pad=60):
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    a = im.getchannel("A").point(lambda v: int(v * alpha / 255)); g = Image.new("RGBA", im.size, col + (0,)); g.putalpha(a)
    out.alpha_composite(g, (pad, pad)); out = out.filter(ImageFilter.GaussianBlur(rad)); out.alpha_composite(im, (pad, pad)); return out
_logo = {}
def logo(name, d):
    # white circle with the logo inside (as on the AllPass page)
    key = (name, d)
    if key in _logo: return _logo[key]
    S = 4; c = Image.new("RGBA", (d * S, d * S), (0, 0, 0, 0)); dc = ImageDraw.Draw(c)
    dark = name in ("chatgpt", "grok")
    dc.ellipse((0, 0, d * S - 1, d * S - 1), fill=(255, 255, 255), outline=(225, 228, 236), width=2 * S)
    lg = Image.open(f"{A}/{name}.png").convert("RGBA")
    if dark:   # white glyphs -> black on the white circle
        r, g, b, al = lg.split(); lg = Image.merge("RGBA", (r.point(lambda v: 18), g.point(lambda v: 18), b.point(lambda v: 18), al))
    s = 0.58 if name != "perplexity" else 0.62
    lw = int(d * S * s); lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    c.alpha_composite(lg, ((d * S - lg.width) // 2, (d * S - lg.height) // 2))
    c = c.resize((d, d), Image.LANCZOS); _logo[key] = c; return c
def logo_stack(names, d, step):
    w = d + step * (len(names) - 1); im = Image.new("RGBA", (w + 4, d + 4), (0, 0, 0, 0))
    for i, n in enumerate(names):
        rg = Image.new("RGBA", (d + 4, d + 4), (0, 0, 0, 0)); ImageDraw.Draw(rg).ellipse((0, 0, d + 3, d + 3), fill=BG0)
        im.alpha_composite(rg, (i * step, 0)); im.alpha_composite(logo(n, d), (i * step + 2, 2))
    return im

# ---------------- AllPass tag (pill, blue->violet like the "1 ano" toggle / "Recomendado" card, yellow word, logo stack)
def allpass_tag():
    f = F(80, 800); S = 2
    txt = "AllPass"; tw = f.getlength(txt); st = logo_stack(["gemini", "claude", "chatgpt", "grok"], 64, 40)
    w, h = int(tw + st.width + 3 * 34), 116
    pill = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    mk = Image.new("L", (w * S, h * S), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, w * S - 1, h * S - 1), h * S // 2, fill=255)
    g = grad(w * S, h * S, (38, 132, 246), (118, 88, 232), 0.25); g.putalpha(mk); pill.alpha_composite(g)
    hi = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); ImageDraw.Draw(hi).rounded_rectangle((6 * S, 4 * S, w * S - 6 * S, h * S // 2), h * S // 3, fill=(255, 255, 255, 46))
    hi = hi.filter(ImageFilter.GaussianBlur(6 * S)); hm = Image.new("L", hi.size, 0); hm.paste(hi.getchannel("A"), (0, 0), mk); hi.putalpha(hm); pill.alpha_composite(hi)
    ImageDraw.Draw(pill).rounded_rectangle((1, 1, w * S - 2, h * S - 2), h * S // 2, outline=(170, 200, 255, 150), width=2 * S)
    pill = pill.resize((w, h), Image.LANCZOS); d = ImageDraw.Draw(pill)
    pill.alpha_composite(st, (30, (h - st.height) // 2))
    d.text((30 + st.width + 22, h / 2 + 2), txt, font=f, fill=YEL, anchor="lm")
    return glow(pill, (80, 110, 255), 26, 170)

# ---------------- floating vertical screen ----------------------------------------------
CW, CH = 380, 600
def panel(title_top=None):
    S = 2; im = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0))
    mk = Image.new("L", im.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, CW * S - 1, CH * S - 1), 40 * S, fill=255)
    bg = grad(CW * S, CH * S, BG1, BG0, 1.2); bg.putalpha(mk); im.alpha_composite(bg)
    # soft blue/violet light in the upper part, like the hero of the page
    lt = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(lt).ellipse((-60 * S, -200 * S, (CW + 60) * S, 220 * S), fill=(60, 90, 220, 70))
    lt = lt.filter(ImageFilter.GaussianBlur(60 * S)); lm = Image.new("L", im.size, 0); lm.paste(lt.getchannel("A"), (0, 0), mk); lt.putalpha(lm); im.alpha_composite(lt)
    bd = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(bd).rounded_rectangle((1, 1, CW * S - 2, CH * S - 2), 40 * S, outline=(120, 140, 255, 120), width=3 * S)
    im.alpha_composite(bd)
    return im.resize((CW, CH), Image.LANCZOS)
def chip(txt, f=None, dot=(70, 210, 130)):
    f = f or F(20, 500); w = int(f.getlength(txt) + 52); h = 38
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=(255, 255, 255, 18), outline=(255, 255, 255, 40), width=1)
    d.ellipse((16, h / 2 - 5, 26, h / 2 + 5), fill=dot); d.text((36, h / 2), txt, font=f, fill=(200, 206, 220), anchor="lm"); return im
def ytbutton(txt, w=None):
    f = F(24, 700); w = w or int(f.getlength(txt) + 70); h = 58
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 14, fill=YEL); d.text((w / 2, h / 2), txt, font=f, fill=(20, 22, 30), anchor="mm"); return im
def center_text(d, y, txt, f, fill=WHITE, w=CW):
    d.text((w / 2, y), txt, font=f, fill=fill, anchor="mm")
def title2(im, y, a, b_grad, c=None, size=36):
    # one line white + one line gradient (+ optional white tail), centred
    d = ImageDraw.Draw(im); f = F(size, 700)
    center_text(d, y, a, f)
    g = grad_text(b_grad, f); y2 = y + int(size * 0.62)
    if c:
        tw = g.width + f.getlength(" " + c); x = (CW - tw) / 2
        im.alpha_composite(g, (int(x), y2)); d.text((x + g.width + f.getlength(" "), y2), c, font=f, fill=WHITE, anchor="la")
    else: im.alpha_composite(g, (int((CW - g.width) / 2), y2))
def pop_in(im, base, x, y, k, n=7):
    if k <= 0: return
    s = 0.6 + 0.4 * ease_out_back(k / n, 2.2); a = min(1, k / 3)
    t = base.resize((max(1, int(base.width * s)), max(1, int(base.height * s))), Image.BICUBIC)
    if a < 1: t = t.copy(); t.putalpha(t.getchannel("A").point(lambda v: int(v * a)))
    im.alpha_composite(t, (int(x - t.width / 2), int(y - t.height / 2)))

# scene 1: all the AIs in one subscription (logos pop as he names them)
def scene_allias(k, beats):
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(chip("HostGator AllPass"), (int((CW - chip("HostGator AllPass").width) / 2), 40))
    title2(im, 120, "Todas las IAs en", "una sola", "suscripción")
    items = [("chatgpt", "ChatGPT"), ("claude", "Claude"), ("grok", "Grok"), ("chinas", "IAs chinas")]
    for i, (n, lab) in enumerate(items):
        cx = 105 + (i % 2) * 170; cy = 262 + (i // 2) * 140
        if n == "chinas":
            b = Image.new("RGBA", (96, 96), (0, 0, 0, 0)); ImageDraw.Draw(b).ellipse((0, 0, 95, 95), fill=(255, 255, 255, 22), outline=(255, 255, 255, 70), width=2)
            ImageDraw.Draw(b).text((48, 48), "+", font=F(52, 500), fill=WHITE, anchor="mm")
        else: b = logo(n, 96)
        kk = k - beats[i]
        pop_in(im, b, cx, cy, kk)
        if kk > 2: d.text((cx, cy + 66), lab, font=F(22, 600), fill=WHITE, anchor="mm")
    if k > beats[-1] + 6: pop_in(im, ytbutton("Quiero mi AllPass"), CW / 2, 544, k - beats[-1] - 6)
    return im

# scene 2: one subscription instead of many
def scene_barata(k, beats):
    im = panel(); d = ImageDraw.Draw(im)
    center_text(d, 62, "Sin AllPass", F(26, 500), MUTED)
    rows = [("chatgpt", "ChatGPT"), ("claude", "Claude"), ("grok", "Grok")]
    for i, (n, lab) in enumerate(rows):
        y = 112 + i * 78; kk = k - beats[min(i, len(beats) - 1)] if i else k
        if kk <= 0: continue
        a = min(1, kk / 4); row = Image.new("RGBA", (CW - 60, 64), (0, 0, 0, 0)); dr = ImageDraw.Draw(row)
        dr.rounded_rectangle((0, 0, CW - 61, 63), 18, fill=(255, 255, 255, 14), outline=(255, 255, 255, 34))
        row.alpha_composite(logo(n, 44), (12, 10)); dr.text((70, 32), lab, font=F(24, 600), fill=WHITE, anchor="lm")
        dr.text((CW - 80, 32), "1 suscripción", font=F(19, 500), fill=(240, 120, 110), anchor="rm")
        if a < 1: row.putalpha(row.getchannel("A").point(lambda v: int(v * a)))
        im.alpha_composite(row, (30, y))
    kk = k - beats[-1] - 4
    if kk > 0:
        d.line((60, 368, CW - 60, 368), fill=(255, 255, 255, 40), width=2)
        center_text(d, 400, "Con AllPass", F(26, 700))
        g = grad_text("1 suscripción", F(44, 800)); pop_in(im, g, CW / 2, 456, kk)
        im.alpha_composite(logo_stack(["gemini", "claude", "chatgpt", "grok"], 50, 32), (int(CW / 2 - 74), 506)) if kk > 5 else None
    return im

# scene 3: ask any model, let one question the other's answer
def scene_compara(k, beats):
    im = panel(); d = ImageDraw.Draw(im)
    title2(im, 56, "Compara respuestas.", "Decide mejor.", size=32)
    def bubble(y, n, name, lines, col, kk):
        if kk <= 0: return
        h = 76 + 28 * (len(lines) - 1); b = Image.new("RGBA", (CW - 50, h), (0, 0, 0, 0)); db = ImageDraw.Draw(b)
        db.rounded_rectangle((0, 0, CW - 51, h - 1), 20, fill=(255, 255, 255, 16), outline=col + (150,), width=2)
        b.alpha_composite(logo(n, 34), (14, 12)); db.text((58, 29), name, font=F(21, 700), fill=WHITE, anchor="lm")
        for j, l in enumerate(lines): db.text((18, 62 + j * 28), l, font=F(19, 400), fill=(205, 210, 222), anchor="lm")
        a = min(1, kk / 4); yy = y + (1 - ease_out_cubic(kk / 8)) * 20
        if a < 1: b.putalpha(b.getchannel("A").point(lambda v: int(v * a)))
        im.alpha_composite(b, (25, int(yy)))
    bubble(130, "chatgpt", "ChatGPT", ["La mejor opción es la A,", "por costo y rapidez."], (90, 160, 255), k - beats[0])
    if k - beats[1] > 0:
        c = chip("Claude cuestiona", F(19, 600), dot=VIOLET); im.alpha_composite(c, (int((CW - c.width) / 2), 292))
    bubble(342, "claude", "Claude", ["Revisé la respuesta de", "ChatGPT: la B escala mejor", "a largo plazo."], VIOLET, k - beats[1] - 3)
    return im

# scene 4: your own saved agent, called into the chat
def scene_agente(k, beats):
    im = panel(); d = ImageDraw.Draw(im)
    title2(im, 56, "Crea tu propio", "agente", size=36)
    kk = k - beats[0]
    if kk > 0:
        cd = Image.new("RGBA", (CW - 60, 150), (0, 0, 0, 0)); dc = ImageDraw.Draw(cd)
        dc.rounded_rectangle((0, 0, CW - 61, 149), 22, fill=(255, 255, 255, 16), outline=(255, 255, 255, 40))
        av = grad(64, 64); m = Image.new("L", (64, 64), 0); ImageDraw.Draw(m).ellipse((0, 0, 63, 63), fill=255); av.putalpha(m); cd.alpha_composite(av, (18, 20))
        ImageDraw.Draw(cd).text((50, 52), "✦", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30), fill=WHITE, anchor="mm")
        dc.text((96, 38), "Mi agente", font=F(25, 700), fill=WHITE, anchor="lm"); dc.text((96, 68), "Ventas · Responde dudas", font=F(18, 400), fill=MUTED, anchor="lm")
        if kk > 10:
            g = chip("Guardado", F(18, 600)); cd.alpha_composite(g, (18, 100))
        cd = cd if kk >= 6 else cd.resize((cd.width, cd.height))
        pop_in(im, cd, CW / 2, 220, kk)
    kk = k - beats[1]
    if kk > 0:
        d.text((CW / 2, 330), "En la conversación", font=F(22, 500), fill=MUTED, anchor="mm")
        ib = Image.new("RGBA", (CW - 50, 70), (0, 0, 0, 0)); di = ImageDraw.Draw(ib)
        di.rounded_rectangle((0, 0, CW - 51, 69), 35, fill=(255, 255, 255, 20), outline=(120, 140, 255, 160), width=2)
        txt = "@Mi agente ayúdame"; n = min(len(txt), int(kk * 1.4))
        f = F(22, 500); x = 26
        tag = txt[:min(n, 10)]; rest = txt[10:n] if n > 10 else ""
        di.text((x, 35), tag, font=f, fill=(120, 170, 255), anchor="lm"); di.text((x + f.getlength(tag), 35), rest, font=f, fill=WHITE, anchor="lm")
        sb = grad(46, 46); ms = Image.new("L", (46, 46), 0); ImageDraw.Draw(ms).ellipse((0, 0, 45, 45), fill=255); sb.putalpha(ms); ib.alpha_composite(sb, (CW - 51 - 58, 12))
        di.text((CW - 51 - 35, 35), "↑", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24), fill=WHITE, anchor="mm")
        im.alpha_composite(ib, (25, 360))
    kk = k - beats[2]
    if kk > 0:
        b = Image.new("RGBA", (CW - 50, 92), (0, 0, 0, 0)); db = ImageDraw.Draw(b)
        db.rounded_rectangle((0, 0, CW - 51, 91), 20, fill=(255, 255, 255, 14), outline=(255, 255, 255, 34))
        db.text((18, 30), "Mi agente", font=F(20, 700), fill=(150, 180, 255), anchor="lm")
        db.text((18, 62), "Respóndele que el envío es hoy.", font=F(19, 400), fill=(210, 214, 226), anchor="lm")
        pop_in(im, b, CW / 2, 500, kk)
    return im

# scene 5: all of them, 10x cheaper
def scene_10x(k, beats):
    im = panel(); d = ImageDraw.Draw(im)
    title2(im, 70, "Todas las IAs en", "un único lugar", size=34)
    st = logo_stack(["gemini", "claude", "chatgpt", "grok"], 70, 48)
    pop_in(im, st, CW / 2, 235, k)
    kk = k - beats[0]
    if kk > 0:
        g = grad_text("10x", F(150, 800)); pop_in(im, glow(g, (90, 110, 255), 20, 140, 30), CW / 2, 390, kk, 8)
        if kk > 6: center_text(d, 500, "menos precio", F(34, 700))
    return im
