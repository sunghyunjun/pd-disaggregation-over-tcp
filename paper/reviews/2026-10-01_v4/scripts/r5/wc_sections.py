import re,sys
src=open(sys.argv[1]).read()
body=src.split('\\begin{document}')[1]
# cut at appendix
main=body.split('\\appendix')[0]
# split by section/subsection keeping line numbers
lines=src.split('\n')
start=[i for i,l in enumerate(lines) if '\\begin{document}' in l][0]
end=[i for i,l in enumerate(lines) if '\\appendix' in l][0]
def clean(t):
    t=re.sub(r'%.*','',t)
    t=re.sub(r'\\begin\{(figure|table)\}.*?\\end\{\1\}','',t,flags=re.S)
    t=re.sub(r'\\(cite|ref|label|eqref)\{[^}]*\}','X',t)
    t=re.sub(r'\\[a-zA-Z]+\*?','',t)
    t=re.sub(r'[{}$\\~]',' ',t)
    return len(t.split())
cur='front'; buf=[]; startl=start; out=[]
for i in range(start,end):
    l=lines[i]
    m=re.match(r'\\(sub)?section\*?\{([^}]*)\}',l.strip())
    if m or l.startswith('\\begin{abstract}'):
        out.append((cur,startl+1,clean('\n'.join(buf))))
        cur=(('  ' if m and m.group(1) else '')+(m.group(2) if m else 'abstract')); buf=[]; startl=i
    buf.append(l)
out.append((cur,startl+1,clean('\n'.join(buf))))
tot=0
for n,s,w in out:
    print(f'{s:4d} {w:5d} {n}'); 
    if n!='abstract': tot+=w
print('total (excl abstract)',tot)
# figure/table captions
caps=re.findall(r'\\caption\{(.*?)\}\n\\label',body.split('\\appendix')[0],flags=re.S)
print('main captions words', sum(clean(c) for c in caps))
