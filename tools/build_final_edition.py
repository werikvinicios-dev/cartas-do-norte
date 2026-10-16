#!/usr/bin/env python3
"""Reconstrói content/ a partir da Edição Final (.docx) do autor.

A Edição Final reorganiza o romance em prólogo, 72 capítulos, 12 cartas e epílogo, com o mesmo texto da v4
salvo correções do autor. Este script:
- extrai o corpo do .docx (itálicos preservados como *…*, como na v4);
- gera content/reading/<id>.json com IDs de parágrafo estáveis (sha256 do texto, mesmo esquema da v4),
  para que destaques, notas e posições salvas continuem apontando para o mesmo parágrafo;
- transfere aquarelas, vestígios (minChapter), pranchas e progresso da v4 para a nova numeração;
- grava content/migration-v4.json (seção antiga → nova) e docs/RELATORIO_EDICAO_FINAL.md.
Uso: python3 tools/build_final_edition.py <Edicao_Final.docx>
"""
import json, re, sys, html, zipfile, hashlib, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCX = Path(sys.argv[1])
sha = lambda b: hashlib.sha256(b).hexdigest()
N = lambda t: re.sub(r'\s+', ' ', t.replace('*', '')).strip()
ROMAN = {r: i for i, r in enumerate('I II III IV V VI VII VIII IX X XI XII'.split(), 1)}
ORNAMENT = re.compile(r'^[—–\-·✧*\sNSLO]+$')

# ── 1. Parágrafos do .docx com itálico ──────────────────────────────────────
xml = zipfile.ZipFile(DOCX).read('word/document.xml').decode()
paras = []
for p in re.findall(r'<w:p[ >].*?</w:p>', xml, re.S):
    style = (re.search(r'<w:pStyle w:val="([^"]+)"', p) or [None, ''])[1]
    p = p.replace('<w:br/>', '<w:t>\n</w:t>')
    out = ''
    for r in re.findall(r'<w:r[ >].*?</w:r>', p, re.S):
        t = html.unescape(''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', r, re.S)))
        if not t: continue
        ital = re.search(r'<w:i(/>| w:val="(1|true)")', r) is not None
        out += f'*{t}*' if ital and t.strip() else t
    out = out.replace('**', '').strip()
    if out: paras.append((style, out))

# ── 2. Unidades de leitura ───────────────────────────────────────────────────
start = max(i for i, (s, t) in enumerate(paras) if s == 'ChapterKicker' and t == 'PRÓLOGO')
units, cur, part = [], None, 'Prólogo'
pending_part = None
for s, t in paras[start:]:
    if s == 'PartKicker': pending_part = t; continue
    if s == 'PartTitle': part = f'{pending_part} — {t}'; continue
    if s in ('ChapterKicker', 'LetterKicker'):
        if t == 'PRÓLOGO': cur = dict(id='prologue', type='prologue', title='Prólogo', chapter=None)
        elif t == 'EPÍLOGO': cur = dict(id='epilogue', type='epilogue', title='Epílogo', chapter=None)
        elif t.startswith('CAPÍTULO'):
            n = int(t.split()[1]); cur = dict(id=f'ch{n}', type='chapter', title='', chapter=n)
        elif t.startswith('CARTA'):
            n = ROMAN[t.split()[1]]; cur = dict(id=f'letter{n}', type='letter', title=f'Carta {t.split()[1]}', chapter=None)
        cur.update(part=part, subtitle='', raw=[]); units.append(cur); continue
    if cur is None: continue
    if s in ('Heading1', 'Heading2') and not cur['raw']:
        if cur['type'] == 'chapter': cur['title'] = N(t)
        else: cur['subtitle'] = N(t)
        continue
    if s == 'LetterTitle' and not cur['raw']: cur['subtitle'] = N(t); continue
    cur['raw'].append(('rule', '✧') if ORNAMENT.match(t) else ('para', t))

def blocks_for(u):
    cnt = collections.Counter(); out = []
    seq = ([('h2', u['title'])] if u['type'] == 'chapter' else []) + u['raw']
    for typ, text in seq:
        d = sha(text.encode())[:12]; cnt[d] += 1
        out.append({'id': f'p-{d}-{cnt[d]}', 'type': typ, 'text': text})
    return out
for u in units: u['blocks'] = blocks_for(u)

# ── 3. Correspondência com a v4 ─────────────────────────────────────────────
old_cat = json.loads((ROOT / 'content/catalog.json').read_text())
if old_cat.get('edition') == 'Edição Final':
    sys.exit('content/ já está na Edição Final: restaure o conteúdo v4 (git) antes de reconstruir a correspondência.')
old = {x['id']: json.loads((ROOT / f"content/reading/{x['id']}.json").read_text()) for x in old_cat['reading']}
where = {}  # texto normalizado → (novo id, novo bloco)
for u in units:
    for b in u['blocks']:
        if b['type'] == 'para': where.setdefault(N(b['text']), (u['id'], b['id']))
def locate(text): return where.get(N(text))
migration, anchors = {}, {}
for oid, data in old.items():
    paras_old = [b for b in data['blocks'] if b['type'] == 'para']
    hits = [locate(b['text']) for b in paras_old]
    found = [h for h in hits if h]
    migration[oid] = {'first': found[0][0] if found else None, 'last': found[-1][0] if found else None}
    for b, h in zip(paras_old, hits):
        if h: anchors[f'{oid}/{b["id"]}'] = h
num = {u['id']: u['chapter'] for u in units}
order = [u['id'] for u in units]

# Aquarelas: a ilustração de cada capítulo v4 vai para o capítulo final onde ele começa.
art = {}
for x in old_cat['reading']:
    if x.get('art'):
        dest = migration[x['id']]['first']
        if dest and dest not in art: art[dest] = x['art']
# Vestígios: liberados no fim do trecho correspondente (último capítulo final que contém o capítulo v4).
cap_end = {}
for oid, m in migration.items():
    if oid.startswith('ch') and m['last']:
        last = m['last']
        # se terminou numa carta, usa o último capítulo anterior a ela
        i = order.index(last)
        while num[order[i]] is None and i > 0: i -= 1
        cap_end[int(oid[2:])] = num[order[i]]
for a in old_cat['artifacts']:
    a['minChapter'] = cap_end[a['minChapter']]

# ── 4. Gravação ─────────────────────────────────────────────────────────────
rd = ROOT / 'content/reading'
for f in rd.glob('*.json'): f.unlink()
reading = []
for u in units:
    key = sha(json.dumps([(b['type'], b['text']) for b in u['blocks']], ensure_ascii=False, separators=(',', ':')).encode())
    (rd / f"{u['id']}.json").write_text(json.dumps({'id': u['id'], 'type': u['type'], 'title': u['title'], 'subtitle': u['subtitle'],
        'part': u['part'], 'blocks': u['blocks'], 'provenance': 'Edição Final do autor (.docx)', 'blocks_sha256': key}, ensure_ascii=False, indent=1))
    item = {'id': u['id'], 'type': u['type'], 'title': u['title'] if u['type'] == 'chapter' else u['title'],
            'subtitle': u['subtitle'], 'part': u['part'], 'chapter': u['chapter'], 'page': None,
            'blocks': len(u['blocks']), 'minChapter': u['chapter'] or 0, 'sha256': key}
    if u['id'] in art: item['art'] = art[u['id']]
    reading.append(item)
parts = []
for x in reading:
    if x['part'].startswith('PARTE') and x['part'] not in [p['title'] for p in parts]:
        parts.append({'title': x['part'], 'page': None, 'order': len(parts) + 1})
docx_sha = sha(DOCX.read_bytes())
front = {}
for i, (st, t) in enumerate(paras[:start]):
    if t.startswith('“') and 'Hebreus' in t: front['epigraph'], front['epigraphSource'] = t.rsplit('”', 1)[0] + '”', t.rsplit('”', 1)[1].strip()
    if st == 'FrontTitle' and t == 'DEDICATÓRIA':
        front['dedication'] = next(x for _, x in paras[i + 1:] if not ORNAMENT.match(x))
cat = {**{k: v for k, v in old_cat.items() if k not in ('reading', 'parts', 'artifacts')},
       'edition': 'Edição Final', 'sourceDocxSha256': docx_sha, 'front': front, 'parts': parts, 'reading': reading, 'artifacts': old_cat['artifacts']}
(ROOT / 'content/catalog.json').write_text(json.dumps(cat, ensure_ascii=False, indent=1))

mig = {'edition': 'final', 'sections': {k: v['first'] for k, v in migration.items()},
       'anchors': {k: v[1] for k, v in anchors.items() if k.split('/')[1] != v[1]}}
(ROOT / 'content/migration-v4.json').write_text(json.dumps(mig, ensure_ascii=False, separators=(',', ':')))

plates = json.loads((ROOT / 'content/plates.json').read_text())
for pl in plates:
    if pl.get('anchor'):
        h = anchors.get(f"{pl['section']}/{pl['anchor']}")
        pl['section'], pl['anchor'] = h
    else:
        pl['section'] = 'epilogue'
(ROOT / 'content/plates.json').write_text(json.dumps(plates, ensure_ascii=False, indent=1))

# ── 5. Relatório ────────────────────────────────────────────────────────────
oldtexts = [N(b['text']) for d in old.values() for b in d['blocks'] if b['type'] == 'para']
newtexts = [N(b['text']) for u in units for b in u['blocks'] if b['type'] == 'para']
so, sn = set(oldtexts), set(newtexts)
gone = [t for t in oldtexts if t not in sn]; added = [t for t in newtexts if t not in so]
rep = [f'# Relatório — adoção da Edição Final\n',
       f'Fonte: `{DOCX.name}` · SHA-256 `{docx_sha}`.\n',
       f'- Unidades: {len(units)} (prólogo, {sum(u["type"]=="chapter" for u in units)} capítulos, {sum(u["type"]=="letter" for u in units)} cartas, epílogo). A v4 tinha 67 (53 capítulos).',
       f'- Parágrafos: v4 {len(oldtexts)} · Edição Final {len(newtexts)} · idênticos {len(oldtexts)-len(gone)}.',
       f'- Itálicos lidos das formatações do .docx e guardados como `*…*`, como na v4.',
       f'- IDs de parágrafo seguem o esquema da v4 (sha256 do texto); {len(anchors)-len(mig["anchors"])} de {len(anchors)} parágrafos mantêm o mesmo ID.\n',
       '## Parágrafos da v4 que não estão na Edição Final\n', *[f'- {t[:220]}' for t in gone],
       '\n## Parágrafos novos ou alterados na Edição Final\n', *[f'- {t[:220]}' for t in added],
       '\n## Correspondência de capítulos (v4 → Edição Final, onde o capítulo começa)\n',
       ' · '.join(f'{k}→{v["first"]}' for k, v in migration.items()),
       '\n\n## Vestígios (capítulo de liberação na nova numeração)\n', *[f'- {a["title"]}: capítulo {a["minChapter"]}' for a in cat['artifacts']]]
(ROOT / 'docs/RELATORIO_EDICAO_FINAL.md').write_text('\n'.join(rep) + '\n')
print(len(units), 'unidades ·', len(gone), 'removidos ·', len(added), 'novos/alterados ·', len(art), 'aquarelas')
