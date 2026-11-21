# Plan: 10 titles x first 50 chapters in Hinglish

Goal: translate the first 50 chapters of 10 famous titles to Hinglish, publish them on the Astro reader site, and measure how readers respond.

Scale: about 500 chapters, roughly 12,000 pages (at about 24 pages per chapter).

## Phase 0 - Done
- Download (mangadex-dl), OCR (EasyOCR), AI upscale 2x (Real-ESRGAN anime), erase and redraw Hinglish (`render.py`).
- Chapter 1 of Soul Land finished end to end.
- Astro site scaffolded in `site/` (home, browse, series, reader).

## Phase 1 - Pick titles and sources
- Choose 10 titles. Check each has English chapters 1-50 hosted on MangaDex (many famous ones only link out, so check the API first).
- Save the list in `titles.json` (title, MangaDex id, chapters).

## Phase 2 - Automate the pipeline (blocker: no API key on this machine)
Hand-reading every page worked for 1 chapter but will not scale to 12,000 pages. Needed:
1. OCR with bubble grouping (exists).
2. Translation step that sends a whole page (image plus OCR text) to a Claude model with a per-series glossary and a rolling story summary. Needs an `ANTHROPIC_API_KEY` and a cost estimate first.
3. Automatic quality checks: text overflow, untranslated English left behind, missing bubbles. Human spot-check about 3 pages per chapter.
4. Render onto enhanced pages (exists).

## Phase 3 - Pilot before scaling
- 1 title x 5 chapters. Record: time per chapter, API cost per chapter, % of bubbles needing fixes.
- Decide go / no-go for the rest from those numbers.

## Phase 4 - Scale
- Run per title in overnight batches. Estimated machine time on this Mac: about 6 s/page upscale plus OCR and render, so roughly 20-35 hours total for 12,000 pages.
- Keep glossary and story summary files per title so names stay consistent across 50 chapters.

## Phase 5 - Hosting and launch
- Size: about 8 MB per chapter, so about 4 GB for 500 chapters. GitHub Pages limits a site to about 1 GB, so images need other storage (for example Cloudflare R2 or Pages) or lower quality and smaller pages.
- On-page SEO (done: titles, descriptions, canonical, Open Graph, sitemap, robots). Then analytics and Search Console.

## Open issues to decide before Phase 5
1. Copyright: these are commercial series and the source pages are fan scans. Publishing 500 translated chapters publicly is the main risk (takedown notices, host suspension). Safer: keep the site private/local, or use licensed, public-domain or own content.
2. Backlinks: earning links (a real community, sharing on relevant forums, a Discord) is fine. Mass automated link posting is spam and can get the site de-indexed and accounts banned, so it is not part of this plan.
