# Histórico de versões do Arquivo Vivo

## v0.10 · 16 de outubro de 2026 — Graça
- **Música de leitura "Graça"** no painel de som: variações de Amazing Grace ao piano (introdução em arpejos; melodia simples; melodia uma oitava acima com apojaturas e violoncelo; melodia no tenor sob arpejos agudos; coda). 2 min 46 s, em repetição sem emenda (a reverberação do fim cai sobre o início), −22 LUFS para não competir com o texto. `tools/musica_leitura.py`.
- **Trilha do trailer:** o hino está mais presente e mais agudo, com piano clássico. No ato I o violoncelo sobe uma oitava, com o piano dobrando. O ato II cita o hino em menor. No ato IV a melodia vem uma oitava acima, com apojaturas, terças, mão esquerda em baixo de Alberti e acorde final arpejado. Os vídeos ainda usam a trilha anterior: serão remontados depois da aprovação do som.

## v0.9 · 16 de outubro de 2026 — Trailer oficial "Uma aquarela que respira"
- Trailer refeito a partir do prompt mestre, em 7 sequências e 80 s (16:9, 24 fps): o mar se lembra; o funeral do faroleiro; o que ficou para trás; a travessia; o peso do passado; o silêncio antes da luz; o nome da história. Sem narração: as frases aparecem na tela, com fade, revelação por máscara e movimento mínimo.
- Acervo analisado antes da montagem (`docs/trailer/STORYBOARD.md` e `storyboard.jpg`): farol sempre apagado antes do desfecho (cap. 1), a Constância do cap. 22, o testamento do cap. 2, nada da segunda metade.
- Animação só atmosférica (chuva, névoa, água, luz, folha fora de foco, transição em pigmento). Sem flashes, glitch ou tremor.
- Trilha original em quatro atos (memória, travessia, confronto, esperança) com foley de madeira, papel, vento e mar, silêncio antes da luz e último acorde suspenso. −14 LUFS, sem clipping.
- Entregas: principal 80 s, vertical 9:16 (usada no celular), 30 s, teaser 15 s, SRT/VTT, pôster, storyboard e relatório (`docs/trailer/RELATORIO.md`).

## v0.8 · 16 de outubro de 2026 — Trailer de impacto
- **Trailer remontado (68 s, 24 fps, janela 2,39:1)** em `tools/build_trailer_v3.py`, sem narração: tipografia em golpe (as palavras caem e assentam com clarão, tremor e aberração cromática), frases escritas como tinta, lacre que se parte, mapa revelado em tinta, montagem que acelera com as grandes pranchas panorâmicas e aquarelas de todo o livro, tempestade com cortes de meio segundo, **mergulho subaquático** com a frase da Carta I ("Havia gente trancada onde os registros diziam que só existiam caixas."), **"UMA PAUSA" congela no preto**, "OUTRAS TRÊS" e três clarões até o emblema.
- **Trilha e desenho de som** (`tools/trailer_sound_v3.py`): pulsos graves, braams, tambores a 120 bpm, cordas e coro, trovões, **gritos de socorro distantes** na tempestade e, no mergulho, tudo abafado com bolhas, borbulhar, coração acelerado e gritos submersos; silêncio absoluto na pausa; final em ré maior. Masterização −14 LUFS.
- Legenda CC continua opcional (desligada por padrão) e acompanha o texto da tela.

## v0.7 · 16 de outubro de 2026 — Cartas de verdade e trailer narrado
- **Cartas como objetos:** as 12 cartas e 8 escritos dentro dos capítulos (declaração e carta de Jonas, a folha sobre os objetos, notas nos desenhos, o bilhete, a carta de Lídia, a resposta de Ana, o bilhete de Gabriel) aparecem na leitura como envelopes lacrados ou folhas de papel antigo. O lacre de cera se parte, a aba se abre, a carta sai do envelope e se desdobra. Tipografia como no livro: itálico Charis (família Charter, a mesma da Edição Final), justificado, rubrica "CARTA I" em ferrugem, destinatário em azul; assinatura em caligrafia. Som discreto de lacre e papel (desligável).
- **Acervo · Correspondência:** cada carta entra no Acervo quando é aberta na leitura (ou quando o capítulo é concluído), com leitura em papel e link de volta ao trecho. As demais aparecem lacradas, sem revelar conteúdo.
- **Trailer com narração e trilha nova, sem legendas na imagem:** narração em voz neural natural (Kokoro, pm_alex, Apache 2.0) tratada como locução de estúdio; trilha original em ré menor em cinco movimentos (piano e cordas, ostinato e coro, tempestade em tutti com silêncio absoluto na "pausa", final em ré maior); música rebaixada sob a voz; masterização a −14 LUFS. Legenda opcional (`trailer.vtt`) desligada por padrão.
- Correção: a lista de arquivos carregados na abertura incluía uma imagem por engano.

## v0.6 · 16 de outubro de 2026 — Nova direção "Noite de vigília"
- **Design refeito do zero** (`src/ui.css`, uma única folha): noite do mar como fundo, o dourado do farol como único acento, papel apenas para ler. As três folhas herdadas (styles/refined/premium) e `experience.js` foram removidas.
- **Átrio em atos guiados pela rolagem** (`src/motion.js`, rolagem nativa, sem sequestro): I. a costa — a cena viva aproxima o farol e escurece; II. a primeira luz — as frases do prólogo surgem uma a uma, o farol pulsa três vezes, a segunda luz acende em vermelho; depois *Ler · Explorar · Sentir* em painéis que se expandem, as doze cartas como envelopes lacrados que se abrem com a leitura, as salas com contadores do seu progresso e o trailer em janela de cinema.
- **Navegação nova:** barra que se recolhe ao descer e mostra "Continuar" com o ponto exato da leitura; menu em tela cheia com prévia de imagem; dock inferior no celular.
- **Biblioteca** com capas de capítulo (aquarela de cada capítulo), seções por Parte com arte própria, frontispício. **Acervo** como mesa do arquivista. **Galeria** em colunas.
- **Trailer de 90 s** reconstruído (`tools/build_trailer_v2.py`): janela 2,39:1, três atos, facho volumétrico, chuva, relâmpagos, tremor de câmera, chicotes, revelação em tinta, emblema num feixe de luz; trilha original sintetizada (drones, impactos, risers, tambores, sinos, piano) com as ambiências da edição.
- Vestígios: correspondência de capítulos recalculada só com parágrafos únicos (a transmissão de Balu abria cedo demais).
- Fonte oficial restrita a letras e números (a pontuação do arquivo está deslocada).

## v0.5 · 16 de outubro de 2026 — Edição Final e identidade oficial
- **Texto da Edição Final do autor** (`sources/Cartas_do_Norte_Edicao_Final.docx`): prólogo, 72 capítulos, 12 cartas e epílogo (86 unidades). Itálicos do autor exibidos no leitor. Corrige resíduos da extração do PDF da v4 (rótulos de mapa dentro da Carta I, cartas duplicadas dentro de capítulos). Detalhes em `docs/RELATORIO_EDICAO_FINAL.md`.
- **Migração automática** do progresso, marcadores, destaques e notas salvos na v4 para a nova numeração, parágrafo a parágrafo (`content/migration-v4.json`).
- Aquarelas, vestígios e pranchas transferidos para os capítulos correspondentes da Edição Final.
- **Pranchas no texto:** cinco ilustrações aparecem dentro do capítulo, na passagem que mostram (lanternas de papel, baleias, primeiros sinos, manivela da lente, três pulsações); oito pranchas avulsas na Galeria, liberadas após o epílogo até que o capítulo seja identificado. Capítulo 37 em alta.
- **Identidade oficial:** emblema (versões ouro e azul) no Átrio, no frontispício e nos ícones do aplicativo; fonte oficial *Cartas do Norte Display* nos títulos; paleta do script de identidade v5.
- **Frontispício** na Biblioteca com moldura ilustrada, epígrafe (Hebreus 6:19) e dedicatória da Edição Final.
- Papel envelhecido nas cartas.

## v0.4 · 16 de outubro de 2026 — Reconstrução imersiva
- **Átrio como Cena Viva:** a aquarela da capa vira plano de câmera, com abertura em movimento (do céu ao mar), paralaxe pelo ponteiro, arrasto no celular, névoa em duas profundidades, luzes do porto e o farol pulsando três vezes, como no prólogo.
- **Pontos de luz reais:** farol → Cena do Farol; barco → leitura; costa → Atlas. Bússola funciona como instrumento de navegação (rosa dos ventos).
- **Cena Viva do Farol** (`#/cena/farol`) com os trechos do romance que citam o Farol da Vigília, só dos trechos já lidos.
- **Leitor editorial:** página de abertura de cada Parte com a aquarela oficial, abertura cinematográfica do capítulo (página dupla no desktop), aquarela viva (respiração, névoa; chuva no capítulo 1), folha própria para as cartas, modos Livro ilustrado e Foco.
- **Vestígios:** fim de capítulo com estante de vestígios (lacrados até a conclusão) e lugares citados; descoberta registrada com data e capítulo de origem.
- **Acervo:** visualizador de tela cheia com pinça, arrasto, roda e teclado; materialidade por tipo documental; lacre de cera que se abre (pulável); fac-símile e transcrição lado a lado (abas no celular); retorno ao mesmo ponto da leitura.
- **Atlas:** mapa ampliável com marcas sobre os nomes impressos; escolher um lugar aproxima a carta do rótulo e mostra os trechos lidos que o citam; histórico de lugares visitados.
- **Observatório:** progresso por Parte, coleção de vestígios com data, lugares conhecidos, personagens pela primeira menção, marcas recentes.
- **Trailer de 63 s** (1920×1080, H.264/AAC, legendas VTT) montado com aquarelas aprovadas e frases literais do prólogo e dos capítulos 1 e 3; trilha original sintetizada + ambiências da edição. Substitui a abertura de 18 s.
- **Tipografia:** Cormorant Garamond (display) e Newsreader (leitura), auto-hospedadas.
- **Anti-spoiler na arquitetura:** transcrições saíram do catálogo e só são carregadas quando o vestígio está liberado; lugares e pessoas têm a primeira menção calculada a partir do texto (`content/places.json`, `content/people.json`).
- Removidos `atrio-loop.mp4`, `abertura.mp4` e o panorama com preenchimento desfocado.
- **Ilustrações do autor:** prólogo ganhou aquarela própria; capítulos 1–36 e 38–53 substituídos pelas versões em alta (1024×1536); prancha avulsa na Galeria (após o epílogo).
- **Retratos:** 12 personagens com retrato; ficha com figura inteira para Miguel, Clara, Balu e Davi; assinatura de Jonas Vale. Observatório abre o retrato com os trechos lidos que citam o nome.
- Texto do romance inalterado: hashes das 67 unidades conferidos.

## v0.3 · 15 de outubro de 2026
- Remodelação visual do Átrio em tela ampla, com paisagem derivada da aquarela oficial.
- Navegação horizontal premium em desktop e navegação inferior corrigida para smartphones.
- Nova composição das salas: Biblioteca em destaque, Atlas, Acervo e Galeria.
- Percurso editorial das quatro partes da obra sem revelar acontecimentos.
- Ambientação cartográfica sem geografia inventada, com desbloqueio progressivo preservado.
- Transições de entrada e rolagem opcionais, desativadas por movimento reduzido.
- Atualização do cache PWA para incluir recursos e código da edição v0.3.
- Sem alterações em content/reading, content/catalog ou nos 53 capítulos aprovados.
- 22 verificações editoriais e 98 verificações de interface aprovadas em ambiente simulado.

## v0.2 · 15 de outubro de 2026
- Átrio cinematográfico anterior; três paisagens sonoras, dois vídeos e galeria de aquarelas.

## v0.1 · 15 de outubro de 2026
- Fundação editorial, leitor e módulos de exploração.
