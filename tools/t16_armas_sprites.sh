#!/bin/sh
# Tarefa 16 (parte 1): sprites das armas novas (pasta ~/Game) -> assets/arma_*.png, ícones do HUD e slots 1-4.
# gun_013 = pistola, Shotgun = doze, gun_017 = minigun, gun_016 = lança-granadas (arma nova).
# Rodar:  sh tools/t16_armas_sprites.sh [pasta das armas]
SRC="${1:-$HOME/Game}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
A="$ROOT/assets"
for par in pistola:gun_013 doze:Shotgun minigun:gun_017 lanca:gun_016; do
  n=${par%%:*}; f=${par##*:}
  magick "$SRC/$f.png" -depth 8 -trim +repage "$A/arma_$n.png"
done
for n in pistola doze minigun lanca; do
  w=$(magick identify -format %w "$A/arma_$n.png"); h=$(magick identify -format %h "$A/arma_$n.png")
  k=$(python3 -c "print(max(1, min(140//$w, 50//$h)))")   # escala inteira: pixel art nítido
  magick "$A/arma_$n.png" -alpha extract -threshold 50% -filter point -scale $((k*100))% -background black -gravity center -extent 150x56 "$A/.m.png"
  magick -size 150x56 xc:white "$A/.m.png" -alpha off -compose CopyOpacity -composite "$A/hud/arma_$n.png"
  # ícone do HUD: silhueta branca que cabe em 150x56
done
# moldes: as molduras dos slots originais (guardadas na 1ª execução, para rodar de novo sem perder a borda)
MOLDE="$ROOT/tools/molde_slots"
[ -d "$MOLDE" ] || { mkdir -p "$MOLDE"; cp "$A"/hud/slot_[123].png "$A"/hud/slot_3_sel.png "$MOLDE"/; }
n=0
for nome in pistola doze minigun lanca; do
  n=$((n+1))
  base="$MOLDE/slot_${n}.png"; [ "$n" = 4 ] && base="$MOLDE/slot_3.png"
  # moldura: a original sem o miolo (borda de 4 px); miolo novo com o ícone
  magick "$A/arma_$nome.png" -alpha extract -filter lanczos -resize 34x16 -background black -gravity center -extent 52x34 "$A/.s.png"
  magick "$base" \( -size 52x34 xc:none -fill white -draw "rectangle 4,4 47,29" \) -compose DstOut -composite "$A/.moldura.png"
  magick -size 52x34 xc:'rgba(191,191,191,0.56)' "$A/.s.png" -alpha off -compose CopyOpacity -composite "$A/.ic.png"
  magick "$A/.moldura.png" "$A/.ic.png" -compose over -composite "$A/hud/slot_${n}.png"
  magick "$MOLDE/slot_3_sel.png" -fill 'rgba(255,255,255,0.917647)' -draw "rectangle 4,4 47,29" "$A/.molsel.png"
  magick -size 52x34 xc:'rgb(17,17,17)' "$A/.s.png" -alpha off -compose CopyOpacity -composite "$A/.ics.png"
  magick "$A/.molsel.png" "$A/.ics.png" -compose over -composite "$A/hud/slot_${n}_sel.png"
done
cp "$A/hud/slot_3_lock.png" "$A/hud/slot_4_lock.png"
cp "$A/hud/pip_doze.png" "$A/hud/pip_lanca.png"
rm -f "$A"/.m.png "$A"/.s.png "$A"/.moldura.png "$A"/.ic.png "$A"/.molsel.png "$A"/.ics.png
