# Sistema de design — Arquivo Vivo v4

Fonte: `src/v4.css` (carregado depois das camadas v0.1–v0.3). Pesquisa de apoio feita com a skill `ui-ux-pro-max` (padrão *Scroll-Triggered Storytelling*, par tipográfico editorial). A paleta sugerida pela ferramenta (preto e rosa) foi descartada: as cores derivam das aquarelas aprovadas.

## Cores

| Token | Valor | Uso |
|---|---|---|
| `--abyss` | `#04131b` | fundo das cenas, visualizador |
| `--deep` / `--tide` | `#08202a` / `#0f2f39` | cabeçalhos de sala, Observatório |
| `--sea` | `#3d5f5c` | verde marítimo dessaturado (lugares visitados) |
| `--mist` | `#c9d1cf` | névoa |
| `--gold` / `--gold-hi` / `--gold-ox` | `#cdaa72` / `#e6cc9b` / `#9c7c45` | ação principal, rótulos, foco |
| `--ivory` / `--paper` | `#f5eddd` / `#efe3cb` | texto sobre escuro, salas de papel |
| `--sepia` / `--ink` | `#7d5f3c` / `#1f2724` | rótulos e texto sobre papel |

Contraste: texto corrido usa `--ink` sobre papel ou `--ivory` sobre `--abyss` (ambos acima de 12:1). Dourado (`--gold-hi`) só em rótulos curtos e títulos sobre fundo escuro.

## Tipografia

- **Marca:** `wordmark.svg` oficial (lettering vetorial). Não é substituída.
- **Display:** Cormorant Garamond 400/500/600 e itálico (títulos, cartões, rótulos de lugar).
- **Leitura:** Newsreader variável (eixos `opsz` e `wght`), desenhada para leitura longa.
- **Interface:** fonte do sistema, caixa alta espaçada só em rótulos de até 3 palavras.
- Fontes auto-hospedadas em `assets/fonts/` (SIL OFL 1.1, licenças ao lado). Sem CDN.

## Movimento

Três intenções: **presença** (névoa, luz do farol, aquarelas respirando), **descoberta** (pontos de luz, lacre que se abre, câmera que aproxima o mapa), **continuidade** (mergulho de câmera entre cena e destino).

- Só `transform` e `opacity` animam. Névoa e chuva são pseudo-elementos transladados, sem repintura.
- Curvas: `--ease` `cubic-bezier(.2,.7,.1,1)` para entradas; `--ease-cine` `cubic-bezier(.65,0,.35,1)` para câmera.
- Durações: microinterações 200–350 ms; câmera 550–650 ms; ambiente 7–90 s em loop sem corte (texturas periódicas).
- O farol pulsa três vezes por ciclo, como descrito no prólogo ("Três pulsações sobre o mar").
- Cenas e aquarelas pausam fora da tela (IntersectionObserver) e com a aba oculta.
- `prefers-reduced-motion` e a preferência "Transições suaves" desligam todas as animações; nada depende delas.
- Lacre: dura 1,5 s, tem botão "Abrir diretamente" e não aparece com movimento reduzido.

## Componentes

- **Cena Viva** (`src/scene.js`): pintura como plano de câmera, paralaxe por ponteiro, arrasto horizontal no toque, pontos de luz (`<a>` reais, 44 px), mergulho de câmera ao escolher.
- **Visualizador** (`src/panzoom.js`): pinça, arrasto, roda (com Ctrl no Atlas), duplo clique e teclado (+ − 0 setas). Usado em documentos, mapas e aquarelas.
- **Materialidade documental:** `.mat-<tipo>` (carta, diário, testamento, registro marítimo, registro, oficial, jurídico, manuscrito, prancha, transmissão, objeto, mapa).
- **Leitor:** página de abertura de parte, abertura cinematográfica com aquarela viva (página dupla a partir de 1000 px), folha de carta, estante de vestígios, lugares citados. Modos *Livro ilustrado* e *Foco*.

## Responsivo

Larguras testadas: 390 e 1440 px nesta rodada (320–1920 px na v0.3). Celular: cena ocupa 62–66 % da altura, texto abaixo, navegação inferior com cinco destinos ao alcance do polegar. Desktop: cena à direita com 66 % da largura e texto à esquerda.
