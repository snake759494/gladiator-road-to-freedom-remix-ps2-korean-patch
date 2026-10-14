import struct,numpy as np,swz,gg
def parse_fnt(d):
    n=struct.unpack_from('<H',d,2)[0];pages={}
    for p in range(n):
        o=4+p*2050;lead=struct.unpack_from('<H',d,o)[0]>>8
        pages[lead]=(o,[struct.unpack_from('<Q',d,o+2+8*i)[0] for i in range(256)])
    return pages
def unswz4(data,w,h):
    px=np.frombuffer(data,np.uint8);n=len(px)//4
    w32=64;h32=n//w32
    ix=swz.idx32(1,w32,h32);vm=np.zeros(1<<23,np.uint8);p=px.reshape(h32,w32,4)
    for k in range(4): vm[ix+k]=p[...,k]
    a=swz.idx4(w//64,w,h);b=vm[a>>1];return np.where(a&1,b>>4,b&15).astype(np.uint8),ix,a
