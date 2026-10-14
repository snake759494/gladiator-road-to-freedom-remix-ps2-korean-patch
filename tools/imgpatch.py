"""텍스처 속 영어 글자를 한글로 교체한다.
지정: (x, y, w, h, 한글, 스타일)  — 상자 안 글자를 지우고(투명 'clear' / 둘레 무늬 'ring') 한글을 가운데에 그린 뒤
팔레트 텍스처는 바뀐 영역만 최근접 팔레트 색으로 다시 양자화한다."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imgtex, cv2

ROOT = 'D:/ps2/글라디에이터_로드투프리덤_리믹스/'
FONTS = {'sans': 'NanumSquareNeo-cBd.ttf', 'sansH': 'NanumSquareNeo-dEb.ttf', 'sansR': 'NanumSquareNeo-bRg.ttf',
         'serif': 'SeoulHangangB.ttf', 'serifEB': 'SeoulHangangEB.ttf', 'serifM': 'SeoulHangangM.ttf'}
_fc = {}


def font(name, size):
    k = (name, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(ROOT + FONTS[name], size)
    return _fc[k]


def fit(text, fname, w, h, maxsize, spacing=0):
    for sz in range(maxsize, 5, -1):
        f = font(fname, sz)
        bb = f.getbbox(text)
        tw = bb[2] - bb[0] + spacing * (len(text) - 1); th = bb[3] - bb[1]
        if tw <= w and th <= h: return f, bb, tw, th
    f = font(fname, 6); bb = f.getbbox(text); return f, bb, bb[2] - bb[0], bb[3] - bb[1]


def text_layer(W, H, text, st):
    """(H,W) 크기 RGBA 글자 레이어"""
    pad = st.get('pad', 1)
    f, bb, tw, th = fit(text, st.get('font', 'sans'), W - 2 * pad, H - 2 * pad, st.get('size', H), st.get('spacing', 0))
    x0 = (W - tw) // 2 - bb[0]; y0 = (H - th) // 2 - bb[1] + st.get('dy', 0)
    mask = Image.new('L', (W, H), 0); d = ImageDraw.Draw(mask)
    sp = st.get('spacing', 0)
    if sp:
        x = x0
        for ch in text:
            d.text((x, y0), ch, font=f, fill=255); b = f.getbbox(ch); x += (b[2] - b[0]) + sp + (f.getlength(ch) - (b[2] - b[0])) * 0
    else:
        d.text((x0, y0), text, font=f, fill=255)
    m = np.array(mask).astype(float) / 255
    out = np.zeros((H, W, 4), float)
    # 그림자 / 외곽선 (아래에 깔기)
    if 'shadow' in st:
        c, dx, dy = st['shadow']
        s = np.zeros_like(m); s[max(dy, 0):H + min(dy, 0), max(dx, 0):W + min(dx, 0)] = m[max(-dy, 0):H - max(dy, 0), max(-dx, 0):W - max(dx, 0)]
        out = over(out, s, c)
    if 'outline' in st:
        c, r = st['outline']
        o = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * r + 1))).astype(float) / 255
        out = over(out, o, c)
    fill = st.get('color', (255, 255, 255))
    if isinstance(fill, list):          # 세로 그라데이션 [위색, 아래색]
        ys = np.nonzero(m.max(1) > 0)[0]
        t0, t1 = (ys.min(), ys.max()) if len(ys) else (0, H - 1)
        col = np.zeros((H, W, 3))
        for y in range(H):
            a = min(1, max(0, (y - t0) / max(1, t1 - t0)))
            col[y] = np.array(fill[0]) * (1 - a) + np.array(fill[1]) * a
        out = over(out, m, col)
    else:
        out = over(out, m, fill)
    return out


def over(dst, a, color):
    color = np.asarray(color, float)
    c = color[..., :3] if color.ndim == 3 else np.broadcast_to(color[:3], dst.shape[:2] + (3,))
    ca = (color[3] / 255 if color.ndim == 1 and len(color) == 4 else 1.0)
    A = a * ca
    outa = A + dst[..., 3] * (1 - A)
    rgb = (c * A[..., None] + dst[..., :3] * (dst[..., 3] * (1 - A))[..., None]) / np.maximum(outa, 1e-6)[..., None]
    r = np.zeros_like(dst); r[..., :3] = rgb; r[..., 3] = outa; return r


def ring_fill(rgba, x, y, w, h, rng):
    H, W = rgba.shape[:2]
    pts = []
    for t in range(1, 4):
        for xx in range(max(0, x - t), min(W, x + w + t)):
            for yy in (y - t, y + h - 1 + t):
                if 0 <= yy < H: pts.append(rgba[yy, xx])
        for yy in range(max(0, y - t), min(H, y + h + t)):
            for xx in (x - t, x + w - 1 + t):
                if 0 <= xx < W: pts.append(rgba[yy, xx])
    pts = np.array(pts)
    sel = pts[rng.integers(0, len(pts), size=(h, w))]
    rgba[y:y + h, x:x + w] = sel


def apply(data, specs, seed=1):
    idx, rgba, pal = imgtex.decode(data)
    rgba = rgba.astype(float); H, W = rgba.shape[:2]
    changed = np.zeros((H, W), bool); rng = np.random.default_rng(seed)
    for (x, y, w, h, text, st) in specs:
        mode = st.get('bg', 'clear')
        if mode == 'clear': rgba[y:y + h, x:x + w] = 0
        elif mode == 'ring':
            tmp = rgba.astype(np.uint8); ring_fill(tmp, x, y, w, h, rng); rgba = tmp.astype(float)
        elif mode == 'inpaint':
            tmp = np.clip(rgba, 0, 255).astype(np.uint8)
            rgb = np.ascontiguousarray(tmp[..., :3]); L = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(int)
            med = cv2.medianBlur(L.astype(np.uint8), 9).astype(int)
            m = np.zeros(L.shape, np.uint8); sub = np.abs(L - med)[y:y + h, x:x + w] > st.get('thr', 22)
            m[y:y + h, x:x + w] = sub
            m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)
            m[:y, :] = 0; m[y + h:, :] = 0; m[:, :x] = 0; m[:, x + w:] = 0
            res = cv2.inpaint(rgb, m * 255, 5, cv2.INPAINT_TELEA)
            rgba[..., :3] = np.where(m[..., None] > 0, res, rgba[..., :3])
        elif mode == 'keep': pass
        else: rgba[y:y + h, x:x + w] = mode      # 단색
        changed[y:y + h, x:x + w] = True
        if text:
            tb = st.get('tbox', (x, y, w, h)); tx, ty, tw, th = tb
            lay = text_layer(tw, th, text, st)
            reg = rgba[ty:ty + th, tx:tx + tw] / [1, 1, 1, 255]
            a = lay[..., 3]
            outa = a + reg[..., 3] * (1 - a)
            rgb = (lay[..., :3] * a[..., None] + reg[..., :3] * (reg[..., 3] * (1 - a))[..., None]) / np.maximum(outa, 1e-6)[..., None]
            rgba[ty:ty + th, tx:tx + tw, :3] = rgb; rgba[ty:ty + th, tx:tx + tw, 3] = outa * 255
            changed[ty:ty + th, tx:tx + tw] = True
    rgba = np.clip(rgba, 0, 255).astype(np.uint8)
    if pal is None:
        return imgtex.encode(data, rgba=rgba)
    nidx = imgtex.quantize(rgba, pal, changed, idx)
    return imgtex.encode(data, idx=nidx)


def preview(data):
    idx, rgba, pal = imgtex.decode(data)
    bg = np.zeros(rgba.shape[:2] + (3,)); bg[:] = [30, 50, 80]; a = rgba[..., 3:4] / 255
    return Image.fromarray((rgba[..., :3] * a + bg * (1 - a)).astype(np.uint8))
