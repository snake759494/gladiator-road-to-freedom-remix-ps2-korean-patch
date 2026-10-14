import struct
def parse(d):
    rows,cols,doff,cw,roff,coff=struct.unpack_from('<6I',d,0x10)
    rn=[d[roff+i*32:roff+i*32+32].split(b'\0')[0] for i in range(rows)]
    cn=[d[coff+i*32:coff+i*32+32].split(b'\0')[0] for i in range(cols)]
    cells=[[d[doff+(r*cols+c)*cw:doff+(r*cols+c+1)*cw] for c in range(cols)] for r in range(rows)]
    return dict(rows=rows,cols=cols,doff=doff,cw=cw,rn=rn,cn=cn,cells=cells)
def jp(b): return any(x>=0x81 for x in b.split(b'\0')[0])
