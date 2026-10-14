import gg,csb,sys
def s(b): return b.split(b'\0')[0].decode('cp932','replace')
for n in sys.argv[1:]:
    t=csb.parse(gg.byname(n))
    print('=====',n,t['rows'],t['cols'],t['cw'])
    print(' | '.join(s(c) for c in t['cn']))
    for i,row in enumerate(t['cells'][:int(__import__('os').environ.get('NR','8'))]):
        print(s(t['rn'][i]),'::',' | '.join(s(c) for c in row))
