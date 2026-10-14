"""ISO9660 + UDF 파일 위치/크기 갱신, 이미지 끝 추가"""
import struct,os
import udf as udfmod
SEC=2048
def _dir_records(f,lba,size):
    f.seek(lba*SEC); data=f.read(size); out=[]; p=0
    while p<len(data):
        ln=data[p]
        if ln==0: p=(p//SEC+1)*SEC; continue
        flags=data[p+25]; nl=data[p+32]; name=data[p+33:p+33+nl]
        out.append((lba*SEC+p,name,struct.unpack_from('<I',data,p+2)[0],struct.unpack_from('<I',data,p+10)[0],flags))
        p+=ln
    return out
def walk(f):
    f.seek(16*SEC+156); root=f.read(34)
    res={}; st=[('',struct.unpack_from('<I',root,2)[0],struct.unpack_from('<I',root,10)[0])]
    while st:
        path,lba,size=st.pop()
        for pos,name,l,s,flags in _dir_records(f,lba,size):
            if name in (b'\0',b'\1'): continue
            n=name.decode('ascii').split(';')[0]
            if flags&2: st.append((path+'/'+n,l,s))
            else: res[path+'/'+n]=(pos,l,s)
    return res
def set_file(f,table,u,path,lba,size):
    pos=table[path][0]
    f.seek(pos+2); f.write(struct.pack('<I',lba)+struct.pack('>I',lba))
    f.seek(pos+10); f.write(struct.pack('<I',size)+struct.pack('>I',size))
    u.set_file(path,lba,size)
def finish(f,u,end_sectors):
    f.seek(16*SEC+80); f.write(struct.pack('<I',end_sectors)+struct.pack('>I',end_sectors))
    f.truncate(end_sectors*SEC)
    u.grow(end_sectors)
