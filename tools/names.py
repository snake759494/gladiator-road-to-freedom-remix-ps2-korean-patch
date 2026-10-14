"""이름 입력: 가나 표(NAMEENTRY_WORD 의 カナ列, 10열×9행)를 한글 음절 표로,
기본 이름(NAMEENTRY_DEFAULT 名前0~8, 표·열·행 좌표)을 한글 표기로 바꾼다."""
import struct
import csb, ary, kotext
W = 'D:/ps2/글라디에이터_로드투프리덤_리믹스/work/'
EXTRA = '김박최정준'


def names():
    return open(W + 'names_ko.txt', encoding='utf8').read().split()


def grid():
    sy = sorted(set(''.join(names())) | set(EXTRA))
    assert len(sy) <= 90, len(sy)
    sy += ['　'] * (90 - len(sy))
    return [sy[r * 10:(r + 1) * 10] for r in range(9)]      # [행][열]


def chars():
    return ''.join(c for row in grid() for c in row if c != '　')


def coords(name):
    g = grid(); pos = {c: (x, y) for y, row in enumerate(g) for x, c in enumerate(row)}
    out = [(1, *pos[c]) for c in name]
    assert len(out) <= 8
    return out + [(2, 0, 0)] * (9 - len(out))


def patch_word_csb(d, cmap):
    t = csb.parse(d); b = bytearray(d); g = grid()
    for r in range(t['rows']):
        for x in range(10):
            e = kotext.encode(g[r % 9][x], cmap)
            p = t['doff'] + (r * t['cols'] + 10 + x) * t['cw']
            b[p:p + t['cw']] = e + bytes(t['cw'] - len(e))
    return bytes(b)


def patch_word_ary(d, cmap):
    a = ary.parse(d); g = grid(); v = list(a['vals'])
    for r in range(18):
        for x in range(10):
            v[r * 20 + 10 + x] = (3, kotext.encode(g[r % 9][x], cmap))
    a['vals'] = v; out = ary.build(a)
    return out + b'\xff' * (-len(out) % 16)


def patch_default_csb(d):
    t = csb.parse(d); b = bytearray(d)
    for r, nm in enumerate(names()):
        for k, (tb, x, y) in enumerate(coords(nm)):
            e = f'{tb} {x} {y}'.encode()
            p = t['doff'] + (r * t['cols'] + 9 + k) * t['cw']
            b[p:p + t['cw']] = e + bytes(t['cw'] - len(e))
    return bytes(b)


def patch_default_ary(d):
    a = ary.parse(d); v = list(a['vals'])
    for r, nm in enumerate(names()):
        for k, (tb, x, y) in enumerate(coords(nm)):
            v[r * 18 + 9 + k] = (5, struct.pack('<4f', tb, x, y, 1.0))
    a['vals'] = v; out = ary.build(a)
    assert len(out) == len(ary.build(ary.parse(d)))
    return out + d[len(out):]
