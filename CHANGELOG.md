# Histórico de versões do Arquivo Vivo

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
