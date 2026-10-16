# Registro de QA — v0.5

**Data:** 16/10/2026. Ambiente: `python3 -m http.server` + Chromium (Playwright) real, com HTTP e IndexedDB reais.

| Verificação | Resultado |
|---|---|
| `python3 tests/integrity_qa.py` | 22/22 — 86 unidades, 72 capítulos em ordem, hashes, 5540/5540 parágrafos presentes na Edição Final |
| `node tests/v4_flows_qa.js` (1440×900 e 390×844) | Átrio, leitor, Atlas com lugar, Acervo com lacre, Cena do Farol, Observatório, retrato: 0 erros de console |
| Larguras 320, 375 (movimento reduzido), 430, 768, 1024, 1920 × 11 rotas | sem rolagem horizontal, sem controles sem nome, pontos de luz alcançáveis por teclado |
| Migração v4 → Edição Final | progresso, posição e destaque reaparecem no mesmo parágrafo do novo capítulo |
| Trailer | 63 s, H.264/AAC 1920×1080, 7,6 MB; quadros-chave inspecionados |
| `node --check` em todos os módulos | OK |

## Não verificado
- Lighthouse, LCP/CLS/INP e uso de memória: não medidos.
- Dispositivos físicos (Android/iOS), instalação PWA e modo offline em aparelho.
- Áudio em navegador com política de autoplay real (apenas lógica de controles testada).
- Leitores de tela (só estrutura: rótulos, foco, ordem de tabulação).

## Pendências editoriais
- Transcrições dos fac-símiles: extraídas do PDF da v4, ainda "em revisão".
- Oito pranchas avulsas sem capítulo confirmado (editar `content/plates.json` para posicioná-las).
- Nomes dos retratos atribuídos por leitura das fichas; conferir.
- Fonte *Cartas do Norte Oficial*: o "í" sai sem acento; fonte *Display*: a vírgula é desenhada como dois-pontos. O site usa a Display com vírgula e ponto e vírgula da Cormorant.
