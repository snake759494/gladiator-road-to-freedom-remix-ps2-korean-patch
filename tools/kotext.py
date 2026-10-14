"""번역 로드 + 한글→SJIS 한자 코드 매핑 + 인코딩"""
import json,glob,os,struct
W='D:/ps2/글라디에이터_로드투프리덤_리믹스/work/'
def load_csb_tr():
    order=json.load(open(W+'src_order.json',encoding='utf8'))
    tr={}
    for f in sorted(glob.glob(W+'ko/*.tsv')):
        for l in open(f,encoding='utf8'):
            l=l.rstrip('\n')
            if not l: continue
            i,ko=l.split('\t',1); tr[order[int(i)]]=ko
    return tr
def load_elf_tr():
    out=[]
    for fn in ('elf_ko.tsv','elf_en_ko.tsv'):
        for l in open(W+fn,encoding='utf8'):
            l=l.rstrip(chr(10))
            if l: a,ko=l.split(chr(9),1); out.append((int(a,16),ko))
    return out
def is_hangul(c): return 0xAC00<=ord(c)<=0xD7A3
def kanji_slots(fnt_pages,extra=None):
    """FNT에 글리프가 있는 SJIS 한자 코드 (제1수준→제2수준 순)"""
    res=[]
    for hi in list(range(0x88,0xA0))+list(range(0xE0,0xEB)):
        for lo in list(range(0x40,0x7F))+list(range(0x80,0xFD)):
            if hi==0x88 and lo<0x9F: continue
            b=bytes([hi,lo])
            try: u=b.decode('cp932')
            except: continue
            if len(u)!=1: continue
            u=ord(u)
            if not (0x4E00<=u<=0x9FFF): continue
            pg=fnt_pages.get(u>>8)
            if not pg or pg[1][u&0xff]==0: continue
            if extra and not extra(u): continue
            res.append((b,u))
    return res
def build_map(texts,fnt_pages,extra=None):
    chars=sorted({c for t in texts for c in t if is_hangul(c)})
    slots=kanji_slots(fnt_pages,extra)
    assert len(chars)<=len(slots),(len(chars),len(slots))
    return {c:slots[i] for i,c in enumerate(chars)}
def encode(s,cmap):
    out=b''
    for c in s:
        if is_hangul(c): out+=cmap[c][0]
        else: out+=c.encode('cp932')
    return out
def elf_room(d,off):
    e=d.index(b'\0',off)
    n=e
    while n<len(d) and d[n]==0: n+=1
    return n-off
