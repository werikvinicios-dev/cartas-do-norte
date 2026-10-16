# Registro de qualidade — Arquivo Vivo v0.3

**Estado global: IMPLEMENTADO E TESTADO PARCIALMENTE — NÃO HOMOLOGADO PARA LANÇAMENTO.**

**Data:** 15/10/2026. **Fonte editorial:** Edição de Colecionador v4 aprovada.

## O que passou

| Subsistema | Estado verificado | Evidências |
|---|---|---|
| Novo Átrio panorâmico / seis sequências editoriais | TESTADO em harness | 320, 390, 768 e 1440 px; sem overflow horizontal |
| Menu desktop e navegação mobile | TESTADO em harness | barra mobile em 5 colunas; navegação funcional nas rotas |
| Leitura integral | TESTADO em harness | 67 unidades; 53 capítulos conferidos com a produção v4 |
| Sumário, marcadores, notas e tema noturno | TESTADO em harness | ações de interface e armazenamento em memória simulado |
| Busca e proteção de spoilers | TESTADO em harness | busca filtrada; cartas e mapas preservados antes do avanço |
| Atlas, Acervo, Galeria e Observatório | TESTADO em harness | abrir, ampliar, descobrir e retornar; recursos em fontes aprovadas |
| Vídeo panorâmico + filme de abertura | ARQUIVO REAL, PLAYERS TESTADOS | 12 s MP4 sem som; 18 s MP4 com áudio; codecs inspecionados |
| Som ambiente | ARQUIVO REAL, CONTROLES TESTADOS | mar/chuva/vento em OGG, 24 s cada; volume e pausa |
| Novas transições e revelações de rolagem | IMPLEMENTADO / NÃO HOMOLOGADO EM APARELHO | CSS, observador, alternativa de movimento reduzido |
| PWA e cache offline | IMPLEMENTADO / NÃO HOMOLOGADO EM APARELHO | cache shell atualizado para versão 0.3; testes reais pendentes |
| Integridade editorial | TESTADO AUTOMATICAMENTE | 22/22 verificações; capítulos idênticos aos blocos aprovados |
| Interface (ação e responsividade) | TESTADO EM HARNESS | 98/98 verificações em 4 formatos, Chromium headless |

## Testes reproduzíveis

- `python tests/integrity_qa.py` — integridade das 67 unidades de leitura, referências a imagens, hashes, presença do acervo e comparação textual dos 53 capítulos.
- `python tests/refined_ui_qa.py` — interface real carregada via `page.set_content` em Chromium, com `content/catalog.json` e `content/reading/*.json` verdadeiros injetados em memória; exercita ações e captura imagens de tela de quatro resoluções.
- `node --check src/main.js`, `src/experience.js`, `src/db.js`, `src/content.js`, `src/ambience.js` e `sw.js` — sintaxe JavaScript.
- `ffprobe` nos dois MP4 e nos três OGG — formato e duração.

## Limitações explícitas

O ambiente de Chromium usado recusou URLs, inclusive `localhost`, com `ERR_BLOCKED_BY_ADMINISTRATOR`. Por isso, o harness verifica **as telas, scripts e fluxos com dados editoriais reais**, mas não verifica HTTP real, IndexedDB persistente, permissões de áudio, Service Worker ou instalação no aparelho. Não há nota Lighthouse nem certificação WCAG 2.2 AA.

Ainda exigem revisão humana: divisão em parágrafos do prólogo, das 12 cartas e do epílogo importados do PDF; texto de transcrições acessíveis dos fac-símiles; contraste, controle de foco, desenho final das imagens e áudio em dispositivos físicos.

**Critério editorial:** os materiais cenográficos introduzidos na interface são derivados de imagens aprovadas e não representam novas localidades ou novos acontecimentos canônicos. A narrativa não foi editada por esta reconstrução.
