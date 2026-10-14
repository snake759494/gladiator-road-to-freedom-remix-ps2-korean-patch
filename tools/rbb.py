"""DATA.RBB: 'siff' 헤더, 0x80 'RIDX' u32 바이트수, (offset,size)*N, 데이터 시작 0x3000
각 .dat = GG.DAT와 같은 형식(u32 개수, u32 오프셋(16바이트 단위), 0번 항목 = 32바이트 이름표)"""
import struct
BASE=0x3000
def dats(rbb):
    n=struct.unpack_from('<I',rbb,0x84)[0]//8
    return [struct.unpack_from('<2I',rbb,0x88+i*8) for i in range(n)]
def files(rbb):
    out=[]
    for di,(off,size) in enumerate(dats(rbb)):
        p=BASE+off
        cnt=struct.unpack_from('<I',rbb,p)[0]
        if cnt==0 or cnt>5000: continue
        o=list(struct.unpack_from('<%dI'%cnt,rbb,p+4))
        valid=sorted(set(x for x in o if x!=0xffffffff))+[size//16]
        ent={}
        for i,x in enumerate(o):
            if x==0xffffffff: continue
            nx=min(v for v in valid if v>x) if any(v>x for v in valid) else size//16
            ent[i]=(p+x*16,(nx-x)*16)
        if 0 not in ent: continue
        no,ns=ent[0]
        names=[rbb[no+k:no+k+32].split(b'\0')[0].decode('cp932','replace') for k in range(0,ns,32)]
        for k,nm in enumerate(names):
            if k+1 in ent and nm: out.append((di,nm,ent[k+1][0],ent[k+1][1]))
    return out
