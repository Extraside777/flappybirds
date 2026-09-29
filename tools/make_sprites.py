#!/usr/bin/env python3
"""
Нарезка спрайтов из плоских картинок в assets/images -> assets/sprites.

Запуск (из корня проекта):
    pip install pillow numpy scipy
    python tools/make_sprites.py

Что делает:
  * восстанавливает чистое небо (градиент) без облаков/заголовка/кнопок
  * вырезает каждое облако отдельным спрайтом
  * вырезает заголовок (две строки отдельно, чтобы они прыгали)
  * вырезает кнопки PLAY / SHOP / MENU и рисует кадры блика (спрайт-листы)
  * отделяет шестерёнку от кнопки настроек и рисует кадры вращения
  * разбирает пейзаж на 3 слоя (город, кусты, земля) для параллакса,
    каждый слой делает бесшовным по горизонтали (зеркальный тайл)
  * пишет assets/sprites/manifest.json -- его читает игра

Игре нужен только pygame; этот скрипт нужен, только если вы меняете исходные
картинки и хотите пересобрать спрайты.
"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_BG = os.path.join(ROOT, "assets", "images", "menu_bg_clean.png")
SRC_MENU_BTN = os.path.join(ROOT, "assets", "images", "return_to_menu.png")
OUT = os.path.join(ROOT, "assets", "sprites")

GROUND_Y = 624          # с этой строки начинается земля в исходной картинке
FILL_PERIOD = 10       # период повтора при достройке закрытой кустами части города
SKY_TOL = 9             # насколько пиксель может отличаться от неба, чтобы считаться небом

manifest = {}


# --------------------------------------------------------------------------
# утилиты
# --------------------------------------------------------------------------
def save(name, arr, sub=""):
    folder = os.path.join(OUT, sub)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    Image.fromarray(np.ascontiguousarray(arr.astype(np.uint8))).save(path, optimize=True)
    return os.path.join(sub, name).replace("\\", "/") if sub else name


def fit_sky(im):
    """Градиент неба по строкам (H,3): подгоняем параболу по «чисто небесным» пикселям."""
    h = im.shape[0]
    lo, hi = np.array([0, 150, 220]), np.array([75, 215, 255])
    m = np.all((im >= lo) & (im <= hi), axis=2)
    m[560:] = False
    yy, xx = np.nonzero(m)
    ys = np.arange(h)
    sky = np.zeros((h, 3))
    for c in range(3):
        co = np.polyfit(yy, im[yy, xx, c], 2)
        for _ in range(3):  # выкидываем выбросы и подгоняем ещё раз
            keep = np.abs(im[yy, xx, c] - np.polyval(co, yy)) < 6
            co = np.polyfit(yy[keep], im[yy[keep], xx[keep], c], 2)
        sky[:, c] = np.polyval(co, ys)
    return np.clip(sky, 0, 255)


def sky_distance(im, sky):
    return np.abs(im - sky[:, None, :]).max(axis=2)


SHADOW_COLOR = np.array([0.0, 60.0, 200.0])   # цвет мягкой тени на фоне неба


def cut_from_sky(rgb, sky_rows):
    """
    Превращает кусок картинки на фоне неба в RGBA:
      небо -> прозрачное, мягкая синяя тень -> полупрозрачная тёмно-синяя, остальное -> как есть.
    Кусок должен быть с запасом неба по краям (тень ищется только «снаружи» спрайта).
    """
    sky3 = sky_rows[:, None, :]
    d = np.abs(rgb - sky3).max(axis=2)
    skylike = d < SKY_TOL

    # тень = небо, смешанное с тёмно-синим: p = sky + a * (S - sky)
    vec = SHADOW_COLOR[None, None, :] - sky3
    a = ((rgb - sky3) * vec).sum(axis=2) / (vec ** 2).sum(axis=2)
    recon = sky3 + a[..., None] * vec
    resid = np.abs(rgb - recon).max(axis=2)
    shadow = (~skylike) & (a > 0.04) & (a < 0.95) & (resid < 30) & (rgb[..., 2] > 150)

    # тенью считаем только то, что достаёт до края куска через небо/тень (не внутренности спрайта)
    cand = skylike | shadow
    lab_c, _ = ndi.label(cand)
    edge = np.unique(np.concatenate([lab_c[0], lab_c[-1], lab_c[:, 0], lab_c[:, -1]]))
    shadow &= np.isin(lab_c, edge[edge > 0])

    out = np.zeros(rgb.shape[:2] + (4,), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[..., 3] = 255
    out[skylike] = 0
    out[shadow, :3] = SHADOW_COLOR.astype(np.uint8)
    out[shadow, 3] = np.clip(a[shadow] * 255, 0, 255).astype(np.uint8)
    return out


def trim(rgba, thr=0):
    """Обрезает прозрачные поля, возвращает (спрайт, x0, y0)."""
    ys, xs = np.nonzero(rgba[..., 3] > thr)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return rgba[y0:y1, x0:x1], int(x0), int(y0)


def shine_frames(rgba, n=14, band=13, strength=0.62, slope=0.55):
    """Кадры «блика», пробегающего по кнопке по диагонали. Первый и последний кадры = оригинал."""
    h, w = rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    diag = xx + slope * yy
    span = w + slope * h + 2 * band
    solid = rgba[..., 3] == 255
    frames = []
    for i in range(n):
        centre = -band + span * i / (n - 1)
        a = np.clip(1 - np.abs(diag - centre) / band, 0, 1) ** 1.4 * strength
        a = a * solid
        f = rgba.copy()
        f[..., :3] = np.clip(f[..., :3] + (255 - f[..., :3]) * a[..., None], 0, 255)
        frames.append(f)
    return frames


def sheet(frames):
    return np.concatenate(frames, axis=1)


def bleed_colors(rgba):
    """Закрашивает цвет прозрачных пикселей ближайшим непрозрачным (чтобы не было тёмной каймы при повороте)."""
    a = rgba[..., 3] > 0
    idx = ndi.distance_transform_edt(~a, return_distances=False, return_indices=True)
    out = rgba.copy()
    out[..., :3] = rgba[idx[0], idx[1], :3]
    return out


# --------------------------------------------------------------------------
# загрузка
# --------------------------------------------------------------------------
im_u8 = np.array(Image.open(SRC_BG).convert("RGB"))
im = im_u8.astype(float)
H, W, _ = im.shape
sky = fit_sky(im)
dist = sky_distance(im, sky)
nonsky = dist >= SKY_TOL

# --------------------------------------------------------------------------
# 1. небо
# --------------------------------------------------------------------------
sky_img = np.repeat(sky[:, None, :], W, axis=1)
manifest["sky"] = {"file": save("bg_sky.png", sky_img)}

# --------------------------------------------------------------------------
# 2. компоненты верхней части: облака, заголовок, кнопки, шестерёнка
# --------------------------------------------------------------------------
top = nonsky.copy()
top[480:] = False
lab, n = ndi.label(top, structure=np.ones((3, 3)))
comps = []
for i, sl in enumerate(ndi.find_objects(lab), 1):
    area = int((lab[sl] == i).sum())
    if area > 150:
        comps.append(dict(id=i, x0=sl[1].start, x1=sl[1].stop, y0=sl[0].start, y1=sl[0].stop, area=area))


def find_comp(x0, y0):
    for c in comps:
        if abs(c["x0"] - x0) <= 3 and abs(c["y0"] - y0) <= 3:
            return c
    raise RuntimeError(f"компонент около ({x0},{y0}) не найден")


# --- облака (все, кроме заголовка, кнопок и шестерёнки)
non_cloud = [(331, 12), (77, 166), (77, 359)]   # шестерёнка, заголовок, PLAY
clouds = []
for c in comps:
    if any(abs(c["x0"] - x) <= 3 and abs(c["y0"] - y) <= 3 for x, y in non_cloud):
        continue
    if c["y0"] > 430 and c["area"] > 5000:       # SHOP (обрезан по y=480)
        continue
    clouds.append(c)
clouds.sort(key=lambda c: (c["y0"], c["x0"]))

manifest["clouds"] = []
for idx, c in enumerate(clouds, 1):
    x0, x1, y0, y1 = c["x0"], c["x1"], c["y0"], c["y1"]
    m = ndi.binary_fill_holes(lab[y0:y1, x0:x1] == c["id"])
    piece = np.dstack([im_u8[y0:y1, x0:x1], (m * 255).astype(np.uint8)])
    piece[~m, :3] = 0
    x_pos = x0
    # облака, обрезанные краем картинки, достраиваем зеркальной половиной
    if x1 >= W - 1:
        piece = np.concatenate([piece, piece[:, ::-1]], axis=1)
    elif x0 <= 0:
        piece = np.concatenate([piece[:, ::-1], piece], axis=1)
        x_pos = x0 - (x1 - x0)
    w = piece.shape[1]
    name = save(f"cloud_{idx}.png", piece, "clouds")
    # крупные облака ближе -> быстрее (px/сек)
    manifest["clouds"].append({"file": name, "x": int(x_pos), "y": int(y0), "w": int(w),
                               "h": int(y1 - y0), "speed": round(5 + w / 14, 1)})

# --------------------------------------------------------------------------
# 3. заголовок: две строки отдельными спрайтами
# --------------------------------------------------------------------------
tc = find_comp(77, 166)
tm = ndi.binary_dilation(lab == tc["id"], iterations=2)
px0, py0, px1, py1 = tc["x0"] - 6, tc["y0"] - 6, tc["x1"] + 6, tc["y1"] + 6
title = cut_from_sky(im[py0:py1, px0:px1], sky[py0:py1])
title[~tm[py0:py1, px0:px1]] = 0
# делим на две строки: каждый пиксель (включая тень) принадлежит той строке,
# к чьим сплошным буквам он ближе
solid = title[..., 3] > 200
comp_lab, comp_n = ndi.label(solid, structure=np.ones((3, 3)))
mid_y = title.shape[0] / 2
comp_line = np.zeros(comp_n + 1, int)
for cid in range(1, comp_n + 1):
    comp_line[cid] = 1 if ndi.center_of_mass(comp_lab == cid)[0] < mid_y else 2
near = ndi.distance_transform_edt(~solid, return_distances=False, return_indices=True)
owner = comp_line[comp_lab[near[0], near[1]]]
lines = []
for j in (1, 2):
    part = title.copy()
    part[owner != j] = 0
    spr, ox, oy = trim(part)
    name = save(f"title_line{j}.png", spr, "title")
    lines.append({"file": name, "x": px0 + ox, "y": py0 + oy, "w": spr.shape[1], "h": spr.shape[0]})
manifest["title"] = lines

# --------------------------------------------------------------------------
# 4. кнопки PLAY / SHOP / MENU (+ блик)
# --------------------------------------------------------------------------
manifest["buttons"] = {}


def add_button(key, rgba, x, y, fps=24, pause=3.2):
    frames = shine_frames(rgba)
    name = save(f"btn_{key}_sheet.png", sheet(frames), "buttons")
    manifest["buttons"][key] = {"file": name, "frames": len(frames), "fw": rgba.shape[1],
                                "fh": rgba.shape[0], "x": int(x), "y": int(y),
                                "fps": fps, "pause": pause}


for key, (bx0, by0, bx1, by1), pause in [("play", (70, 352, 330, 439), 3.2),
                                          ("shop", (70, 439, 330, 512), 3.2)]:
    cut = cut_from_sky(im[by0:by1, bx0:bx1], sky[by0:by1])
    spr, ox, oy = trim(cut)
    add_button(key, spr, bx0 + ox, by0 + oy, pause=pause)

# кнопка MENU (экран Game Over) -- уже с прозрачностью
menu_btn = np.array(Image.open(SRC_MENU_BTN).convert("RGBA"))
spr, ox, oy = trim(menu_btn)
add_button("menu", menu_btn, 0, 0, pause=2.4)
manifest["buttons"]["menu"]["trim"] = [ox, oy]

# --------------------------------------------------------------------------
# 5. настройки: панель + вращающаяся шестерёнка
# --------------------------------------------------------------------------
gc = find_comp(331, 12)
gm = ndi.binary_dilation(lab == gc["id"], iterations=2)
gx0, gy0, gx1, gy1 = gc["x0"] - 6, gc["y0"] - 6, gc["x1"] + 6, gc["y1"] + 8
panel_full = cut_from_sky(im[gy0:gy1, gx0:gx1], sky[gy0:gy1])
panel_full[~gm[gy0:gy1, gx0:gx1]] = 0

# шестерёнка = тёмные/серые пиксели внутри круга около центра панели
cy, cx = 38.5, 360.0
yy, xx = np.mgrid[gy0:gy1, gx0:gx1]
inside = (xx - cx) ** 2 + (yy - cy) ** 2 <= 21.5 ** 2
v = im_u8[gy0:gy1, gx0:gx1].max(axis=2) / 255.0
gear_m = inside & (v < 0.72) & (panel_full[..., 3] == 255)
gear_m = ndi.binary_closing(gear_m, iterations=1)
gear_m = ndi.binary_dilation(gear_m, iterations=1) & inside

# панель без шестерёнки: «дыру» закрашиваем кремовым цветом панели.
# Берём только кремовые пиксели вне шестерёнки, считаем цвет по строкам и интерполируем по вертикали
base = panel_full.copy()
hole = ndi.binary_dilation(gear_m, iterations=2)
ph, pw = hole.shape
rgb_p = base[..., :3].astype(int)
cream = (rgb_p[..., 0] > 240) & (rgb_p[..., 1] > 205) & (rgb_p[..., 2] > 165) & (base[..., 3] == 255) \
    & ~ndi.binary_dilation(hole, iterations=2)
row_ok, row_col = [], []
for yv in range(ph):
    if cream[yv].sum() >= 4:
        row_ok.append(yv)
        row_col.append(np.median(rgb_p[yv][cream[yv]], axis=0))
row_col = np.array(row_col)
for yv in np.nonzero(hole.any(axis=1))[0]:
    col = [np.interp(yv, row_ok, row_col[:, ch]) for ch in range(3)]
    base[yv][hole[yv], :3] = np.round(col).astype(np.uint8)
manifest["settings"] = {
    "base": save("btn_settings_base.png", base, "buttons"),
    "x": int(gx0), "y": int(gy0), "w": int(base.shape[1]), "h": int(base.shape[0]),
}

# спрайт-лист вращения: 72 кадра по 5 градусов
ys_, xs_ = np.nonzero(gear_m)
r = int(np.ceil(np.hypot(xs_ - (cx - gx0), ys_ - (cy - gy0)).max())) + 2
size = 2 * r + 1
gear = np.zeros((size, size, 4), np.uint8)
oy_, ox_ = int(round(cy - gy0)) - r, int(round(cx - gx0)) - r
for yv, xv in zip(ys_, xs_):
    gear[yv - oy_, xv - ox_, :3] = panel_full[yv, xv, :3]
    gear[yv - oy_, xv - ox_, 3] = 255
# «дырка» шестерёнки (центр) остаётся прозрачной -- через неё видна панель
gear = bleed_colors(gear)
gear_big = Image.fromarray(gear).resize((size * 4, size * 4), Image.NEAREST)
gframes = []
for k in range(72):
    rot = gear_big.rotate(k * 5, resample=Image.BICUBIC, center=(size * 2, size * 2))
    small = rot.resize((size, size), Image.LANCZOS)
    gframes.append(np.array(small))
manifest["settings"]["gear"] = {
    "file": save("gear_sheet.png", sheet(gframes), "buttons"),
    "frames": 72, "fw": size, "fh": size, "fps": 9,
    # где рисовать кадр относительно левого верхнего угла панели
    "ox": int(ox_), "oy": int(oy_),
}

# --------------------------------------------------------------------------
# 6. пейзаж: город (дальний), кусты (средний), земля (ближний)
# --------------------------------------------------------------------------
f = im / 255.0
r_, g_, b_ = f[..., 0], f[..., 1], f[..., 2]
sat = (f.max(2) - f.min(2)) / np.maximum(f.max(2), 1e-6)
bush = ((g_ > r_ + 0.12) & (g_ > b_ + 0.12) & (sat > 0.45)) | ((r_ < 0.08) & (g_ > b_ + 0.05) & (g_ > 0.3))
bush[:480] = False
bush[GROUND_Y:] = False
# морфология по краю картинки «съедает» маску -- поэтому сначала достраиваем поля по краям
PAD = 6
bush = np.pad(bush, ((0, 0), (PAD, PAD)), mode="edge")
bush = ndi.binary_closing(bush, structure=np.ones((3, 3)), iterations=2)
bush = ndi.binary_fill_holes(bush)[:, PAD:-PAD]
bl, bn = ndi.label(bush)
sizes = ndi.sum(bush, bl, range(1, bn + 1))
bush = np.isin(bl, [i + 1 for i, s in enumerate(sizes) if s > 400])
first = np.where(bush.any(0), bush.argmax(0), GROUND_Y)
rowi = np.arange(H)[:, None]
bush_solid = (rowi >= first[None, :]) & (rowi < GROUND_Y)


def mirror_tile(a):
    """Делает слой бесшовным по X: картинка + её зеркальная копия."""
    return np.concatenate([a, a[:, ::-1]], axis=1)


# --- кусты
# +1 пиксель сверху: там тёмный контур кустов
bush_edge = ndi.binary_dilation(bush_solid, structure=np.array([[0, 1, 0], [0, 1, 0], [0, 0, 0]], bool))
bush_edge[GROUND_Y:] = False
b0 = int(np.nonzero(bush_edge.any(axis=1))[0].min())
bush_rgba = np.zeros((GROUND_Y - b0, W, 4), np.uint8)
sel = bush_edge[b0:GROUND_Y]
bush_rgba[..., :3][sel] = im_u8[b0:GROUND_Y][sel]
bush_rgba[..., 3][sel] = 255

# --- земля
ground_rgba = np.dstack([im_u8[GROUND_Y:], np.full((H - GROUND_Y, W), 255, np.uint8)])

# --- город/холмы: всё, что не небо и не кусты; под кустами достраиваем
far_mask = nonsky.copy()
far_mask[:470] = False
far_mask[GROUND_Y:] = False
far_mask[:515, 70:330] = False            # кнопка SHOP и её тень
hidden = ndi.binary_dilation(np.pad(bush_solid, ((0, 0), (PAD, PAD)), mode='edge'), iterations=3)[:, PAD:-PAD]   # кайма кустов не должна попасть в дальний слой
far_mask &= ~hidden
far_mask = ndi.binary_fill_holes(far_mask) | far_mask
mint_px = im_u8[520:560][far_mask[520:560] & (im_u8[520:560].min(axis=2) > 190)]
mint = np.median(mint_px, axis=0)
far_rgba = np.zeros((GROUND_Y + 6 - 470, W, 4), np.uint8)
fm = far_mask[470:GROUND_Y]
far_rgba[:GROUND_Y - 470, :, :3][fm] = im_u8[470:GROUND_Y][fm]
far_rgba[:GROUND_Y - 470, :, 3][fm] = 255
for x in range(W):
    col = hidden[:, x] & (np.arange(H) < GROUND_Y)
    if not col.any():
        continue
    t = int(col.argmax())
    for yv in range(t, GROUND_Y + 6):
        # то, что раньше было закрыто кустами, достраиваем повтором последних строк над кустами:
        # окна и стены зданий продолжаются вниз регулярным узором, холмы -- своим цветом
        sy = t - FILL_PERIOD + ((yv - t) % FILL_PERIOD)
        if sy >= 470 and far_mask[sy, x]:
            c = im_u8[sy, x]
        else:
            c = mint.astype(np.uint8)
        far_rgba[yv - 470, x, :3] = c
        far_rgba[yv - 470, x, 3] = 255
# верхняя граница дальнего слоя
far_top = int(np.nonzero(far_rgba[..., 3].any(axis=1))[0].min())
far_rgba = far_rgba[far_top:]
far_y = 470 + far_top

manifest["layers"] = {
    "far": {"file": save("bg_far.png", mirror_tile(far_rgba), "layers"), "y": far_y, "w": W * 2,
            "h": int(far_rgba.shape[0]), "period": W * 2, "factor": 0.12},
    "bushes": {"file": save("bg_bushes.png", mirror_tile(bush_rgba), "layers"), "y": b0, "w": W * 2,
               "h": int(bush_rgba.shape[0]), "period": W * 2, "factor": 0.45},
    "ground": {"file": save("bg_ground.png", mirror_tile(ground_rgba), "layers"), "y": GROUND_Y, "w": W * 2,
               "h": int(ground_rgba.shape[0]), "period": W * 2, "factor": 1.0},
}
manifest["screen"] = {"w": int(W), "h": int(H), "ground_y": GROUND_Y}

with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=2)
print("готово ->", OUT)
