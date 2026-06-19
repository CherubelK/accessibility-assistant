#!/usr/bin/env bash
# Downloads the open-weight Piper TTS voices used by src/nodes/speech_out.py
# (see src/config.py LANGUAGES for the language -> voice mapping).
# Run once after cloning: bash models/download_voices.sh
set -e
cd "$(dirname "$0")/piper"

declare -A voices=(
  ["es_ES-davefx-medium"]="es/es_ES/davefx/medium"
  ["zh_CN-huayan-medium"]="zh/zh_CN/huayan/medium"
  ["vi_VN-vais1000-medium"]="vi/vi_VN/vais1000/medium"
  ["ar_JO-kareem-medium"]="ar/ar_JO/kareem/medium"
  ["ru_RU-denis-medium"]="ru/ru_RU/denis/medium"
  ["fr_FR-siwis-medium"]="fr/fr_FR/siwis/medium"
  ["pt_BR-faber-medium"]="pt/pt_BR/faber/medium"
  ["hi_IN-pratham-medium"]="hi/hi_IN/pratham/medium"
  ["ur_PK-fasih-medium"]="ur/ur_PK/fasih/medium"
  ["fa_IR-amir-medium"]="fa/fa_IR/amir/medium"
)

for name in "${!voices[@]}"; do
  dir="${voices[$name]}"
  echo "=== $name ==="
  curl -sL -o "${name}.onnx" "https://huggingface.co/rhasspy/piper-voices/resolve/main/${dir}/${name}.onnx"
  curl -sL -o "${name}.onnx.json" "https://huggingface.co/rhasspy/piper-voices/resolve/main/${dir}/${name}.onnx.json"
done

echo "Done. Voices saved in $(pwd)"
