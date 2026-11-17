import json,sys
D=json.loads(open('/workspace/deploy/cta-ox-app/site/enrich/base_bank.js').read().split('window.BANK=',1)[1].rsplit(';',1)[0])
subj=sys.argv[1]; start=int(sys.argv[2]); cnt=int(sys.argv[3])
groups=[];seen={}
for x in D:
    if x['subject']!=subj: continue
    k=(x['year'],x['round'],x['num'])
    if k not in seen: seen[k]=[]; groups.append(k)
    seen[k].append(x)
sel=groups[start:start+cnt]
code={'세법학개론':'Q','행정소송법':'A','재정학':'R','회계학개론(말문제)':'C'}[subj]
print(f'[{subj}] Q {start+1}~{start+len(sel)} of {len(groups)}')
for k in sel:
    xs=sorted(seen[k],key=lambda x:x['no'])
    print(f"\n== Q {code}:{k[0]}-{k[1].replace('제','').replace('회','')}-{k[2]} | {xs[0]['tax']} | ans {xs[0]['ans']} | {xs[0]['qtype']}")
    print("Q:",xs[0]['q'][:300])
    for x in xs:
        print(f" [{x['id']}] {x['no']}.{x['answer']} | {x['stmt']}")
        print(f"    why={x['why']}")
