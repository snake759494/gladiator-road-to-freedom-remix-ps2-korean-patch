import struct
ISO="D:/ps2/글라디에이터_로드투프리덤_리믹스/Gladiator - Road to Freedom - Remix (Japan).iso"
GG_LBA=1075959; GG_SIZE=226678576
def load():
    f=open(ISO,"rb");f.seek(GG_LBA*2048);h=f.read(0x8000)
    n=struct.unpack_from('<I',h)[0]
    o=list(struct.unpack_from('<%dI'%n,h,4))
    return f,n,o
def entries():
    f,n,o=load()
    valid=sorted(set(x for x in o if x!=0xffffffff))+[GG_SIZE//16]
    res={}
    for i,x in enumerate(o):
        if x==0xffffffff: continue
        nx=valid[valid.index(x)+1]
        res[i]=(x*16,(nx-x)*16)
    return f,res
def get(i):
    f,r=entries();off,sz=r[i];f.seek(GG_LBA*2048+off);return f.read(sz)
_names=None
def names():
    global _names
    if _names is None:
        d=get(0); _names={d[i:i+32].split(b'\0')[0].decode('cp932','replace'):i//32+1 for i in range(0,len(d),32)}
    return _names
def byname(n):
    return get(names()['DATA/'+n])
