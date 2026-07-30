#!/bin/bash
# vid46 A-roll prep. Cuts the 4K master into the 8 chunk ranges at project encode
# settings, and renders one continuous cleaned VO master for assembly.
#
# Boundaries are frame-exact and every one lands on a word onset inside a >=0.20s gap
# (see vid46-breakdown.md). Frames: 907 922 910 917 849 884 852 954 = 7195.
set -euo pipefail
cd "$(dirname "$0")"

SRC="/Volumes/Shreyansh/nader new video/incogni edited.mp4"
OUT=assets/aroll
mkdir -p "$OUT"

# chunk  start_frame  end_frame
CHUNKS="c1:0:907 c2:907:1829 c3:1829:2739 c4:2739:3656 c5:3656:4505 c6:4505:5389 c7:5389:6241 c8:6241:7195"

echo "--- video chunks (silent; VO is muxed once at assembly) ---"
for spec in $CHUNKS; do
  IFS=: read -r name a b <<< "$spec"
  ss=$(awk -v f="$a" 'BEGIN{printf "%.6f", f/30}')
  du=$(awk -v a="$a" -v b="$b" 'BEGIN{printf "%.6f", (b-a)/30}')
  ffmpeg -y -v error -ss "$ss" -i "$SRC" -t "$du" \
    -an -vf "scale=3840:2160,setsar=1" -r 30 \
    -c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p \
    -g 15 -keyint_min 15 -movflags +faststart "$OUT/$name.mp4"
  n=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$OUT/$name.mp4")
  printf "  %-3s frames %4s (want %4s)  %s\n" "$name" "$n" "$((b-a))" "$(du -h "$OUT/$name.mp4" | cut -f1)"
done

echo "--- continuous cleaned VO master ---"
ffmpeg -y -v error -i "$SRC" -vn -ac 1 -ar 48000 \
  -af "highpass=f=75, afftdn=nr=14:nf=-28:tn=1, adeclick" \
  -c:a pcm_s16le assets/vo-master.wav
ffprobe -v error -show_entries format=duration -of csv=p=0 assets/vo-master.wav
echo "--- done ---"
