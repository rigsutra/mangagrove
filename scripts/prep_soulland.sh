#!/bin/zsh
cd /Users/ashishsingh/projects/mangatranslate
until grep -q "ALL DONE" /tmp/prep.log; do sleep 30; done
for ch in raw_en/Vol.\ 1\ Ch.\ *; do
  [[ "$ch" == "raw_en/Vol. 1 Ch. 1" ]] && continue
  echo "PREP soul-land $ch"
  .venv/bin/python enhance.py "$ch" >/dev/null 2>&1
  OCR_SCALE=2 OCR_GAP=9 OCR_LANGS=en OCR_INVERT=0 .venv/bin/python ocr.py "$ch" >/dev/null 2>&1
done
echo "SOULLAND DONE"
