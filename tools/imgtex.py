"""QTX 텍스처 RGBA 디코드/인코드 (4bpp·8bpp: CT32 폭64 업로드 스위즐 + 팔레트, 32bpp: 선형)"""
import struct, numpy as np, swz
_ix = {}
def _idx32(h32):
    if h32 not in _ix: _ix[h32] = swz.idx32(1, 64, h32)
    return _ix[h32]
def _layout(d):
    w, h = struct.unpack_from('<2H', d, 0x180); psm = d[0x40]
    bpp = {0x13: 8, 0x14: 4, 0x00: 32}[psm]
    return w, h, bpp
SW = np.arange(256); SW = (SW & ~0x18) | ((SW & 8) << 1) | ((SW & 16) >> 1)
def decode(d):
    """-> (idx 또는 None, rgba(h,w,4 uint8, alpha 0~255), palette rgba(n,4 0~255) 또는 None)"""
    w, h, bpp = _layout(d); n = w * h * bpp // 8; px = np.frombuffer(d[0x200:0x200 + n], np.uint8)
    if bpp == 32:
        a = px.reshape(h, w, 4).astype(int).copy(); a[..., 3] = np.minimum(255, a[..., 3] * 2)
        return None, a.astype(np.uint8), None
    h32 = n // 256; ix = _idx32(h32); vm = np.zeros(max(1 << 22, ix.max() + 4), np.uint8)
    p = px.reshape(h32, 64, 4)
    for k in range(4): vm[ix + k] = p[..., k]
    if bpp == 4:
        a = swz.idx4(max(2, w // 64), w, h); b = vm[a >> 1]; idx = np.where(a & 1, b >> 4, b & 15).astype(np.uint8)
        pal = np.frombuffer(d[0x200 + n + 0x80:0x200 + n + 0x80 + 64], np.uint8).reshape(16, 4).astype(int)
    else:
        a = swz.idx8(max(2, w // 64), w, h); idx = vm[a]
        pal = np.frombuffer(d[0x200 + n + 0x80:0x200 + n + 0x80 + 1024], np.uint8).reshape(256, 4)[SW].astype(int)
    pal = pal.copy(); pal[:, 3] = np.minimum(255, pal[:, 3] * 2)
    return idx, pal[idx].astype(np.uint8), pal.astype(np.uint8)
def encode(d, idx=None, rgba=None):
    d = bytearray(d); w, h, bpp = _layout(d); n = w * h * bpp // 8
    if bpp == 32:
        a = rgba.astype(int).copy(); a[..., 3] = (a[..., 3] + 1) // 2
        d[0x200:0x200 + n] = a.astype(np.uint8).tobytes(); return bytes(d)
    px = np.frombuffer(bytes(d[0x200:0x200 + n]), np.uint8); h32 = n // 256; ix = _idx32(h32)
    vm = np.zeros(max(1 << 22, ix.max() + 4), np.uint8); p = px.reshape(h32, 64, 4)
    for k in range(4): vm[ix + k] = p[..., k]
    if bpp == 4:
        a = swz.idx4(max(2, w // 64), w, h).ravel(); v = idx.ravel().astype(np.uint8); b = a >> 1; hi = (a & 1) == 1
        vm[b[hi]] = (vm[b[hi]] & 0x0f) | (v[hi] << 4); vm[b[~hi]] = (vm[b[~hi]] & 0xf0) | v[~hi]
    else:
        a = swz.idx8(max(2, w // 64), w, h); vm[a] = idx
    d[0x200:0x200 + n] = np.stack([vm[ix + k] for k in range(4)], -1).reshape(-1).tobytes()
    return bytes(d)
def quantize(rgba, pal, mask, idx):
    """mask 영역의 rgba 를 팔레트 최근접 인덱스로"""
    out = idx.copy(); pts = rgba[mask].astype(int)
    P = pal.astype(int); wgt = np.array([1, 1, 1, 2])
    dist = (((pts[:, None, :] - P[None, :, :]) ** 2) * wgt).sum(-1)
    out[mask] = dist.argmin(1); return out
