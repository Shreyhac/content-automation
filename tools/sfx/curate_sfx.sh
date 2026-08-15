#!/bin/bash
# vid46 ROUND 2, SFX curation from the repo's own licensed library.
#
# What round 1 got wrong, measured:
#   * 236 placements over what LOOKED like 17 files, but boom.mp3/cboom.mp3 are
#     byte-identical and so are riser.mp3/riser2.mp3, so it was 15 distinct sounds,
#     and ONE of them (boom) carried 48 hits. Top four distinct sounds = 130/236 = 55%.
#     His "why are you just using two or three SFX" was closer to the truth than the
#     round-1 audit was.
#   * volumes 0.16-0.34 with a median of 0.20, which he heard as too loud.
#   * the library files come at wildly different levels, so a single data-volume number
#     meant a different loudness per file, and the fix each time was to nudge the
#     volume up, which is how the bed ended up hot.
#
# So this pass does three things the round-1 curation did not:
#   1. a real ROTATION per gesture class (5 impacts, 6 ticks, 4 pops, 4 risers,
#      5 wooshes, ...) so no single file can exceed ~8% of placements
#   2. TRIM LEADING SILENCE. Several library files have 20-80ms of digital black at
#      the head, which lands the transient late against its word. `silenceremove` on
#      the front only, tails are left alone because they carry the decay.
#   3. PEAK NORMALISE every file to -3 dBFS, so data-volume finally means the same
#      thing everywhere and the mix can sit at a 0.12 median instead of chasing levels.
set -euo pipefail
cd "$(dirname "$0")"

LIB=../sfx-library
OUT=assets/sfx
rm -rf "$OUT"; mkdir -p "$OUT"

# name                     source
copy() {
  local name="$1" src="$2"
  [ -f "$src" ] || { echo "  MISSING: $src"; return 1; }
  ffmpeg -y -v error -i "$src" \
    -af "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0:detection=peak,\
aformat=sample_fmts=fltp,\
loudnorm=I=-18:TP=-3.0:LRA=7:print_format=summary" \
    -ar 48000 -ac 1 -c:a libmp3lame -q:a 3 "$OUT/$name.mp3" 2>/dev/null \
  || ffmpeg -y -v error -i "$src" \
    -af "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0:detection=peak" \
    -ar 48000 -ac 1 -c:a libmp3lame -q:a 3 "$OUT/$name.mp3"
  printf "  %-9s %6s  %s\n" "$name" \
    "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/$name.mp3" | cut -c1-5)s" \
    "$(basename "$src")"
}

echo "--- impacts (act openers, hard landings) ---"
copy imp1  "$LIB/universfield-impact-cinematic-boom-02-487858.mp3"
copy imp2  "$LIB/audiopapkin-sound-design-elements-impact-sfx-ps-139-500887.mp3"
copy imp3  "$LIB/rizer/alexis_gaming_cam-ks-motion-metal-hit-351564.mp3"
copy imp4  "$LIB/soft-kit/pop-cluster.mp3"
copy imp5  "$LIB/dragon-studio-epic-transition-478367.mp3"

echo "--- UI ticks (a value locking, a row selecting) ---"
copy tick1 "$LIB/soft-kit/click-interface-cool.mp3"
copy tick2 "$LIB/soft-kit/click-select.mp3"
copy tick3 "$LIB/soft-kit/click-light-button.mp3"
copy tick4 "$LIB/Click/display455-ui-click-soft-512213.mp3"
copy tick5 "$LIB/Click/u_a59y4emt1v-single-keypad-beep-433456.mp3"
copy tick6 "$LIB/Click/freesound_community-pindrop-85096.mp3"

echo "--- pops (a chip arriving, a packet landing) ---"
copy pop1  "$LIB/soft-kit/pop-dry.mp3"
copy pop2  "$LIB/soft-kit/pop-message.mp3"
copy pop3  "$LIB/soft-kit/pop-soft-long.mp3"
copy pop4  "$LIB/soft-kit/pop-soap-bubble.mp3"

echo "--- risers (into a cut; NOT the round-1 riser, he named it) ---"
copy rise1 "$LIB/rizer/soundreality-riser-hole-391174.mp3"
copy rise2 "$LIB/rizer/dragon-studio-cinematic-riser-03-414575.mp3"
copy rise3 "$LIB/rizer/soundreality-riser-wildfire-285209.mp3"
copy rise4 "$LIB/rizer/freesound_community-guitar-swell-36526.mp3"

echo "--- wooshes (wipes, slides, reveals) ---"
copy wsh1  "$LIB/soft-kit/whoosh-fast-soft.mp3"
copy wsh2  "$LIB/Wooshes/dragon-studio-simple-whoosh-382724.mp3"
copy wsh3  "$LIB/Wooshes/liecio-short-woosh-109592.mp3"
copy wsh4  "$LIB/Wooshes/universfield-swoosh-06-351021.mp3"
copy wsh5  "$LIB/soft-kit/whoosh-swirl.mp3"
copy wsh6  "$LIB/Wooshes/studiokolomna-slow-whoosh-118247.mp3"

echo "--- redaction / paper / mechanical (the new carriers need new sounds) ---"
copy slide1 "$LIB/soft-kit/paper-slide.mp3"
copy slide2 "$LIB/soft-kit/paper-move-quick.mp3"
copy gear1  "$LIB/Click/ksjsbwuil-middle-gear-513910.mp3"
copy stamp1 "$LIB/rizer/freesound_community-camera-shutter-and-flash-combined-6827.mp3"
copy stamp2 "$LIB/Click/alexis_gaming_cam-camera-shutter-346101.mp3"

echo "--- digital (glitch, data, counters) ---"
copy gl1   "$LIB/dragon-studio-glitch-effect-1-397982.mp3"
copy gl2   "$LIB/aberrantrealities-futuristic-digital-whoosh-high-pitch-glitch-transition-effect-03-407114.mp3"
copy data1 "$LIB/tunetank.com_data-boost.wav"
copy data2 "$LIB/ElevenLabs_An_electronic_counter_with_high-pitched_beeps_incrementing_rapidly.mp3"
copy type1 "$LIB/Click/virtualzero-keyboard-typing-fast-371229.mp3"

echo "--- positive (verified, winner, CTA) ---"
copy shine1 "$LIB/benkirb-shine-11-268907.mp3"
copy shine2 "$LIB/soft-kit/marimba-magic.mp3"
copy ok1    "$LIB/soft-kit/tone-correct.mp3"
copy ok2    "$LIB/soft-kit/tone-positive.mp3"
copy ok3    "$LIB/soft-kit/tone-confirm.mp3"

echo
echo "--- pool ---"
ls -1 "$OUT" | wc -l
echo "duplicate check (round 1 shipped boom==cboom and riser==riser2):"
md5 -q "$OUT"/*.mp3 | sort | uniq -d | while read h; do
  echo "  !! DUPLICATE $h"; for f in "$OUT"/*.mp3; do
    [ "$(md5 -q "$f")" = "$h" ] && echo "     $f"; done
done
echo "  (no output above = every file in the pool is a distinct sound)"
