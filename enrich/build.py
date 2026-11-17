#!/usr/bin/env python3
"""enrich/exp_*.jsonl 을 base_bank.js 에 병합해 bank.js 를 다시 만든다.

두 가지 레코드 형식을 모두 받는다.

(A) 지문 단위
  {"id":"Q0017411","why":"...","theory":"· ...\\n· ...","trap":"...","arts":["국기법 §56"]}

(B) 문항 단위 (같은 규칙을 5지문이 공유하므로 출력 절약)
  {"Q":"2017-54-41","theory":"· ...\\n· ...","arts":["국기법 §56"],
   "s":{"Q0017411":{"why":"...","trap":"..."}, ...}}
  지문별로 theory/arts 를 덮어쓸 수도 있다.
  "stmt" 를 주면 지문 문장을 교정한다(원문 대조로 오탈자를 확인한 경우만).

- why    → x['why']   (앱: 「핵심 이유」)
- theory → x['main']  (앱: 「근거·이론」)
- trap   → x['trap']  (앱: 「함정 포인트」)
- arts   → x['arts']  (앱: 「관련 조문」)
"""
import json, glob, os, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
BASE = os.path.join(HERE, 'base_bank.js')


def load_base():
    s = open(BASE, encoding='utf-8').read()
    i, j = s.index('['), s.rindex(']')
    return json.loads(s[i:j+1])


CODE = {'Q': '세법학개론', 'A': '행정소송법', 'R': '재정학', 'C': '회계학개론(말문제)'}


def groups_of(base):
    g = {}
    for x in base:
        g.setdefault((x['id'][0], x['year'], x['round'], x['num']), []).append(x['id'])
    return g


def load_exp(base):
    by_id = {}
    stmt_fix = {}
    groups = groups_of(base)
    for p in sorted(glob.glob(os.path.join(HERE, 'exp_*.jsonl'))):
        for ln, line in enumerate(open(p, encoding='utf-8'), 1):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            try:
                r = json.loads(line)
            except Exception as e:
                print(f'!! JSON 오류 {os.path.basename(p)}:{ln}: {e}')
                sys.exit(1)
            if 'id' in r:
                if r['id'] in by_id:
                    print(f'!! 중복 id {r["id"]} in {os.path.basename(p)}:{ln}')
                    sys.exit(1)
                by_id[r['id']] = r
                continue
            # 문항 단위
            q = r['Q']
            code = 'Q'
            if ':' in q:
                code, q = q.split(':', 1)
            key = q.split('-')
            k = (code, int(key[0]), '제%s회' % key[1], int(key[2]))
            if k not in groups:
                print(f'!! 없는 문항 {r["Q"]} ({os.path.basename(p)}:{ln})')
                sys.exit(1)
            for sid in groups[k]:
                item = dict(r.get('s', {}).get(sid) or {})
                item.setdefault('theory', r.get('theory'))
                item.setdefault('arts', r.get('arts'))
                item.setdefault('why', r.get('why'))
                item['id'] = sid
                by_id[sid] = item
                if item.get('stmt'):
                    stmt_fix[sid] = item['stmt']
            missing = [s_ for s_ in groups[k] if s_ not in by_id]
            if missing:
                print(f'!! {r["Q"]} 지문 누락: {missing} ({os.path.basename(p)}:{ln})')
                sys.exit(1)
    return by_id, stmt_fix


def main():
    base = load_base()
    exp, stmt_fix = load_exp(base)
    ids = {x['id'] for x in base}
    bad = [k for k in exp if k not in ids]
    if bad:
        print('!! base 에 없는 id:', bad[:10], len(bad)); sys.exit(1)

    miss = []
    for x in base:
        r = exp.get(x['id'])
        if not r:
            miss.append(x['id']); continue
        for k in ('why', 'theory'):
            if not r.get(k):
                print('!! 필수 필드 없음', x['id'], k); sys.exit(1)
        x['why'] = r['why']
        x['main'] = r['theory']
        x['trap'] = r.get('trap') or ''
        if r.get('arts'):
            x['arts'] = r['arts']
        if x['id'] in stmt_fix:
            x['stmt_orig'] = x['stmt']
            x['stmt'] = stmt_fix[x['id']]
        x['expv'] = 2

    out = 'window.BANK=' + json.dumps(base, ensure_ascii=False, separators=(',', ':')) + ';\n'
    open(os.path.join(SITE, 'bank.js'), 'w', encoding='utf-8').write(out)

    raw = open(os.path.join(SITE, 'bank.js'), encoding='utf-8').read()
    chk = json.loads(raw[len('window.BANK='):-2])
    assert len(chk) == len(base), '지문 수 불일치'
    by = Counter(x['subject'] for x in chk)
    done = Counter(x['subject'] for x in chk if x.get('expv') == 2)
    ln = [len(x['why'] or '') + len(x['main'] or '') + len(x.get('trap') or '') for x in chk if x.get('expv') == 2]
    print(f"bank.js 재생성 — 지문 {len(chk):,} · 풍성화 {sum(done.values()):,}")
    for s in by:
        print(f"  {s:12s} {done[s]:>4} / {by[s]:>4}  ({done[s]/by[s]*100:5.1f}%)")
    if ln:
        print(f"  해설 길이 평균 {sum(ln)/len(ln):.0f}자 · 최소 {min(ln)}자 · 최대 {max(ln)}자")
    print(f"  미보강 {len(miss)}개 · 문장 교정 {len(stmt_fix)}개")
    open(os.path.join(HERE, 'missing.txt'), 'w').write('\n'.join(miss))
    print('  파일 %.2f MB' % (os.path.getsize(os.path.join(SITE, 'bank.js')) / 1048576))


if __name__ == '__main__':
    main()
