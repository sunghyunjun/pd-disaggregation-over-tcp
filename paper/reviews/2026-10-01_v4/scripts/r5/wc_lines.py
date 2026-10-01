import re,sys
lines=open(sys.argv[1]).read().split('\n')
def clean(t):
    t=re.sub(r'\\(cite|ref|label|eqref)\{[^}]*\}','X',t)
    t=re.sub(r'\\[a-zA-Z]+\*?','',t)
    t=re.sub(r'[{}$\\~]',' ',t)
    return len(t.split())
for spec in sys.argv[2:]:
    a,b=(spec.split('-')+[spec])[:2]; a=int(a); b=int(b)
    print(spec, clean('\n'.join(lines[a-1:b])))
