#!/usr/bin/env python3
"""Gera os dados da v4 a partir do catálogo aprovado, sem tocar no texto do romance.

- Transcrições saem do catálogo e passam a ser carregadas só quando o vestígio é liberado
  (content/artifacts/<id>.json).
- Cada documento recebe a sua forma material (kind), deduzida do título editorial.
- Cada mapa recebe a posição dos rótulos impressos na própria imagem (porcentagem da largura/altura),
  medida visualmente sobre o fac-símile. Nenhuma coordenada geográfica é inventada.
- content/places.json lista, para cada localidade nomeada nos mapas ou no índice, as entradas de
  leitura em que o nome aparece literalmente no texto aprovado.
Pode ser executado várias vezes: lê transcrições de content/artifacts quando já foram extraídas.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cat_path = ROOT / 'content/catalog.json'
c = json.loads(cat_path.read_text())
art_dir = ROOT / 'content/artifacts'
art_dir.mkdir(exist_ok=True)

KIND = {
    'testament': 'testamento', 'constancia_blueprint': 'prancha', 'passenger_register': 'registro',
    'diary_blue': 'diario', 'radio_log': 'registro-maritimo', 'order': 'oficial', 'tomas_note': 'manuscrito',
    'balu_transmission': 'transmissao', 'ana_letter': 'carta', 'brass_tube': 'objeto', 'sentence_extract': 'juridico',
}
STAGE = {'Porto da Vigília': (26.4, 77), 'Farol da Vigília': (35, 64), 'Ponta do Corvo': (45.6, 72.7),
         'Salinas': (24.4, 52), 'Canal da Agulha': (52, 69)}
LATE = {'Estação Norte': (58.6, 24.4), 'Ilha do Sino': (61.6, 31.6), 'Ilha dos Espelhos': (57, 50.7)}
LAST = {'Enseada dos Cedros': (67.2, 59), 'Ilha Sem Nome': (69.6, 76), 'Tanque Treze': (38.8, 83.6)}
LABELS = {
    'map_stage_1': STAGE,
    'canal_chart': {'Farol da Vigília': (33.2, 61.5), 'Ponta do Corvo': (77, 62.8), 'Canal da Agulha': (50.4, 71.6),
                    'Porto da Vigília': (22, 77), 'recifes': (54.4, 79)},
    'map_stage_2': {**STAGE, **LATE},
    'map_stage_3': {**STAGE, **LATE, **LAST},
    'map_stage_4': {**STAGE, **LATE, **LAST},
    'north_restored_chart': {**STAGE, **LATE, **LAST},
    'gruta_map': {'Entrada marítima': (19, 73), 'Câmara central': (47, 50.7), 'Saída alta': (75.5, 28), 'Chaminé': (69.6, 49)},
}

for a in c['artifacts']:
    f = art_dir / f"{a['id']}.json"
    if 'transcription' in a:
        f.write_text(json.dumps({'id': a['id'], 'transcription': a.pop('transcription'),
                                 'status': a.pop('transcriptionStatus')}, ensure_ascii=False, indent=1))
    if a['type'] == 'document':
        a['kind'] = KIND[a['id']]
    else:
        a['kind'] = 'mapa'
        a['labels'] = [{'name': n, 'x': x, 'y': y} for n, (x, y) in LABELS[a['id']].items()]

# Localidades: nomes impressos nos mapas + índice narrativo já existente.
names = sorted({l['name'] for a in c['artifacts'] if a['type'] == 'map' and a['id'] != 'gruta_map'
                for l in a['labels'] if l['name'] != 'recifes'} | {'Gruta das Vozes', 'Ilha da Memória'})
order = [x['id'] for x in c['reading']]
texts = {x['id']: ' '.join(b['text'] for b in json.loads((ROOT / f"content/reading/{x['id']}.json").read_text())['blocks'])
         for x in c['reading']}
places = []
for n in names:
    mentions = [i for i in order if n.lower() in texts[i].lower()]
    if not mentions:
        continue
    maps = [a['id'] for a in c['artifacts'] if a['type'] == 'map' and any(l['name'] == n for l in a['labels'])]
    places.append({'name': n, 'first': mentions[0], 'firstIndex': order.index(mentions[0]), 'mentions': mentions, 'maps': maps})
places.sort(key=lambda p: (p['firstIndex'], p['name']))
(ROOT / 'content/places.json').write_text(json.dumps(places, ensure_ascii=False, indent=1))
PEOPLE = ['Miguel', 'Jonas Vale', 'Clara Moura', 'Ana Moura', 'Abel Faria', 'Estevão', 'Gabriel', 'Davi', 'Severo', 'Baltasar', 'Elias', 'Tomás', 'Balu']
people = []
for n in PEOPLE:
    mentions = [i for i in order if __import__('re').search(r'\b' + n + r'\b', texts[i])]
    if mentions:
        people.append({'name': n, 'first': mentions[0], 'firstIndex': order.index(mentions[0]), 'mentions': len(mentions)})
people.sort(key=lambda p: (p['firstIndex'], p['name']))
(ROOT / 'content/people.json').write_text(json.dumps(people, ensure_ascii=False, indent=1))
print('pessoas:', ', '.join(f"{p['name']}→{p['first']}" for p in people))
cat_path.write_text(json.dumps(c, ensure_ascii=False, indent=1))
print(len(places), 'localidades:', ', '.join(f"{p['name']}→{p['first']}" for p in places))
