# Cartas do Norte — direção de arte da Edição Imersiva v0.3

## Visão

O arquivo agora funciona como uma visita editorial, não como um dashboard: Átrio panorâmico → retomada discreta → salas da coleção com composição assimétrica → quatro partes canônicas → carta cartográfica segura → coleção de vestígios → retorno à leitura. A hierarquia não apresenta material narrativo novo.

## Decisões

- **Átrio widescreen:** panorama panorâmico de uma aquarela de capa já aprovada, recomposta fotograficamente para telas amplas; nenhum relevo ou localidade nova foi desenhado. Letras oficiais são preservadas no SVG de marca. A atmosfera dinâmica usa o vídeo já produzido e possui fallback estático.
- **Galeria das salas:** um painel monumental dedicado ao romance e três salas menores; cada interação tem destino funcional.
- **Cartografia segura:** antes do desbloqueio é mostrado um frontispício ornamental derivado apenas de ativos editoriais aprovados, sem um mapa com localidades futuras. Após o desbloqueio, a imagem de mapa vem do catálogo canônico.
- **Ritmo editorial:** alternância intencional entre azul-marinho profundo e papel aquecido, com margens largas e títulos serifados, reduzindo grids repetitivas.
- **Movimento:** revelação progressiva em viewport, microelevação dos links e panorama lento em telas grandes. Não há animação essencial; `prefers-reduced-motion` e a preferência interna desligam transições.
- **Leitor:** continua separado do espetáculo; controles de índice, anotações, fonte, marcações, posição e tema permanecem disponíveis.
- **Áudio/vídeo:** dois MP4 e três OGG originais da v0.2 permanecem incorporados; som só começa por ação explícita e é pausado antes do vídeo de abertura.
- **Sem spoilers:** dados canônicos e desbloqueio do Atlas/Acervo/Galeria permanecem centralizados em `catalog.json` e no progresso do leitor.

## Principais arquivos de interface

- `src/premium.css`: nova linguagem visual e quatro escalas responsivas.
- `src/experience.js`: coordena observação de conteúdo na rolagem sem substituir navegação.
- `src/main.js`: novo Átrio renderizado em seções sem alterar os arquivos de romance.
- `assets/experience/hero-panorama.webp`: derivação panorâmica de pintura de capa oficial.
- `assets/experience/edition-paper.webp`: fundo editorial de Parte I aprovada.
- `assets/experience/archive-frontispiece.webp`: montagem ornamental de imagem aprovada e bússola aprovada; não é mapa canônico nem documento original.

## Próxima homologação

Ambas as escalas desktop e mobile foram inspecionadas por capturas de Chromium com fonte real de CSS e JavaScript, mas um mecanismo de testes isolado (sem URLs/rede acessíveis). Ainda são necessários ensaios com HTTPS, Service Worker, IndexedDB persistente, controles de mídia em aparelhos e revisão humana das transcrições extraídas do PDF.
