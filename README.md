# Cartas do Norte — O Arquivo Vivo

**Edição Imersiva v0.6 · Direção "Noite de vigília" · 16 de outubro de 2026**

Texto: Edição Final (72 capítulos), reconstruída com `python3 tools/build_final_edition.py sources/Cartas_do_Norte_Edicao_Final.docx`. Atenção: a pasta `sources/` vai junto se o site for publicado inteiro; remova-a da hospedagem se não quiser o .docx público.

Novidades em `CHANGELOG.md`; sistema visual em `docs/design-system.md`; estado de QA em `docs/QA_V4.md`.

Uma aplicação literária responsiva com a obra integral, Atlas, Acervo, Galeria, Observatório, som opcional, filme audiovisual, experiências visuais amplas e leitor confiável. Esta versão utiliza a **Edição de Colecionador v4 aprovada** como fonte de verdade editorial.

## Começar

**No computador**: extraia o ZIP mantendo a estrutura de diretórios, abra um terminal dentro da pasta com `index.html`, execute `python -m http.server 8765` (ou `python3`) e navegue até `http://localhost:8765/#/atrio`.

**No celular Android**: publique **a pasta inteira** em uma hospedagem estática HTTPS, preservando a organização dos diretórios, e abra a URL pelo navegador. O site está pronto para ser servido na **raiz** de um domínio; não está pronto para abrir todos os recursos por `file://` ou para hospedagem direta em uma subpasta. O navegador pode oferecer a ação de adicionar à tela inicial, dependendo do ambiente.

**Importante:** este ZIP não é APK, não é um serviço online já publicado e não contém backend; a aplicação usa armazenamento local e recursos embutidos. Não precisa de banco de dados remoto nem de fontes externas.

## Caminho do visitante

1. **Átrio panorâmico** com a marca oficial, uma pintura panorâmica derivada da capa aprovada, vídeo opcional, ações de leitura e revelação das salas.
2. **A Biblioteca** com prólogo, 53 capítulos, 12 cartas e epílogo em ordem canônica, sem bloqueio da leitura.
3. **O Leitor** com sumário, fonte ajustável, três temas, posições estáveis por bloco, marcadores, destaques, anotações locais, busca e retorno ao ponto de leitura.
4. **O Atlas** com 7 mapas oficiais progressivos e um frontispício ornamental seguro antes do desbloqueio.
5. **O Acervo** com 11 fac-símiles oficiais, ampliação, origem identificada e transcrições extraídas para revisão editorial.
6. **Galeria e Observatório** com aquarelas, vestígios e nomes liberados conforme progresso.

## Imersão opt-in

- **Trailer:** `assets/video/trailer.mp4` — 68 s, 1920×1080 (janela 2,39:1), 24 fps, H.264/AAC, legenda opcional em `trailer.vtt`. Reproduzível com `python3 tools/build_trailer_v3.py` (imagem) + `tools/trailer_sound_v3.py` (som). Versões anteriores: `build_trailer_v2.py` (requer numpy, scipy, Pillow, fonttools, ffmpeg, kokoro-onnx + espeak-ng e o modelo Kokoro v1.0; trilha e narração em `tools/trailer_audio.py`). Cartas: `python3 tools/build_letters.py` gera `content/letters.json`.
- **Cenas Vivas:** Átrio e Farol (`src/scene.js`), sem vídeo de fundo; animações só com transform/opacity.
- **Som ambiental:** `assets/audio/mar.ogg`, `chuva.ogg` e `vento.ogg` — 24 s cada, repetição e volume configuráveis, sempre iniciados pelo usuário.
- **Movimento de interface:** surgimento progressivo no rolar, brilho discreto e escala leve em itens clicáveis; possui fallback completo sem efeitos.

## Preservação e privacidade

O texto foi mantido fora dos componentes em `content/reading/*.json`, com estrutura editorial em `content/catalog.json`. O sistema anti-spoiler respeita conclusão e nível de revelação; a leitura principal nunca é bloqueada. Progresso, marcadores, notas, ajustes e descobertas ficam em IndexedDB; as opções de som ficam em localStorage. Configurações permitem exportar, importar e apagar os dados do usuário.

## Arquitetura

```text
index.html                 entrada e navegação
src/styles.css             fundação editorial
src/refined.css            recursos de interação e layout v0.2
src/premium.css            reconstrução visual v0.3
src/main.js                rotas, leitor, Átrio, Atlas, Acervo, busca, privacidade
src/experience.js          aprimoramento progressivo e movimento acessível
src/ambience.js            controles do som
src/content.js             leitura sob demanda
src/db.js                  persistência IndexedDB
content/catalog.json      Biblioteca Mestra / metadados anti-spoiler
content/reading/*.json    romance em 67 unidades
assets/experience/         composições visuais derivadas das imagens aprovadas
assets/branding/           identidade original e ornamentos
assets/art/                imagens editoriais oficiais
assets/maps/               mapas oficiais
assets/docs/               fac-símiles oficiais
assets/audio/              3 sons originais
assets/video/              2 vídeos produzidos para a interface
sw.js                     service worker e cache versão 0.3
manifest.webmanifest       descrição de instalação PWA
tests/                    scripts e evidências
```

## Dados editoriais

A cópia oficial de leitura PDF v4 possui SHA-256 registrado `03f568445ae6825fcc51808cafcc9f79aa402c692dfc32f97b2c2ef179dd50f1`. A auditoria automática comparou os 53 capítulos com seus blocos estruturais da produção v4 e encontrou correspondência exata. Os limites de parágrafos do prólogo, cartas e epílogo, bem como transcrições de artefatos, ainda precisam de conferência humana antes de homologação editorial completa.

## Verificações técnicas

Execute `python tests/integrity_qa.py` e `python tests/refined_ui_qa.py` (este último requer Chromium + Playwright). Esta entrega passou **22/22 verificações de integridade** e **98/98 verificações de interface em ambiente simulado**, com larguras de 320, 390, 768 e 1440 px; isso **não substitui** testar PWA, áudio, rede, armazenamento persistente e acessibilidade em dispositivos reais. Veja `docs/QA_E_ESTADO.md` e `docs/DIRECAO_DE_ARTE_V3.md`.

**Fontes:** não distribuímos arquivos de fontes comerciais ou fontes originais; o lettering aprovado existe como contorno vetorial na marca.
