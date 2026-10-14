"""글라디에이터 로드 투 프리덤 리믹스 한글패치 빌드
- 텍스트: GG.DAT / DATA.RBB 안의 CSB(고정폭 셀) · ARY(컴파일 테이블, 가변 길이) · ELF 문자열
- 작은 글꼴 GGFONT0/1.QTX: 매핑한 한자 칸에 한글 / 큰 글꼴 LARGE.FNT+LARGE0.QTX: 한자 칸 재활용 + 레코드 재지정
- 크기가 바뀐 GG.DAT · DATA.RBB 는 ISO 끝에 다시 쓰고 ISO9660/UDF 레코드 갱신"""
import os, shutil, struct, numpy as np
from PIL import Image, ImageDraw, ImageFont
import gg, csb, textcols, kotext, font, swz, ary, isoio, udf, names
import rbb as rbbmod

ROOT = 'D:/ps2/글라디에이터_로드투프리덤_리믹스/'
SRC = ROOT + 'Gladiator - Road to Freedom - Remix (Japan).iso'
DST = ROOT + 'Gladiator - Road to Freedom - Remix (Korean).iso'
TTF = ROOT + 'NanumSquareNeo-bRg.ttf'
SEC = 2048


def s(b): return b.split(b'\0')[0].decode('cp932')
def isjp(t): return any(ord(c) >= 0x3000 for c in t)


# ---------- 텍스트 ----------
EN = textcols.load_en()


def patch_csb(data, name, tr, cmap, stat):
    cs = textcols.cols_for(name)
    base = name.replace('DATA/', '').rsplit('.', 1)[0]
    en = textcols.EN_CSB.get(base, set())
    if not cs and not en: return None
    d = bytearray(data); t = csb.parse(data); ch = 0
    for ri, row in enumerate(t['cells']):
        for c, cell in enumerate(row):
            cn = s(t['cn'][c])
            if cn in en and s(cell) in EN:
                e = kotext.encode(EN[s(cell)], cmap)
                assert len(e) < t['cw'], (name, EN[s(cell)])
                p = t['doff'] + (ri * t['cols'] + c) * t['cw']
                d[p:p + t['cw']] = e + bytes(t['cw'] - len(e)); ch += 1; continue
            ok = (cs == 'ALL' and not cn.startswith('英語')) or (cs != 'ALL' and cn in cs)
            if not (ok and csb.jp(cell)): continue
            src = s(cell)
            if src in textcols.KEEP: continue
            if src not in tr: stat['miss'].add(src); continue
            e = kotext.encode(tr[src], cmap)
            assert len(e) < t['cw'], (name, tr[src])
            p = t['doff'] + (ri * t['cols'] + c) * t['cw']
            d[p:p + t['cw']] = e + bytes(t['cw'] - len(e)); ch += 1
    stat['cells'] += ch
    return bytes(d) if ch else None


def patch_ary(data, name, tr, cmap, stat):
    base = name.replace('DATA/', '').rsplit('.', 1)[0]
    if base not in textcols.ARY_OK and base not in textcols.EN_ARY: return None
    a = ary.parse(data); ch = 0; vals = []
    for t, v in a['vals']:
        if t == 3:
            src = v.decode('cp932')
            if base in textcols.EN_ARY and src in EN:
                vals.append((t, kotext.encode(EN[src], cmap))); ch += 1; continue
            if base not in textcols.ARY_OK:
                vals.append((t, v)); continue
            if isjp(src) and src in tr and src not in textcols.KEEP:
                v = kotext.encode(tr[src], cmap); ch += 1
        vals.append((t, v))
    if not ch: return None
    a['vals'] = vals; out = ary.build(a)
    out += b'\xff' * (-len(out) % 16)
    stat['ary'] += ch
    return out


# ---------- 글꼴 ----------
def tex_edit(q, w, h, edits, cw, chh):
    d = bytearray(q); n = w * h // 2
    px = np.frombuffer(bytes(d[0x200:0x200 + n]), np.uint8)
    h32 = n // 256; ix = swz.idx32(1, 64, h32)
    vm = np.zeros(1 << 23, np.uint8); p = px.reshape(h32, 64, 4)
    for k in range(4): vm[ix + k] = p[..., k]
    a = swz.idx4(w // 64, w, h)
    for x, y, cell in edits:
        aa = a[y:y + chh, x:x + cw].ravel(); v = cell.ravel().astype(np.uint8)
        b = aa >> 1; hi = (aa & 1) == 1
        vm[b[hi]] = (vm[b[hi]] & 0x0f) | (v[hi] << 4)
        vm[b[~hi]] = (vm[b[~hi]] & 0xf0) | v[~hi]
    d[0x200:0x200 + n] = np.stack([vm[ix + k] for k in range(4)], -1).reshape(-1).tobytes()
    return bytes(d)


def render(ch, ft, box):
    g = Image.new('L', (box, box), 0); dr = ImageDraw.Draw(g)
    bb = dr.textbbox((0, 0), ch, font=ft); w = bb[2] - bb[0]; h = bb[3] - bb[1]
    dr.text(((box - 1 - w) // 2 - bb[0], (box - 1 - h) // 2 - bb[1]), ch, font=ft, fill=255)
    return np.array(g)


def small_glyph(ch, ft):
    a = render(ch, ft, 16) > 110
    cell = np.zeros((17, 17), np.uint8); sh = np.zeros((17, 17), bool); sh[1:, 1:] = a
    cell[sh] = 1; cell[:16, :16][a] = 15
    return cell


LPAL = [17, 41, 68, 93, 120, 151, 192, 229, 242, 248, 254]   # 큰 글꼴 팔레트 5~15 밝기


def large_glyph(ch, ft):
    g = render(ch, ft, 22).astype(int)
    cell = np.zeros((23, 23), np.uint8); body = g > 40
    idx = np.zeros_like(g)
    for k, v in enumerate(LPAL): idx[g >= v - 8] = 5 + k
    cell[:22, :22][body] = idx[body]
    B = np.zeros((23, 23), bool); B[:22, :22] = body
    sh = np.zeros((23, 23), bool); sh[1:, 1:] = B[:-1, :-1]; sh[1:, :] |= B[:-1, :]; sh &= ~B
    cell[sh] = 2
    M = B | sh; dil = M.copy()
    dil[1:, :] |= M[:-1, :]; dil[:-1, :] |= M[1:, :]; dil[:, 1:] |= M[:, :-1]; dil[:, :-1] |= M[:, 1:]
    cell[dil & ~M] = 1
    return cell


# ---------- 아카이브 (GG.DAT / .dat 공통: u32 개수 + u32 오프셋(16B 단위), 0번 = 이름표) ----------
def arc_entries(d):
    n = struct.unpack_from('<I', d, 0)[0]
    return n, list(struct.unpack_from('<%dI' % n, d, 4))


def arc_names(d, o, size):
    n = len(o); end = size // 16
    valid = sorted(set(x for x in o if x != 0xffffffff)) + [end]

    def ent(i):
        x = o[i]; nx = min(v for v in valid if v > x); return x * 16, (nx - x) * 16
    no, ns = ent(0)
    names = [d[no + k:no + k + 32].split(b'\0')[0].decode('cp932', 'replace') for k in range(0, ns, 32)]
    return [(k + 1, nm) + ent(k + 1) for k, nm in enumerate(names) if nm and k + 1 < n and o[k + 1] != 0xffffffff]


def arc_rebuild(d, newfiles):
    """원본 배치 순서를 유지하며 다시 쌓고 오프셋 표를 고친다. newfiles: {index: bytes}"""
    n, o = arc_entries(d); end = len(d) // 16
    valid = sorted(set(x for x in o if x != 0xffffffff and x < end))
    bounds = valid + [end]
    out = bytearray(d[:valid[0] * 16]); newpos = {}
    for k, x in enumerate(valid):
        blob = None
        for i, v in enumerate(o):
            if v == x and i in newfiles: blob = newfiles[i]
        if blob is None: blob = d[x * 16:bounds[k + 1] * 16]
        else: blob = blob + b'\xff' * (-len(blob) % 16)
        newpos[x] = len(out) // 16; out += blob
    newend = len(out) // 16
    no = [x if x == 0xffffffff else newpos.get(x, newend if x == end else x) for x in o]
    struct.pack_into('<%dI' % n, out, 4, *no)
    return bytes(out)


def main():
    tr = kotext.load_csb_tr(); el = kotext.load_elf_tr()
    src = open(SRC, 'rb'); T = isoio.walk(src)

    def readf(p):
        pos, l, sz = T[p]; src.seek(l * SEC); return src.read(sz)
    GG = readf('/DATA/GG.DAT'); RB = readf('/DATA/STREAM/DATA.RBB')
    ELF = bytearray(readf('/SLPM_661.32')); IDX = readf('/DATA/RBBINDEX.TXT')
    n, o = arc_entries(GG); G = arc_names(GG, o, len(GG))
    byname = {nm: (i, off, sz) for i, nm, off, sz in G}
    getg = lambda nm: GG[byname[nm][1]:byname[nm][1] + byname[nm][2]]
    P = font.parse_fnt(getg('DATA/GGFONT.FNT')); LF = getg('DATA/LARGE.FNT'); LP = font.parse_fnt(LF)
    cmap = kotext.build_map(list(tr.values()) + [k for a, k in el] + [names.chars()] + list(EN.values()), P, lambda u: (u >> 8) in LP)
    stat = {'cells': 0, 'ary': 0, 'miss': set()}

    # 글꼴 준비
    sft = ImageFont.truetype(TTF, 15); ed = {0: [], 1: []}
    for c, (sj, u) in cmap.items():
        r = P[u >> 8][1][u & 0xff]
        ed[(r >> 56) & 0xff].append((r & 0xfff, (r >> 32) & 0xfff, small_glyph(c, sft)))
    cells = sorted({((r >> 32) & 0xfff, r & 0xfff) for pg, (oo, recs) in LP.items() if 0x4e <= pg <= 0x9f for r in recs if r})
    assert len(cells) >= len(cmap)
    tmpl = next(r for r in LP[0x4e][1] if r)
    lfd = bytearray(LF); lft = ImageFont.truetype(TTF, 20); led = []
    for k, (c, (sj, u)) in enumerate(sorted(cmap.items())):
        y, x = cells[k]
        rec = (tmpl & ~0x00000fff00000fff) | (y << 32) | x
        oo = LP[u >> 8][0] + 2 + 8 * (u & 0xff); lfd[oo:oo + 8] = struct.pack('<Q', rec)
        led.append((x, y, large_glyph(c, lft)))
    LFn = bytes(lfd)

    def patch_file(nm, d):
        if nm == 'DATA/NAMEENTRY_WORD.CSB': return names.patch_word_csb(d, cmap)
        if nm == 'DATA/NAMEENTRY_WORD.ARY': return names.patch_word_ary(d, cmap)
        if nm == 'DATA/NAMEENTRY_DEFAULT.CSB': return names.patch_default_csb(d)
        if nm == 'DATA/NAMEENTRY_DEFAULT.ARY': return names.patch_default_ary(d)
        if nm.endswith('.CSB'): return patch_csb(d, nm, tr, cmap, stat)
        if nm.endswith('.ARY'): return patch_ary(d, nm, tr, cmap, stat)
        if nm == 'DATA/GGFONT0.QTX': return tex_edit(d, 1024, 1024, ed[0], 17, 17)
        if nm == 'DATA/GGFONT1.QTX': return tex_edit(d, 1024, 512, ed[1], 17, 17)
        if nm == 'DATA/LARGE.FNT': return LFn + d[len(LF):]
        if nm == 'DATA/LARGE0.QTX': return tex_edit(d, 1024, 1024, led, 23, 23)
        return None

    # ---- DATA.RBB ----
    nd = struct.unpack_from('<I', RB, 0x84)[0] // 8
    ridx = [struct.unpack_from('<2I', RB, 0x88 + i * 8) for i in range(nd)]
    datas = []; changed = {}; resized = {}
    for di, (off, size) in enumerate(ridx):
        blob = RB[rbbmod.BASE + off:rbbmod.BASE + off + size]
        cnt = struct.unpack_from('<I', blob, 0)[0]; newf = {}
        if 0 < cnt < 5000:
            oo = list(struct.unpack_from('<%dI' % cnt, blob, 4))
            for i, nm, fo, fs in arc_names(blob, oo, size):
                r = patch_file(nm, blob[fo:fo + fs])
                if r is not None and r != blob[fo:fo + fs]: newf[i] = r
        if newf:
            nb = arc_rebuild(blob, newf); changed[di] = 1
            if len(nb) != len(blob): resized[di] = len(nb)
            blob = nb
        datas.append(blob)
    hdr = bytearray(RB[:rbbmod.BASE]); pos = 0
    for di, b in enumerate(datas):
        struct.pack_into('<2I', hdr, 0x88 + di * 8, pos, len(b)); pos += len(b)
    RBn = bytes(hdr) + b''.join(datas)
    print('RBB: .dat 변경', len(changed), '크기 변경', len(resized), len(RB), '->', len(RBn))
    # RBBINDEX.TXT (크기 갱신)
    lines = IDX.decode('cp932').split('\n')
    for k, l in enumerate(lines):
        p = l.split('\t')
        if len(p) >= 4 and p[3].strip().isdigit() and int(p[3]) in resized:
            p[1] = str(resized[int(p[3])]); lines[k] = '\t'.join(p)
    IDXn = '\n'.join(lines).encode('cp932')

    # ---- GG.DAT ----
    newg = {}
    for i, nm, off, sz in G:
        d = GG[off:off + sz]
        if nm == 'DATA/RBBINDEX.TXT':
            r = IDXn + bytes(sz - len(IDX)) if len(IDXn) == len(IDX) else IDXn + b'\0' * (sz - len(IDX))
            r = IDXn + d[len(IDX):] if len(IDXn) <= len(IDX) else IDXn
        else:
            r = patch_file(nm, d)
        if r is not None and r != d: newg[i] = r
    GGn = arc_rebuild(GG, newg)
    print('GG.DAT: 변경', len(newg), len(GG), '->', len(GGn))

    # ---- ELF ----
    for a, ko in el:
        room = kotext.elf_room(bytes(ELF), a); e = kotext.encode(ko, cmap)
        assert len(e) + 1 <= room, (hex(a), ko)
        ELF[a:a + room] = e + bytes(room - len(e))
    print('CSB 셀', stat['cells'], 'ARY 문자열', stat['ary'], '누락', len(stat['miss']), '글자', len(cmap), 'ELF', len(el))

    # ---- ISO ----
    shutil.copyfile(SRC, DST)
    with open(DST, 'r+b') as f:
        T2 = isoio.walk(f); u = udf.UDF(f)
        end = os.path.getsize(SRC) // SEC - 1      # 마지막 섹터(UDF 앵커) 자리부터 덧붙임
        for path, data in [('/SLPM_661.32', bytes(ELF)), ('/DATA/RBBINDEX.TXT', IDXn),
                           ('/DATA/GG.DAT', GGn), ('/DATA/STREAM/DATA.RBB', RBn)]:
            pos, l, sz = T2[path]; room = (sz + SEC - 1) // SEC * SEC
            if len(data) <= room: lba = l
            else: lba = end; end += (len(data) + SEC - 1) // SEC
            f.seek(lba * SEC); f.write(data); f.write(bytes(-len(data) % SEC))
            if (lba, len(data)) != (l, sz): isoio.set_file(f, T2, u, path, lba, len(data))
            print(f'  {path}: LBA {l}->{lba} size {sz}->{len(data)}')
        isoio.finish(f, u, end + 1)
    with open(ROOT + 'work/charmap.tsv', 'w', encoding='utf8') as m:
        for c, (sj, u) in sorted(cmap.items()): m.write(f'{c}\t{sj.hex()}\t{chr(u)}\n')
    print('->', DST, os.path.getsize(DST))


if __name__ == '__main__': main()
