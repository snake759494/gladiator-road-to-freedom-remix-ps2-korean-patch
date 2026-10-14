import sys,gg,imgtex,numpy as np
from PIL import Image,ImageDraw
S='C:/Users/Jay/AppData/Local/Temp/claude/D--ps2------------------/536147a6-8391-447f-936a-328ce9b55826/scratchpad/'
def view(name,x0=0,y0=0,x1=None,y1=None,sc=3,step=8,out=None,data=None):
    d=data or gg.byname(name);idx,rgba,pal=imgtex.decode(d)
    h,w=rgba.shape[:2];x1=x1 or w;y1=y1 or h
    bg=np.zeros((h,w,3));bg[:]=[30,50,80];a=rgba[...,3:4]/255
    im=(rgba[...,:3]*a+bg*(1-a)).astype(np.uint8)[y0:y1,x0:x1]
    I=Image.fromarray(im).resize(((x1-x0)*sc,(y1-y0)*sc),Image.NEAREST);D=ImageDraw.Draw(I)
    for x in range(x0-x0%step,x1,step):
        c=(255,0,0) if x%32==0 else (90,0,0);D.line([((x-x0)*sc,0),((x-x0)*sc,I.height)],fill=c)
        if x%32==0: D.text(((x-x0)*sc+2,0),str(x),fill=(255,255,0))
    for y in range(y0-y0%step,y1,step):
        c=(0,255,0) if y%32==0 else (0,90,0);D.line([(0,(y-y0)*sc),(I.width,(y-y0)*sc)],fill=c)
        if y%32==0: D.text((2,(y-y0)*sc+2),str(y),fill=(0,255,255))
    I.save(S+(out or 'g.png'))
if __name__=='__main__':
    a=sys.argv; view(a[1],*map(int,a[2:7]),out=a[7] if len(a)>7 else None)
