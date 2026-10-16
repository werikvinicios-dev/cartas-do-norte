# Relatório de produção — Trailer oficial

## Entregues (`assets/video/`)
| Arquivo | Conteúdo |
|---|---|
| `trailer.mp4` | **Principal**, 80 s, 1920×1080, 24 fps, H.264 + AAC 48 kHz estéreo, −14 LUFS, pico −1 dBTP. Sem narração; as frases aparecem na tela. É o que o site exibe. |
| `trailer-vertical.mp4` | 9:16 (1080×1920), mesmo filme com enquadramentos e textos refeitos para a vertical, não cortados do 16:9. O site usa esta versão em celulares na vertical. |
| `trailer-30s.mp4` | Versão reduzida de 30 s. |
| `trailer-15s.mp4` | Teaser de 15 s. |
| `trailer.srt` / `trailer.vtt` | Texto em tela com tempos. No site a legenda é opcional (CC desligado por padrão). |
| `trailer-poster.webp` | Pôster (quadro do emblema com subtítulo). |
| `docs/trailer/STORYBOARD.md` + `storyboard.jpg` | Análise do acervo, escolhas, planos com tempo, movimento, texto e som. |

Projeto editável: `tools/trailer_oficial.py` (imagem; `TRAILER_W/TRAILER_H` definem 16:9 ou 9:16), `tools/trailer_oficial_som.py` (trilha e som; `--narrado` gera, se um dia for útil, uma variante com voz sintética, fora do repositório) e `tools/trailer_cortes.py` (30 s e 15 s).

## Decisões
- **Farol apagado:** o capítulo 1 diz que "a torre estava apagada havia dezessete anos". A capa (farol aceso) e a prancha "três pulsações" (farol reaceso) ficaram de fora. O farol é a aquarela isolada da edição, sem luz, composta sobre céu e mar da prancha da Parte II e identificada como composição atmosférica.
- **Constância:** a embarcação é a do capítulo 22 ("A Constância deixara a Ilha do Sino").
- **Sem spoilers:** apenas a Parte I e o início da II, a prancha de abertura da Parte IV (paisagem sem pessoas) e uma prancha avulsa usada só pelo detalhe da mão e do relógio.
- **Animação:** nada na pintura é deformado. Chuva, névoa, ondulação abaixo da linha d'água, luz, brilho na bússola e uma folha fora de foco são camadas próprias. A câmera se move pouco. Sem flashes, glitch ou tremor.
- **Frases:** são texto publicitário do roteiro, não citações do romance.
- **Trilha original** em ré menor que resolve em ré maior. Instrumentos sintetizados; mar, vento e chuva são as ambiências originais da edição. A sequência V tem gritos muito distantes, filtrados, sob o mar escuro (pedido anterior), em nível baixo; para tirar, apague o bloco `cries` em `trailer_oficial_som.py`.

## Limitações
- **4K:** não renderizado. As aquarelas originais têm no máximo 1536 px; em 3840×2160 elas seriam só ampliadas, sem ganho de detalhe, e o render passaria de algumas horas neste ambiente. A matriz é 1920×1080.
- **Instrumentos sintetizados:** não são uma orquestra gravada. O resultado é limpo e dinâmico, mas tem timbre de sintetizador nas cordas.
- **Parallax 2.5D real:** exigiria separar camadas de cada aquarela à mão. Para não deformar as pinturas, o movimento ficou na câmera mínima e nas camadas atmosféricas.
- **Revisão:** feita por quadros-chave e por medição de volume. Não foi feita em monitor calibrado nem em fones de referência.
