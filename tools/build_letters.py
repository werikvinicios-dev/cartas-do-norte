#!/usr/bin/env python3
"""Gera content/letters.json: as cartas e escritos que aparecem no romance.

- As 12 cartas da Edição Final (unidades letter1…letter12): envelope lacrado, endereçado como no livro.
- Escritos dentro dos capítulos, localizados pelo início e fim exatos do texto (itálico no livro).
  Cada trecho é marcado pelos IDs de parágrafo; o texto não é copiado nem alterado.
  Títulos descrevem o objeto como o próprio texto o nomeia (declaração, carta, folha, bilhete, resposta)
  e chamam as pessoas pelo nome real: apelidos íntimos (Miqueias, Mico) ficam só dentro do texto do livro.
  O id 'carta-jonas-miqueias' é mantido para preservar o estado salvo dos leitores.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
cat = json.loads((ROOT / 'content/catalog.json').read_text())
blocks = {x['id']: json.loads((ROOT / f"content/reading/{x['id']}.json").read_text())['blocks'] for x in cat['reading']}
ROMAN = 'I II III IV V VI VII VIII IX X XI XII'.split()

def span(sec, start, end):
    b = [x for x in blocks[sec] if x['type'] == 'para']
    i = next(k for k, x in enumerate(b) if x['text'].lstrip('*').startswith(start))
    j = next(k for k, x in enumerate(b) if k >= i and x['text'].lstrip('*').startswith(end))
    assert all(x['text'].strip().startswith('*') for x in b[i:j + 1]), (sec, start)
    return [b[i]['id'], b[j]['id']]

INLINE = [  # id, seção, tipo, lacrada, título, trechos (início, fim)
    ('declaracao-jonas', 'ch2', 'declaracao', False, 'A declaração de Jonas', [('Não coloco a verdade', 'Não coloco a verdade')]),
    ('carta-jonas-miqueias', 'ch3', 'carta', True, 'A carta de Jonas a Miguel', [('Se você está lendo', 'Se você está lendo'), ('Não vou pedir que confie', 'Jonas.')]),
    ('folha-doze-cartas', 'ch3', 'folha', False, 'A folha sobre os objetos', [('DOZE CARTAS', 'Nesta, talvez')]),
    ('notas-desenhos', 'ch4', 'folha', False, 'As notas nos desenhos', [('Mico diz que isto afunda', 'Perguntar a Clara'), ('Não terminei porque', 'Não terminei porque')]),
    ('bilhete-ponta-do-corvo', 'ch46', 'bilhete', False, 'O bilhete', [('Jonas acreditava que verdade', 'Encontre-me na Ponta do Corvo')]),
    ('carta-lidia', 'ch60', 'carta', True, 'A carta de Lídia', [('Meu filho,', 'Mãe.')]),
    ('resposta-ana', 'ch61', 'carta', False, 'A resposta de Ana', [('Você veio à minha casa', 'Ana.')]),
    ('bilhete-gabriel', 'ch68', 'bilhete', True, 'O bilhete de Gabriel', [('Mico,', 'Gabriel.')]),
]
out = []
for x in cat['reading']:
    if x['type'] == 'letter':
        n = int(x['id'][6:])
        out.append({'id': x['id'], 'section': x['id'], 'kind': 'carta', 'sealed': True, 'whole': True,
                    'title': f'Carta {ROMAN[n - 1]}', 'to': x['subtitle'], 'part': x['part']})
for lid, sec, kind, sealed, title, parts in INLINE:
    out.append({'id': lid, 'section': sec, 'kind': kind, 'sealed': sealed, 'whole': False, 'title': title,
                'spans': [span(sec, a, b) for a, b in parts]})
(ROOT / 'content/letters.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(len(out), 'escritos:', ', '.join(f"{o['id']}@{o['section']}" for o in out))
