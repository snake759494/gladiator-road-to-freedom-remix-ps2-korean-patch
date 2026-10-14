import numpy as np,struct,swz
def info(d):
    w,h=struct.unpack_from('<2H',d,0x180); psm=d[0x40]
    bpp={0x13:8,0x14:4,0x00:32}[psm]
    return w,h,bpp
def _vm(px):
    n=len(px)//4; w32=64; h32=n//w32
    ix=swz.idx32(1,w32,h32); vm=np.zeros(max(1<<22,(ix.max()+4)),np.uint8)
    p=np.frombuffer(px,np.uint8)[:n*4].reshape(h32,w32,4)
    for k in range(4): vm[ix+k]=p[...,k]
    return vm,ix
def decode(d):
    """returns (index image, palette RGBA(n,4)) or (rgba,None) for 32bit"""
    w,h,bpp=info(d)
    n=w*h*bpp//8; px=d[0x200:0x200+n]
    if bpp==32:
        return np.frombuffer(px,np.uint8).reshape(h,w,4).copy(),None
    bw=max(1,w//64)
    vm,_=_vm(px)
    if bpp==4:
        a=swz.idx4(max(2,bw),w,h);b=vm[a>>1];im=np.where(a&1,b>>4,b&15).astype(np.uint8)
        pal=np.frombuffer(d[0x200+n+0x80:0x200+n+0x80+64],np.uint8).reshape(16,4)
    else:
        a=swz.idx8(max(2,bw),w,h);im=vm[a]
        pal=np.frombuffer(d[0x200+n+0x80:0x200+n+0x80+1024],np.uint8).reshape(256,4)
        i=np.arange(256);sw=(i&~0x18)|((i&8)<<1)|((i&16)>>1);pal=pal[sw]
    return im,pal
def to_rgba(d):
    im,pal=decode(d)
    if pal is None: return im
    p=pal.astype(int).copy();p[:,3]=np.minimum(255,p[:,3]*2)
    return p[im].astype(np.uint8)
