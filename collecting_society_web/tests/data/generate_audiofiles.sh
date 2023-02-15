#!/bin/bash

BITRATE=16
CHANNELS=2
SAMPLERATE=44100
CDLENGTH=3600
SONGLENGTH=300

# make dirs
mkdir -p ape au flac shn tta wav wv

# generate noise (44100Hz, 16bit, stereo)
echo "generating noise ..."
sox -n -G -c$CHANNELS -b$BITRATE -r$SAMPLERATE noise.wav synth whitenoise gain -15 trim 0 $CDLENGTH
# generate numbers
echo "generating numbers ..."
echo {1..1882}. | espeak --stdin -w numbers.wav
ffmpeg -y -i numbers.wav -ac $CHANNELS -ab $BITRATE -ar $SAMPLERATE numbers.hq.wav
mv numbers.hq.wav numbers.wav

### cd-full
# mix noise and numbers
echo "generating full cd ..."
sox -m noise.wav numbers.wav wav/upload-cd-full.wav trim 0 $CDLENGTH
# convert
echo "converting full cd ..."
ffmpeg -y -i wav/upload-cd-full.wav au/upload-cd-full.au
ffmpeg -y -i wav/upload-cd-full.wav flac/upload-cd-full.flac
#ffmpeg -y -i wav/upload-cd-full.wav wv/upload-cd-full.wv
mac wav/upload-cd-full.wav ape/upload-cd-full.ape -c2000
#shorten wav/upload-cd-full.wav shn/upload-cd-full.shn
#ttaenc -e wav/upload-cd-full.wav -o tta/upload-cd-full.tta

### cd-songs
# split
echo "splitting songs ..."
sox wav/upload-cd-full.wav wav/upload-cd-song.wav trim 0 $SONGLENGTH : newfile : restart
# convert
echo "converting songs ..."
for song in wav/upload-cd-song*.wav; do
  filename=$(basename "$song")
  songname="${filename%.*}"
  ffmpeg -y -i $song au/$songname.au
  ffmpeg -y -i $song flac/$songname.flac
  #ffmpeg -y -i $song wv/$songname.wv
  mac $song ape/$songname.ape -c2000
  #shorten $song shn/$songname.shn
  #ttaenc -e $song -o tta/$songname.tta
done
echo "done."
