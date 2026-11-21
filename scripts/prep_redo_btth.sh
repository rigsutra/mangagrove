#!/bin/zsh
# Battle Through the Heavens pages are PNG; re-run enhance + OCR after the other jobs finish.
cd /Users/ashishsingh/projects/mangatranslate
until grep -q "SOULLAND DONE" /tmp/prep_soul.log 2>/dev/null; do sleep 30; done
for ch in raw_en/battle-through-the-heavens/Vol.*; do
  echo "REDO btth $ch"
  .venv/bin/python enhance.py "$ch" >/dev/null 2>&1
  OCR_SCALE=2 OCR_GAP=9 OCR_LANGS=en OCR_INVERT=0 .venv/bin/python ocr.py "$ch" >/dev/null 2>&1
done
echo "BTTH DONE"
