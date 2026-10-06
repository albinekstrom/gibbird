#!/usr/bin/env bash
# Downloads Google's iNaturalist bird classifier (MobileNet V2, ~964 species, 3.5 MB).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p models
base=https://raw.githubusercontent.com/google-coral/test_data/master
for f in mobilenet_v2_1.0_224_inat_bird_quant.tflite inat_bird_labels.txt; do
  curl -fL --retry 3 -o "models/$f" "$base/$f"
done
echo "Model saved in models/"
