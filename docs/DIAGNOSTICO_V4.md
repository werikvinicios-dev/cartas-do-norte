# Diagnóstico — ponto de partida da v4 (Fase 1)

Base analisada: Edição Imersiva v0.3 (JavaScript puro, ES modules, sem build, ~187 KB de código + ~14 MB de ativos).
Execução real: `python3 -m http.server` + Chromium (Playwright), 1440×900 e 390×844, sete rotas.

## O que já funciona (preservar)

- Texto do romance fora do código (`content/reading/*.json`, 67 unidades) e catálogo anti-spoiler (`content/catalog.json`).
- Leitor com sumário, marcadores, destaques, notas, busca, temas e posição por parágrafo (IndexedDB).
- Roteamento por hash, sem scroll horizontal em nenhuma das 7 rotas testadas, nas duas larguras.
- Atlas, Acervo, Galeria e Observatório funcionais com anti-spoiler por capítulo.
- PWA (manifest + service worker), áudio opt-in, vídeo de abertura opt-in.
- Marca oficial (`wordmark.svg`) e ativos aprovados.

## Limitações encontradas

| Área | Situação atual | Distância do prompt mestre |
|---|---|---|
| Átrio | Hero com panorama estático + rolagem de seções. Parece uma landing page elegante. | Falta profundidade por camadas, resposta ao ponteiro/toque, hotspots reais. |
| Cenas Vivas | Não existem. | Sistema inteiro a criar. |
| Leitor | Arte do capítulo é uma imagem pequena em coluna única; um só layout de página. | Faltam abertura cinematográfica, página dupla no desktop, tratamento distinto para cartas. |
| Acervo | Fac-símile num modal com zoom por botões. | Faltam materialidade por tipo documental, envelope/lacre, comparação fac-símile × transcrição. |
| Atlas | Imagem + botão "examinar" + lista de nomes. | Faltam zoom por gesto, pan, localidades interativas, vínculo com capítulos. |
| Vestígios | Lista simples no Observatório. | Faltam fonte, capítulo, momento de revelação e dependências por vestígio. |
| Observatório | Lista de nomes sem imagem nem relações. | Faltam páginas editoriais, linha do tempo documentada, galeria integrada. |
| Trailer | Montagem de aquarelas de 18 s. | Precisa de storyboard e direção própria. |
| Anti-spoiler | Aplicado nas telas (JS). Busca respeita o progresso. | Falta aplicar em miniaturas/descrições dos mapas e no próprio catálogo carregado. |
| Motion | Revelação por rolagem e hover. | Sem linguagem própria nem camadas animadas nas aquarelas. |

## Pendências técnicas

- `src/main.js` concentra ~58 KB em um arquivo (rotas, leitor, Átrio, Atlas, Acervo, busca, privacidade). Refatorar em módulos por ambiente antes de expandir.
- Três folhas de estilo sobrepostas (`styles.css`, `refined.css`, `premium.css`), com camadas de sobrescrita.
- `atrio-loop.mp4` falhou no Chromium headless deste ambiente (`requestfailed`). A causa não foi isolada: o servidor `python -m http.server` não suporta requisições `Range`, e o Chromium do Playwright pode não ter codec H.264. Testar com um servidor com `Range` e em navegador real antes de concluir.
- Transcrições dos documentos e divisão de parágrafos do prólogo, cartas e epílogo ainda exigem conferência humana (já registrado no QA da v0.3).
- Sem Lighthouse, sem teste em dispositivo físico, sem verificação WCAG formal.

## Decisão de stack

Manter JavaScript puro com ES modules (refatoração progressiva), como o prompt mestre pede ("escolha a tecnologia de acordo com o projeto existente"). Não migrar para React/Vite/Tailwind: o ganho não compensa o risco sobre um site que já passa nas verificações de integridade editorial. Reavaliar apenas se surgir necessidade concreta de build.

## Ordem proposta

1. Refatorar `main.js` em módulos por ambiente (sem mudar comportamento) e rodar `tests/integrity_qa.py` para provar que o texto não mudou.
2. Direção de arte e motion: tokens em `docs/design-system.md` (skills `ui-ux-pro-max` e `motion`).
3. Fatia vertical: Átrio em camadas → leitor com abertura cinematográfica → carta com transcrição → vestígio → retorno à leitura.
4. Atlas com zoom/pan por gesto e vínculos com capítulos.
5. Acervo com materialidade por tipo documental.
6. Cenas Vivas (apenas as com base suficiente nos materiais aprovados, p. ex. Farol da Vigília).
7. Trailer: storyboard primeiro; MP4 só se o ffmpeg do ambiente produzir qualidade aceitável.
8. QA com capturas reais, auditoria MotionScore e Lighthouse quando possível.
