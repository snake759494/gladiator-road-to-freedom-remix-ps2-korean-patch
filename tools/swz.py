import numpy as np,gsmem
def idx32(bw,w,h):
    y,x=np.mgrid[0:h,0:w]
    page=(y//32)*bw+(x//64);px_=x%64;py=y%32
    B=np.array(gsmem.BLOCK32);C=np.array(gsmem.COL32)
    return (page*2048+B[py//8,px_//8]*64+C[py%8,px_%8])*4
def idx4(bw,w,h):
    y,x=np.mgrid[0:h,0:w]
    page=(y//128)*(bw//2)+(x//128);px_=x%128;py=y%128
    B=np.array(gsmem.BLOCK4);C=np.array(gsmem.COL4)
    by=py%16;col=by//4
    return (page*8192+B[py//16,px_//32]*256+col*64)*2+C[col%2,by%4,px_%32]
def idx8(bw,w,h):
    y,x=np.mgrid[0:h,0:w]
    page=(y//64)*(bw//2)+(x//128);px_=x%128;py=y%64
    B=np.array(gsmem.BLOCK8);C=np.array(gsmem.COL8)
    by=py%16;col=by//4
    return page*8192+B[py//16,px_//16]*256+col*64+C[col%2,by%4,px_%16]
