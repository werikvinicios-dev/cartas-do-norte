# Vídeo promocional em motion graphics (32,6 s)

Arquivos finais: `assets/video/promo-30s.mp4` (16:9, 1920×1080) e `assets/video/promo-30s-vertical.mp4` (9:16, 1080×1920), 30 fps, 32,6 s.

O emblema da abertura é o original separado em camadas por `tools/promo/split_emblem.py` (aro, pontos cardeais, estrela, montanhas, pássaros, "CARTAS", "do", "NORTE", mar), em `tools/promo/emblem/`. Empilhadas, as camadas reproduzem o emblema pixel a pixel.

| Tempo | Cena | Movimento |
|---|---|---|
| 0–7,3 s | O emblema se monta | o aro se desenha no sentido horário; N, L, S, O; a estrela abre girando e o raio sul sobe; as montanhas e as árvores sobem, os pássaros chegam; "CARTAS" e "NORTE" são escritos da esquerda para a direita, "do" entre eles; o mar se abre do centro; um brilho atravessa o emblema; "Uma jornada entre a névoa, o mar e a graça" |
| 7,3–12,4 s | A carta | o envelope sobe, o lacre carimba, o contador vai de 1 a 12, o lacre se parte, a aba abre e a folha mostra "Miqueias," (cap. 3) |
| 12,4–17,6 s | O Atlas | a câmera aproxima a primeira carta náutica e a rota passa por Porto da Vigília, Farol da Vigília, Ponta do Corvo e Canal da Agulha |
| 17,6–22,7 s | Mosaico | entrada da bateria: aquarelas da Parte I e do começo da Parte II em faixas que deslizam; 72 capítulos, 54 aquarelas, 12 cartas no tempo da música |
| 22,7–27,9 s | O site | notebook e celular com telas reais do Arquivo Vivo (átrio, leitura, carta lacrada, painel de som) |
| 27,9–32,6 s | Emblema | o emblema se abre num círculo de luz; "Um romance de Werik Martins"; "Entre no Arquivo Vivo" |

Cortes no compasso da faixa (70 bpm, 3 tempos): uma cortina dourada atravessa a tela a cada troca. Sem flashes nem tremor; nada além da Parte II.

Refazer:

```sh
python3 -m http.server 8765 &                                   # na raiz do repositório
node tools/promo/render_promo.js 1920 1080 /tmp/h.mp4
node tools/promo/render_promo.js 1080 1920 /tmp/v.mp4
python3 tools/promo/promo_som.py <amazing-grace-lofi.mp3> /tmp/a.wav
ffmpeg -i /tmp/h.mp4 -i /tmp/a.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1.5 -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart assets/video/promo-30s.mp4
```

`node tools/promo/render_promo.js 1920 1080 --frames <pasta> 2.8,9.6,16.6` grava quadros soltos para revisão.
As telas do site ficam em `tools/promo/shots/` (capturas de 1440×900 e 390×844).

A faixa "Amazing Grace (lofi instrumental)", de The Lofi Christian, foi enviada pelo autor e não está no repositório; confirme a licença antes de publicar.
