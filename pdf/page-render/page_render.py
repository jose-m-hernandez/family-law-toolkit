#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Render selected PDF pages to PNGs, with a contact sheet and a manifest.

Python 3.9 compatible. Exit codes: 0 ok, 2 usage/input, 3 page spec, 4 output dir, 5 unexpected.
"""
import argparse
import hashlib
import html
import fnmatch
import glob
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.parse

PNG_SIG = b"\x89PNG\r\n\x1a\n"
DEFAULT_PDFTOPPM = "/opt/homebrew/bin/pdftoppm"
DEFAULT_PDFINFO = "/opt/homebrew/bin/pdfinfo"
DEFAULT_PDFTOTEXT = "/opt/homebrew/bin/pdftotext"
MANIFEST = "manifest.tsv"
SHEET = "contact_sheet.html"


class Fail(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self, msg)
        self.code = code
        self.msg = msg


def find_pdftoppm():
    p = os.environ.get("PAGE_RENDER_PDFTOPPM", DEFAULT_PDFTOPPM)
    if os.path.isfile(p) and os.access(p, os.X_OK):
        return p
    raise Fail(2, "pdftoppm not found at %s" % p)


def parse_pages(spec, total):
    """Return sorted unique 1-based page numbers; Fail(3) on anything bad."""
    spec = spec.strip()
    if spec.lower() == "all":
        return list(range(1, total + 1))
    if not spec:
        raise Fail(3, "empty page spec")
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        bits = part.split("-")
        if len(bits) > 2 or not all(b.strip().isdigit() for b in bits):
            raise Fail(3, "bad page spec element: %r" % part)
        lo = int(bits[0])
        hi = int(bits[1]) if len(bits) == 2 else lo
        if lo < 1 or hi < lo:
            raise Fail(3, "bad page range: %r" % part)
        if hi > total:
            raise Fail(3, "page %d out of range (document has %d pages)" % (hi, total))
        pages.update(range(lo, hi + 1))
    return sorted(pages)


def poppler_tool(env, default):
    p = os.environ.get(env, default)
    if os.path.isfile(p) and os.access(p, os.X_OK):
        return p
    raise Fail(2, "%s not found at %s" % (os.path.basename(default), p))


def pdfinfo(path, extra, what):
    """Run pdfinfo; return stdout text. Fail(2) if poppler cannot read the file."""
    exe = poppler_tool("PAGE_RENDER_PDFINFO", DEFAULT_PDFINFO)
    r = subprocess.run([exe] + extra + [path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        first = (r.stderr.decode("utf-8", "replace").strip().splitlines() or ["no message"])[0]
        raise Fail(2, "poppler cannot read the PDF (%s): %s" % (what, first))
    return r.stdout.decode("utf-8", "replace")


def check_page_tree(reader):
    """Walk /Root /Pages with raw objects. Fail(5) on any malformed node, cycle, or /Count mismatch."""
    def bad(path):
        return Fail(5, "malformed page tree at %s: refusing; repair the PDF first" % path)

    seen = set()

    def walk(ref, path, depth):
        if depth > 64:
            raise bad(path)
        try:
            obj = ref.get_object()
        except Exception:
            raise bad(path)
        key = (getattr(ref, "idnum", None), getattr(ref, "generation", None))
        if key[0] is not None:
            if key in seen:
                raise bad(path)  # cycle or a node reachable twice
            seen.add(key)
        if not hasattr(obj, "get"):
            raise bad(path)
        typ = obj.get("/Type")
        if typ == "/Page":
            return 1
        if typ != "/Pages":
            raise bad(path)
        kids = obj.get("/Kids")
        kids = kids.get_object() if kids is not None and hasattr(kids, "get_object") else kids
        if not isinstance(kids, list):
            raise bad(path)
        n = 0
        for i, kid in enumerate(kids):
            n += walk(kid, "%s/Kids[%d]" % (path, i), depth + 1)
        cnt = obj.get("/Count")
        if cnt is None or int(cnt) != n:
            raise bad(path)
        return n

    root = reader.trailer["/Root"]
    pages = root.get("/Pages") if hasattr(root, "get") else None
    if pages is None:
        raise bad("/Root/Pages")
    walk(pages, "/Root/Pages", 0)


def read_pdf(path):
    """pypdf: encryption and page count only. Poppler is the authority for count and boxes."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise Fail(2, "pypdf is not installed")
    if not os.path.isfile(path):
        raise Fail(2, "input not found: %s" % path)
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise Fail(2, "PDF is encrypted: %s" % path)
        check_page_tree(reader)
        pypdf_total = len(reader.pages)
    except Fail:
        raise
    except Exception as e:
        raise Fail(2, "unreadable PDF (%s): %s" % (type(e).__name__, e))
    m = re.search(r"^Pages:\s+(\d+)\s*$", pdfinfo(path, [], "page count"), re.M)
    if not m:
        raise Fail(5, "pdfinfo did not report a page count")
    total = int(m.group(1))
    if pypdf_total != total:
        raise Fail(5, "page count disagreement between pypdf (%d) and poppler (%d): refusing"
                   % (pypdf_total, total))
    if total < 1:
        raise Fail(2, "PDF has no pages")
    return reader, total


def page_geometry(path, page):
    """Poppler's view of one page: (x0, y0, x1, y1, rotation), CropBox as reported by pdfinfo."""
    out = pdfinfo(path, ["-f", str(page), "-l", str(page), "-box"], "page %d" % page)
    box = re.search(r"^Page\s+%d\s+CropBox:\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$" % page, out, re.M)
    rot = re.search(r"^Page\s+%d\s+rot:\s+(-?\d+)\s*$" % page, out, re.M)
    if not box or not rot:
        raise Fail(5, "pdfinfo did not report CropBox/rotation for page %d" % page)
    x0, y0, x1, y1 = [float(v) for v in box.groups()]
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), int(rot.group(1)) % 360)


def pypdf_geometry(pg):
    """pypdf's view: CropBox (default MediaBox) clipped to MediaBox, as poppler does; effective /Rotate."""
    mb, cb = pg.mediabox, pg.cropbox
    x0, y0 = max(float(cb.left), float(mb.left)), max(float(cb.bottom), float(mb.bottom))
    x1, y1 = min(float(cb.right), float(mb.right)), min(float(cb.top), float(mb.top))
    return (x0, y0, x1, y1, int(pg.rotation or 0) % 360)


def geometry_mismatch(pypdf_g, poppler_g):
    """None if the two agree (box within 0.5 pt, same rotation), else a description. Accepts (w,h,rot) or 5-tuples."""
    if len(pypdf_g) == 3:
        a = (0, 0, pypdf_g[0], pypdf_g[1], pypdf_g[2])
        b = (0, 0, poppler_g[0], poppler_g[1], poppler_g[2])
    else:
        a, b = pypdf_g, poppler_g
    if a[4] != b[4]:
        return "rotation %d (pypdf) vs %d (poppler)" % (a[4], b[4])
    if any(abs(x - y) > 0.5 for x, y in zip(a[:4], b[:4])):
        return "page box %s (pypdf) vs %s (poppler)" % (
            [round(v, 2) for v in a[:4]], [round(v, 2) for v in b[:4]])
    return None


def expected_points(g):
    w, h = g[2] - g[0], g[3] - g[1]
    return (h, w) if g[4] % 180 == 90 else (w, h)


def tokens(text):
    return text.split()


def texts_agree(a, b):
    """False only when both texts are non-empty and differ after whitespace normalisation."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return True  # image-only (or one engine saw nothing): the one-sided rule handles the latter
    return ta == tb


def empty_side(poppler_txt, pypdf_txt):
    """(engine_with_nothing, engine_with_text) when exactly one side is empty, else None."""
    pe, ye = not poppler_txt.strip(), not pypdf_txt.strip()
    if pe and not ye:
        return ("poppler", "pypdf")
    if ye and not pe:
        return ("pypdf", "poppler")
    return None


def poppler_text(path, page):
    exe = poppler_tool("PAGE_RENDER_PDFTOTEXT", DEFAULT_PDFTOTEXT)
    r = subprocess.run([exe, "-f", str(page), "-l", str(page), path, "-"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else ""


def check_userunit(reader, pages):
    """Refuse requested pages whose /UserUnit is not 1, before anything is written."""
    for p in pages:
        uu = reader.pages[p - 1].get("/UserUnit")
        try:
            uu = 1.0 if uu is None else float(uu)
        except (TypeError, ValueError):
            raise Fail(3, "page %d has an unreadable /UserUnit; refusing to render at an unknown scale" % p)
        if uu != 1.0:
            raise Fail(3, "page %d has /UserUnit %g (not 1); refusing to render at a wrong scale" % (p, uu))


def extract_single(reader, page, tmp):
    """pypdf alone selects page N: clone the whole document (catalog, /OCProperties, /AcroForm, /Names
    survive), drop every other page, write a one-page PDF. Poppler never chooses the page."""
    from pypdf import PdfReader, PdfWriter
    w = PdfWriter(clone_from=reader)
    for i in range(len(w.pages) - 1, -1, -1):
        if i != page - 1:
            w.remove_page(i)
    path = os.path.join(tmp, "one-%04d.pdf" % page)
    with open(path, "wb") as f:
        w.write(f)
    chk = PdfReader(path)
    if len(chk.pages) != 1:
        raise Fail(5, "extracted file for page %d has %d pages, expected 1" % (page, len(chk.pages)))

    def content(pg):
        c = pg.get_contents()
        return c.get_data() if c is not None else b""

    if content(chk.pages[0]) != content(reader.pages[page - 1]):
        raise Fail(5, "extracted page %d content differs from the source page, refusing" % page)
    return path


def png_pixels(path):
    """(IHDR bytes, decompressed IDAT pixel data): compares what is drawn, not file bytes."""
    import zlib
    with open(path, "rb") as f:
        d = f.read()
    if d[:8] != PNG_SIG:
        raise ValueError("not a PNG: %s" % path)
    i, ihdr, idat = 8, b"", b""
    while i + 8 <= len(d):
        n = struct.unpack(">I", d[i:i + 4])[0]
        t, body = d[i + 4:i + 8], d[i + 8:i + 8 + n]
        if t == b"IHDR":
            ihdr = body
        elif t == b"IDAT":
            idat += body
        i += 12 + n
    return ihdr, zlib.decompress(idat)


def check_extracted(reader, page, one, full_pdf):
    """Verify the one-page file really is page N; return poppler's geometry for it."""
    from pypdf import PdfReader
    m = re.search(r"^Pages:\s+(\d+)\s*$", pdfinfo(one, [], "extracted page %d" % page), re.M)
    if not m or int(m.group(1)) != 1:
        raise Fail(5, "extracted file for page %d does not have exactly one page" % page)
    g = page_geometry(one, 1)
    bad = geometry_mismatch(pypdf_geometry(reader.pages[page - 1]), g)
    if bad:
        raise Fail(5, "page %d: extracted page differs from the source page (%s), refusing" % (page, bad))
    try:
        ptxt = PdfReader(one).pages[0].extract_text() or ""
    except Exception:
        ptxt = ""
    ptxt_poppler = poppler_text(one, 1)
    if not texts_agree(ptxt_poppler, poppler_text(full_pdf, page)):  # hard: poppler vs poppler
        raise Fail(5, "page %d: the one-page copy and the full document give different text, refusing" % page)
    status = text_status(ptxt_poppler, ptxt, bool(reader.pages[page - 1].get("/Annots")))
    if status in ("differ", "one-empty"):  # advisory only: pixel identity and the tree check decide page identity
        print("page_render: warning: page %d: text %s between pypdf and poppler" % (page, status), file=sys.stderr)
    return g, status


def text_status(poppler_txt, pypdf_txt, has_annots):
    """agree / differ / one-empty / skipped-annots (pypdf omits form-field text poppler draws)."""
    if has_annots:
        return "skipped-annots"
    if empty_side(poppler_txt, pypdf_txt):
        return "one-empty"
    return "agree" if texts_agree(poppler_txt, pypdf_txt) else "differ"


def png_dims(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != PNG_SIG or head[12:16] != b"IHDR":
        raise ValueError("not a valid PNG: %s" % path)
    return struct.unpack(">II", head[16:24])


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def prepare_outdir(outdir, stem, names, overwrite):
    try:
        os.makedirs(outdir, exist_ok=True)
        if not os.access(outdir, os.W_OK | os.X_OK):
            raise OSError("not writable")
        probe = tempfile.mkstemp(dir=outdir, prefix=".probe-")
        os.close(probe[0])
        os.unlink(probe[1])
    except OSError as e:
        raise Fail(4, "OUTDIR not writable: %s (%s)" % (outdir, e))
    pattern = glob.escape(stem) + "-p*.png"
    existing = [n for n in os.listdir(outdir)
                if fnmatch.fnmatchcase(n, pattern) or n in (MANIFEST, SHEET)]
    wanted = set(names)
    if overwrite:
        # files this run overwrites are fine; any other <stem>-p*.png would sit stale beside the new ones
        bad = [n for n in existing if n not in wanted and n not in (MANIFEST, SHEET)]
    else:
        bad = existing
    if bad:
        raise Fail(4, "OUTDIR already holds %d file(s) this run would not cleanly replace, e.g. %s; "
                   "nothing was deleted. Choose an empty OUTDIR%s"
                   % (len(bad), sorted(bad)[0], "" if overwrite else " (or --overwrite for an exact re-run)"))


def render_one(pdftoppm, pdf, page, dpi, tmp):
    """Render a single page; -singlefile gives a predictable name, which we verify."""
    for old in os.listdir(tmp):
        if old.startswith("pg"):
            os.unlink(os.path.join(tmp, old))
    cmd = [pdftoppm, "-png", "-r", str(dpi), "-f", str(page), "-l", str(page),
           "-cropbox", "-singlefile", pdf, os.path.join(tmp, "pg")]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err = r.stderr.decode("utf-8", "replace").strip()
    if r.returncode != 0 or err:
        first = (err.splitlines() or ["exit %d" % r.returncode])[0]
        raise Fail(5, "pdftoppm reported a problem on page %d: %s" % (page, first))
    produced = sorted(n for n in os.listdir(tmp) if n.startswith("pg"))
    if produced != ["pg.png"]:
        raise Fail(5, "pdftoppm produced unexpected files for page %d: %r" % (page, produced))
    return os.path.join(tmp, "pg.png")


def write_sheet(path, stem, rows):
    parts = ["<!doctype html><meta charset='utf-8'><title>%s contact sheet</title>" % html.escape(stem),
             "<style>body{font-family:sans-serif}figure{display:inline-block;margin:8px;text-align:center}"
             "img{width:220px;border:1px solid #888}</style>",
             "<h1>%s: %d page(s)</h1>" % (html.escape(stem), len(rows))]
    for page, fname, w, h in rows:
        ref = html.escape(urllib.parse.quote(fname), True)
        parts.append("<figure><a href='%s'><img src='%s' alt='page %d'></a>"
                     "<figcaption>Page %d<br><small>%dx%d px</small></figcaption></figure>"
                     % (ref, ref, page, page, w, h))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")


def run(args):
    if not 72 <= args.dpi <= 600:
        raise Fail(2, "--dpi must be 72-600, got %d" % args.dpi)
    pdftoppm = find_pdftoppm()
    pdf = os.path.abspath(args.input)
    reader, total = read_pdf(pdf)
    pages = parse_pages(args.pages, total)  # all validation before any rendering
    check_userunit(reader, pages)
    stem = os.path.splitext(os.path.basename(pdf))[0]
    fnames = {p: "%s-p%04d.png" % (stem, p) for p in pages}
    outdir = os.path.abspath(args.output)
    prepare_outdir(outdir, stem, list(fnames.values()) + [MANIFEST, SHEET], args.overwrite)

    rows = []
    tstat = {}
    staged = []
    tmp = tempfile.mkdtemp(dir=outdir, prefix=".render-")
    try:
        for p in pages:
            one = extract_single(reader, p, tmp)
            g, tstatus = check_extracted(reader, p, one, pdf)
            tstat[p] = tstatus
            # second, independent path: the tree is validated, so poppler's page p of the FULL file is pypdf's page p
            full = os.path.join(tmp, "full-%04d.png" % p)
            os.replace(render_one(pdftoppm, pdf, p, args.dpi, tmp), full)
            src = render_one(pdftoppm, one, 1, args.dpi, tmp)
            try:
                same = png_pixels(src) == png_pixels(full)
            except Exception:
                same = False
            if not same:
                raise Fail(5, "render mismatch on page %d: the one-page copy and the full document render "
                           "differently, refusing" % p)
            w, h = png_dims(src)
            sw, sh = expected_points(g)
            ew, eh = sw * args.dpi / 72.0, sh * args.dpi / 72.0
            if abs(w - ew) > 2 or abs(h - eh) > 2:
                raise Fail(5, "page %d is %dx%d px, expected about %.0fx%.0f" % (p, w, h, ew, eh))
            keep = os.path.join(tmp, "keep-%04d.png" % p)
            os.replace(src, keep)
            staged.append((p, keep))
            rows.append((p, fnames[p], w, h))
        for p, keep in staged:  # commit only after every page passed
            os.replace(keep, os.path.join(outdir, fnames[p]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # count check before success: exactly one valid PNG per requested page, no extras
    present = sorted(n for n in os.listdir(outdir)
                     if n.startswith(stem + "-p") and n.endswith(".png") and n in set(fnames.values()))
    if len(rows) != len(pages) or present != sorted(fnames.values()):
        raise Fail(5, "count mismatch: requested %d, rendered %d" % (len(pages), len(present)))

    with open(os.path.join(outdir, MANIFEST), "w", encoding="utf-8") as f:
        f.write("page\tfile\twidth_px\theight_px\tsha256\ttext_check\n")
        for p, fname, w, h in rows:
            f.write("%d\t%s\t%d\t%d\t%s\t%s\n" % (p, fname, w, h, sha256(os.path.join(outdir, fname)), tstat[p]))
    write_sheet(os.path.join(outdir, SHEET), stem, rows)
    print("OK: rendered %d of %d page(s) at %d dpi -> %s" % (len(rows), total, args.dpi, outdir))
    print("pages: %s" % ",".join(str(r[0]) for r in rows))
    print("manifest: %s\ncontact sheet: %s" % (os.path.join(outdir, MANIFEST), os.path.join(outdir, SHEET)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render PDF pages to PNG with contact sheet and manifest.")
    ap.add_argument("input")
    ap.add_argument("--pages", required=True, help="e.g. 1-3,9 or all (1-based)")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--overwrite", action="store_true")
    try:
        args = ap.parse_args(argv)  # argparse exits 2 on usage errors
        return run(args)
    except Fail as e:
        print("page_render: error: %s" % e.msg, file=sys.stderr)
        return e.code
    except Exception as e:  # fail closed
        print("page_render: unexpected error: %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 5


if __name__ == "__main__":
    sys.exit(main())
