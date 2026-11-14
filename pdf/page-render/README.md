# page-render

Renders selected pages of an image-only PDF to PNGs, so they can be read and cited.
Python 3.9 stdlib + `pypdf`; renders with `/opt/homebrew/bin/pdftoppm` (override: env `PAGE_RENDER_PDFTOPPM`).

    python3 page_render.py INPUT.pdf --pages 1-3,9 [--dpi 200] -o OUTDIR [--overwrite]

- `--pages`: 1-based, comma list of pages and inclusive ranges, or `all`. Duplicates collapse; output is in page order.
- `--dpi`: 72-600, default 200.
- Output: `OUTDIR/<stem>-p<NNNN>.png` (named by SOURCE page), `contact_sheet.html`, `manifest.tsv`
  (`page file width_px height_px sha256 text_check`).
- Contact sheet is HTML referencing the PNGs by relative path (no extra dependencies; keep it beside the PNGs).

## Exit codes
0 ok; 2 usage, missing/unreadable/encrypted PDF, bad dpi, poppler tool missing; 3 bad page spec, page out of range,
or a requested page with `/UserUnit` other than 1 (validated before anything renders); 4 OUTDIR not writable, or
OUTDIR holds files this run would not cleanly replace; 5 unexpected or an integrity check failed (fails closed).

## Design: one engine decides which page is page N
Page identity rests on the malformed-tree refusal plus two-path pixel identity (below); the pypdf-vs-poppler text compare is advisory.
- **Malformed page trees are refused (exit 5, before anything renders):** `/Root/Pages` is walked recursively on raw pypdf objects.
  A /Kids entry whose /Type is missing or neither /Page nor /Pages, a cycle or duplicate node, or a /Count that
  disagrees with the leaf count gives `malformed page tree at <path>: refusing; repair the PDF first`. This is what stops
  junk /Kids entries, which shift page numbers differently in pypdf and poppler, including on image-only scans.
  Such PDFs (and PDFs with no /Type on a page) are refused, not repaired; repair them first.
- **pypdf alone selects the page.** For each requested page N, pypdf clones the whole document (catalog, /OCProperties, /AcroForm
  survive), drops every other page, and writes a one-page PDF in the staging dir
  and `pdftoppm -f 1 -l 1 -cropbox` renders THAT file. Poppler never chooses a page. The extracted file's page count
  must be 1 before rendering.

## Checks done on every run
- **Pixel cross-check:** page N is also rendered from the full file (`-f N -l N -cropbox`, same dpi); decoded IHDR + pixel data
  must be identical to the one-page render, else exit 5 "render mismatch on page N". Two independent paths must agree.
- pypdf detects encryption; the pypdf and poppler (`pdfinfo`) page counts must also agree (exit 5).
- **Structural cross-check, per requested page, on the extracted file:** pypdf's box for page N (CropBox else MediaBox,
  clipped to MediaBox as poppler does) and effective /Rotate must match `pdfinfo -box` and its rotation (0.5 pt), else exit 5.
- **Text cross-check is ADVISORY** (pypdf vs poppler spacing differs on real filings, e.g. `P 0` vs `P0`). `differ` or
  `one-empty` prints a warning to stderr and is recorded in the manifest `text_check` column
  (`agree`/`differ`/`one-empty`/`skipped-annots`; pages with /Annots skip it, since pypdf omits field text). It never changes
  the exit code. The HARD text check is poppler vs poppler: the one-page copy's text must equal page N of the full file.
- `pdftoppm` runs with `-cropbox`; ANY stderr output from it (e.g. "Syntax Error") is exit 5. Each PNG's IHDR size must
  match CropBox x dpi/72 (+-2 px, rotation swapped). PNGs are staged and moved into OUTDIR only after every page passed.
- **OUTDIR must be clean:** exit 4 if it holds any `<stem>-p*.png`, `manifest.tsv` or `contact_sheet.html` (without
  `--overwrite`), or, with `--overwrite`, any `<stem>-p*.png` the run would not overwrite. Files are never deleted; use an empty OUTDIR.
- `/UserUnit` != 1 on a requested page: exit 3 naming the page (not rendered at a wrong scale).
- The produced file set must equal the requested set before success is printed.

## Limits
- Encrypted PDFs are refused, not decrypted. Rendering uses the CropBox (as poppler reports it, clipped to the MediaBox) and page /Rotate.
- Contact sheet is HTML, not PDF/image; link and src values are percent-encoded, captions HTML-escaped; thumbnails scaled in the browser.
- Remaining limits: pypdf is trusted to order a well-formed tree correctly; a wrong /Count-consistent but
  semantically misordered tree (pages simply in the wrong order) cannot be detected by any tool. pypdf's page copy keeps the
  page's own content but a damaged object shared between pages could still render wrongly; the cross-checks above are the only net.
- Very large dpi on large pages makes big files; no memory cap.
- Env overrides: `PAGE_RENDER_PDFTOPPM`, `PAGE_RENDER_PDFINFO`, `PAGE_RENDER_PDFTOTEXT`.
- Tests: `python3 -m unittest discover -s tests` (fixtures in `tests/pdfs/`).
