"""ARY(컴파일된 테이블) 파서/직렬화
헤더: u32 행크기, u32 행수, u32 필드수, u32 0 / 필드: (u8 타입, u16 오프셋)
타입 0=int32 1=float 2=u8 3=문자열(NUL 종료) 5=float4 7=배열
구조 영역: 행마다 배열 필드의 설명자(u32 원소크기, u32 개수, u32 하위필드수, u32 ?, 하위필드*3) — 재귀
값 영역: 행마다 필드 값 순서대로, 배열은 원소별로 하위필드 값"""
import struct
SZ={0:4,1:4,2:1,5:16,4:4,6:8}
class Rd:
    def __init__(s,d,p): s.d=d; s.p=p
    def u32(s): v=struct.unpack_from('<I',s.d,s.p)[0]; s.p+=4; return v
    def fields(s,n):
        out=[]
        for _ in range(n):
            t=s.d[s.p]; o=struct.unpack_from('<H',s.d,s.p+1)[0]; s.p+=3; out.append((t,o))
        return out
def _desc(r):
    es,cnt,ns,fl=r.u32(),r.u32(),r.u32(),r.u32()
    sub=r.fields(ns)
    node={'es':es,'cnt':cnt,'fl':fl,'f':sub,'kids':[]}
    for e in range(cnt):
        kk=[]
        for t,o in sub:
            if t==7: kk.append(_desc(r))
        node['kids'].append(kk)
    return node
def parse(d):
    r=Rd(d,0)
    h=[r.u32() for _ in range(4)]
    F=r.fields(h[2])
    descs=[]
    for row in range(h[1]):
        rr=[]
        for t,o in F:
            if t==7: rr.append(_desc(r))
        descs.append(rr)
    sp=r.p
    vals=[]   # 평탄화된 (타입, 값)
    def rv(t):
        if t==3:
            e=d.index(b'\0',r.p); v=d[r.p:e]; r.p=e+1; vals.append((3,v))
        else:
            n=SZ[t]; vals.append((t,d[r.p:r.p+n])); r.p+=n
    def rarr(node):
        for e in range(node['cnt']):
            ki=iter(node['kids'][e])
            for t,o in node['f']:
                if t==7: rarr(next(ki))
                else: rv(t)
    for row in range(h[1]):
        di=iter(descs[row])
        for t,o in F:
            if t==7: rarr(next(di))
            else: rv(t)
    return {'head':d[:sp],'vals':vals,'tail':d[r.p:],'end':r.p}
def build(a):
    out=bytearray(a['head'])
    for t,v in a['vals']:
        out+=v+(b'\0' if t==3 else b'')
    return bytes(out)
