#!/bin/sh
# Tarefa 15 (parte 1): recolore o pato (azul-esverdeado -> amarelo) com ImageMagick, corta os quadros de 64x64
# e salva em assets/pato_<animação>_<n>.png, todos com o mesmo recorte (36x31 a partir de 13,17), pés no fundo.
# Rodar:  sh tools/t15_pato_sprites.sh [pasta dos spritesheets]
SRC="${1:-$HOME/Game/duck/Ducky/Spritesheets}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
magick -size 1x1 xc:'rgb(40,25,0)' xc:'rgb(70,45,0)' xc:'rgb(190,130,0)' xc:'rgb(245,190,5)' xc:'rgb(253,215,20)' xc:'rgb(255,232,70)' xc:'rgb(255,248,140)' +append -filter triangle -resize 256x1! "$T/clut.png"
for a in idle walk jump fall hit death; do
  in="$SRC/$a.png"
  # máscara: só os pixels azul-esverdeados (matiz entre 38% e 62%) e opacos; bico e pés (marrom) ficam de fora
  magick "$in" -colorspace HSL -channel R -separate +channel \( -clone 0 -threshold 38% \) \( -clone 0 -threshold 62% -negate \) -delete 0 -compose multiply -composite "$T/h.png"
  magick "$in" -alpha extract "$T/a.png"
  magick "$T/h.png" "$T/a.png" -compose multiply -composite "$T/m.png"
  # corpo: luminância -> rampa de amarelo; resto: mais saturado (bico e pés laranja)
  magick "$in" -alpha off -colorspace Gray -level 0,60% "$T/clut.png" -clut "$T/yel.png"
  magick "$in" -modulate 100,175,100 "$T/orange.png"
  magick "$T/orange.png" "$T/yel.png" "$T/m.png" -composite -alpha off "$in" -compose CopyOpacity -composite "$T/$a.png"
  magick "$T/$a.png" -crop 64x64 +repage -background none "$T/${a}_%d.png"
done
for f in "$T"/*_[0-9].png; do
  [ "$(magick "$f" -format '%[fx:mean.a]' info:)" = "0" ] && continue   # quadro vazio
  magick "$f" -crop 36x31+13+17 +repage "$ROOT/assets/pato_$(basename "$f")"
done
rm -rf "$T"
