# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import fixtures  # noqa: E402
import page_render  # noqa: E402

TOOL = os.path.join(ROOT, "page_render.py")


def run(*args, **env):
    e = dict(os.environ)
    e.update(env)
    r = subprocess.run([sys.executable, TOOL] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, env=e, universal_newlines=True)
    return r.returncode, r.stdout, r.stderr


def ihdr(path):
    with open(path, "rb") as f:
        d = f.read(24)
    assert d[:8] == b"\x89PNG\r\n\x1a\n", "bad signature"
    assert d[12:16] == b"IHDR"
    return struct.unpack(">II", d[16:24])


def expected(page, dpi):
    w, h, rot = fixtures.SPEC[page - 1]
    if rot % 180 == 90:
        w, h = h, w
    return w * dpi / 72.0, h * dpi / 72.0


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.pdf = os.path.join(self.tmp, "filing.pdf")
        with open(self.pdf, "wb") as f:
            f.write(fixtures.build_pdf(fixtures.SPEC))
        self.out = os.path.join(self.tmp, "out")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pngs(self):
        return sorted(n for n in os.listdir(self.out) if n.endswith(".png"))


class RenderTests(Base):
    def test_exact_files_and_page_identity(self):
        code, out, err = run(self.pdf, "--pages", "1-3,9,12", "--dpi", "100", "-o", self.out)
        self.assertEqual(code, 0, err)
        want = [1, 2, 3, 9, 12]
        self.assertEqual(self.pngs(), ["filing-p%04d.png" % p for p in want])  # no extras, none missing
        self.assertEqual(sorted(os.listdir(self.out)),
                         sorted(self.pngs() + ["manifest.tsv", "contact_sheet.html"]))
        for p in want:  # distinct page sizes make dimensions identify the source page
            w, h = ihdr(os.path.join(self.out, "filing-p%04d.png" % p))
            ew, eh = expected(p, 100)
            self.assertLessEqual(abs(w - ew), 2, p)
            self.assertLessEqual(abs(h - eh), 2, p)

    def test_single_page_named_by_source_number(self):
        code, _, err = run(self.pdf, "--pages", "5", "-o", self.out)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.pngs(), ["filing-p0005.png"])
        w, h = ihdr(os.path.join(self.out, "filing-p0005.png"))
        self.assertLessEqual(abs(w - expected(5, 200)[0]), 2)

    def test_all_pages(self):
        code, _, err = run(self.pdf, "--pages", "all", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.pngs()), 12)

    def test_landscape_and_rotated_orientation(self):
        run(self.pdf, "--pages", "4,7,10", "--dpi", "144", "-o", self.out)
        w, h = ihdr(os.path.join(self.out, "filing-p0004.png"))
        self.assertGreater(w, h)                      # landscape stays landscape
        w, h = ihdr(os.path.join(self.out, "filing-p0007.png"))
        self.assertGreater(w, h)                      # 320x520 rotated 90 -> landscape
        self.assertLessEqual(abs(w - 520 * 2), 2)
        w, h = ihdr(os.path.join(self.out, "filing-p0010.png"))
        self.assertGreater(w, h)                      # 270 also swaps
        self.assertLessEqual(abs(h - 330 * 2), 2)

    def test_manifest_matches_files(self):
        run(self.pdf, "--pages", "2-4,7", "-o", self.out)
        with open(os.path.join(self.out, "manifest.tsv")) as f:
            lines = f.read().splitlines()
        self.assertEqual(lines[0].split("\t"), ["page", "file", "width_px", "height_px", "sha256", "text_check"])
        self.assertEqual([int(l.split("\t")[0]) for l in lines[1:]], [2, 3, 4, 7])
        for l in lines[1:]:
            page, fname, w, h, sha, tc = l.split("\t")
            self.assertEqual(tc, "agree")
            path = os.path.join(self.out, fname)
            with open(path, "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), sha)
            self.assertEqual(ihdr(path), (int(w), int(h)))

    def test_contact_sheet_lists_every_page(self):
        run(self.pdf, "--pages", "1,6,11", "-o", self.out)
        with open(os.path.join(self.out, "contact_sheet.html")) as f:
            s = f.read()
        for p in (1, 6, 11):
            self.assertIn("filing-p%04d.png" % p, s)
            self.assertIn("Page %d<" % p, s)
        self.assertEqual(s.count("<img"), 3)

    def test_pages_differ(self):
        run(self.pdf, "--pages", "1-3", "-o", self.out)
        with open(os.path.join(self.out, "manifest.tsv")) as f:
            shas = [l.split("\t")[4] for l in f.read().splitlines()[1:]]
        self.assertEqual(len(set(shas)), 3)


class FailureTests(Base):
    def test_bad_specs_exit_3_and_render_nothing(self):
        for spec in ["0", "13", "1-13", "5-3", "a", "1,,2", "", "1-2-3", "-1"]:
            code, _, _ = run(self.pdf, "--pages", spec, "-o", self.out)
            self.assertEqual(code, 3, spec)
            self.assertFalse(os.path.exists(self.out) and self.pngs(), spec)

    def test_late_bad_page_renders_nothing(self):
        code, _, _ = run(self.pdf, "--pages", "1-2,99", "-o", self.out)
        self.assertEqual(code, 3)
        self.assertFalse(os.path.exists(self.out) and os.listdir(self.out))

    def test_missing_input_and_bad_dpi_exit_2(self):
        self.assertEqual(run(os.path.join(self.tmp, "nope.pdf"), "--pages", "1", "-o", self.out)[0], 2)
        self.assertEqual(run(self.pdf, "--pages", "1", "--dpi", "71", "-o", self.out)[0], 2)
        self.assertEqual(run(self.pdf, "--pages", "1", "--dpi", "601", "-o", self.out)[0], 2)
        self.assertEqual(run(self.pdf, "-o", self.out)[0], 2)

    def test_garbage_pdf_exit_2(self):
        bad = os.path.join(self.tmp, "bad.pdf")
        with open(bad, "wb") as f:
            f.write(b"not a pdf at all")
        self.assertEqual(run(bad, "--pages", "1", "-o", self.out)[0], 2)

    def test_encrypted_pdf_exit_2(self):
        from pypdf import PdfReader, PdfWriter
        w = PdfWriter()
        for pg in PdfReader(self.pdf).pages:
            w.add_page(pg)
        w.encrypt("secret")
        enc = os.path.join(self.tmp, "enc.pdf")
        with open(enc, "wb") as f:
            w.write(f)
        self.assertEqual(run(enc, "--pages", "1", "-o", self.out)[0], 2)

    def test_pdftoppm_missing_exit_2(self):
        code, _, err = run(self.pdf, "--pages", "1", "-o", self.out, PAGE_RENDER_PDFTOPPM="/nonexistent/pdftoppm")
        self.assertEqual(code, 2)

    def test_outdir_not_writable_exit_4(self):
        os.makedirs(self.out)
        os.chmod(self.out, 0o500)
        try:
            self.assertEqual(run(self.pdf, "--pages", "1", "-o", self.out)[0], 4)
        finally:
            os.chmod(self.out, 0o700)

    def test_overwrite_refused_then_allowed(self):
        self.assertEqual(run(self.pdf, "--pages", "1-2", "-o", self.out)[0], 0)
        marker = os.path.join(self.out, "filing-p0002.png")
        with open(marker, "wb") as f:
            f.write(b"keep")
        self.assertEqual(run(self.pdf, "--pages", "2-3", "-o", self.out)[0], 4)
        with open(marker, "rb") as f:
            self.assertEqual(f.read(), b"keep")
        self.assertFalse(os.path.exists(os.path.join(self.out, "filing-p0003.png")))
        # --overwrite of a SUBSET would leave filing-p0001.png stale beside the new files: refused (fix 5)
        self.assertEqual(run(self.pdf, "--pages", "2-3", "-o", self.out, "--overwrite")[0], 4)
        self.assertEqual(run(self.pdf, "--pages", "1-2", "-o", self.out, "--overwrite")[0], 0)
        self.assertGreater(os.path.getsize(marker), 100)

    def test_no_temp_leftovers(self):
        run(self.pdf, "--pages", "1", "-o", self.out)
        self.assertFalse([n for n in os.listdir(self.out) if n.startswith(".")])


STUBS = os.path.join(HERE, "stubs")  # stand-ins for pdftoppm; the PDFs are built by fixtures.py at set-up


def decode_png(path):  # stdlib PNG decoder, 8-bit RGB/gray/RGBA
    import zlib
    d = open(path, "rb").read()
    i, idat = 8, b""
    while i < len(d):
        n, = struct.unpack(">I", d[i:i + 4])
        t, body = d[i + 4:i + 8], d[i + 8:i + 8 + n]
        if t == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        if t == b"IDAT":
            idat += body
        i += 12 + n
    raw = zlib.decompress(idat)
    bpp = {2: 3, 0: 1, 6: 4}[ct]
    stride, rows, prev, p = w * bpp, [], bytearray(w * bpp), 0
    for y in range(h):
        f, line = raw[p], bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return w, h, rows


def fixture(name, dest_dir, as_name=None):
    return fixtures.write_named(name, dest_dir, as_name)


class ReviewFixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.out = os.path.join(self.tmp, "out")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pngs(self):
        return sorted(n for n in os.listdir(self.out) if n.endswith(".png")) if os.path.isdir(self.out) else []

    # fix 1: poppler is the page-count authority; disagreement refuses
    def test_fix1_page_count_disagreement_exit_5(self):
        pdf = os.path.join(self.tmp, "cnt.pdf")
        data = fixtures.build_named("junkkid.pdf")
        with open(pdf, "wb") as f:
            f.write(data.replace(b"/Count 4", b"/Count 9", 1))  # pypdf walks Kids (4), poppler trusts /Count (9)
        code, _, err = run(pdf, "--pages", "1", "-o", self.out)
        self.assertEqual(code, 5, err)
        self.assertIn("malformed page tree at /Root/Pages", err)  # superseded: tree walk catches /Count lies first
        self.assertEqual(self.pngs(), [])

    # fix 2: wrong-page guard (the /Kids fixture: poppler page 3 text is "PAGE 2")
    def test_fix2_kids_fixture_exit_5(self):
        pdf = fixture("junkkid.pdf", self.tmp)
        for spec in ("3", "all"):  # the junk /Kids entry is now refused as a malformed tree, before any page is chosen
            code, _, err = run(pdf, "--pages", spec, "-o", self.out)
            self.assertEqual(code, 5, err)
            self.assertIn("malformed page tree at /Root/Pages/Kids[1]", err)
        self.assertEqual(self.pngs(), [])

    def test_fix2_guard_unit(self):
        self.assertTrue(page_render.texts_agree("PAGE 1", "PAGE   1\n"))
        self.assertFalse(page_render.texts_agree("PAGE 2", "PAGE 3"))
        self.assertTrue(page_render.texts_agree("", "PAGE 3"))  # one side empty: guard cannot judge

    # fix 3: any pdftoppm stderr is fatal
    def test_fix3_pdftoppm_stderr_exit_5(self):
        pdf = fixture("corrupt.pdf", self.tmp)
        code, _, err = run(pdf, "--pages", "all", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 5, err)
        self.assertIn("Syntax Error", err)
        self.assertEqual(self.pngs(), [])

    # fix 4: CropBox honoured, size computed from pdfinfo's CropBox
    def test_fix4_cropbox_smaller_than_mediabox(self):
        pdf = fixture("crop.pdf", self.tmp)
        code, _, err = run(pdf, "--pages", "1", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 0, err)
        self.assertEqual(ihdr(os.path.join(self.out, "crop-p0001.png")), (612, 492))

    def test_fix4_cropbox_larger_than_mediabox(self):
        pdf = fixture("cropbig.pdf", self.tmp)
        code, _, err = run(pdf, "--pages", "1", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 0, err)
        self.assertEqual(ihdr(os.path.join(self.out, "cropbig-p0001.png")), (612, 792))

    def test_fix4_inherited_rotation(self):
        pdf = fixture("inhrot.pdf", self.tmp)
        code, _, err = run(pdf, "--pages", "1", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 0, err)
        self.assertEqual(ihdr(os.path.join(self.out, "inhrot-p0001.png")), (792, 612))

    # fix 5: stale files
    def test_fix5_stale_png_without_overwrite_exit_4(self):
        pdf = fixture("same.pdf", self.tmp)
        os.makedirs(self.out)
        stale = os.path.join(self.out, "same-p0009.png")
        with open(stale, "wb") as f:
            f.write(b"old")
        code, _, err = run(pdf, "--pages", "1", "-o", self.out)
        self.assertEqual(code, 4, err)
        self.assertEqual(os.listdir(self.out), ["same-p0009.png"])
        self.assertIn("empty OUTDIR", err)

    def test_fix5_stale_manifest_or_sheet_exit_4(self):
        pdf = fixture("same.pdf", self.tmp)
        for name in ("manifest.tsv", "contact_sheet.html"):
            shutil.rmtree(self.out, ignore_errors=True)
            os.makedirs(self.out)
            with open(os.path.join(self.out, name), "w") as f:
                f.write("old")
            self.assertEqual(run(pdf, "--pages", "1", "-o", self.out)[0], 4, name)
            self.assertEqual(os.listdir(self.out), [name])

    def test_fix5_overwrite_still_refuses_leftover_png(self):
        pdf = fixture("same.pdf", self.tmp)
        self.assertEqual(run(pdf, "--pages", "1-3", "-o", self.out)[0], 0)
        code, _, err = run(pdf, "--pages", "1-2", "-o", self.out, "--overwrite")
        self.assertEqual(code, 4, err)
        self.assertEqual(len(self.pngs()), 3)

    # fix 6: contact sheet links resolve
    def test_fix6_contact_sheet_links_resolve(self):
        from html.parser import HTMLParser
        from urllib.parse import unquote, urlsplit
        pdf = fixture("same.pdf", self.tmp, "Exhibit #3 50%.pdf")
        code, _, err = run(pdf, "--pages", "1-2", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 0, err)
        found = []

        class P(HTMLParser):
            def handle_starttag(self, tag, attrs):
                a = dict(attrs)
                if tag == "img":
                    found.append(a["src"])
                if tag == "a":
                    found.append(a["href"])

        with open(os.path.join(self.out, "contact_sheet.html"), encoding="utf-8") as f:
            P().feed(f.read())
        self.assertEqual(len(found), 4)
        for ref in found:
            parts = urlsplit(ref)  # how a browser reads it: '#' would start a fragment
            self.assertEqual((parts.fragment, parts.query), ("", ""), ref)
            self.assertNotIn(" ", ref)
            self.assertTrue(os.path.isfile(os.path.join(self.out, unquote(parts.path))), ref)

    def test_fix6_caption_escaped(self):
        pdf = fixture("same.pdf", self.tmp, "a<b>&c.pdf")
        self.assertEqual(run(pdf, "--pages", "1", "--dpi", "72", "-o", self.out)[0], 0)
        with open(os.path.join(self.out, "contact_sheet.html"), encoding="utf-8") as f:
            s = f.read()
        self.assertNotIn("<b>", s)

    # one-sided empty text is refused
    def test_onesided_empty_text_exit_5(self):
        pdf = fixture("junkkid.pdf", self.tmp)  # poppler page 2 is the blank junk kid, pypdf page 2 says "PAGE 2"
        code, _, err = run(pdf, "--pages", "2", "-o", self.out)
        self.assertEqual(code, 5, err)
        self.assertIn("malformed page tree at", err)  # the text rule itself is covered by test_onesided_unit
        self.assertEqual(self.pngs(), [])

    def test_onesided_unit(self):
        self.assertEqual(page_render.empty_side("", "x"), ("poppler", "pypdf"))
        self.assertIsNone(page_render.empty_side("", " \n"))
        self.assertIsNone(page_render.empty_side("a", "b"))

    # structural cross-check (box + rotation) works on image-only pages
    def image_only_shift(self, junk_at):
        pdf = os.path.join(self.tmp, "imgshift.pdf")
        with open(pdf, "wb") as f:
            f.write(fixtures.build_pdf(fixtures.SPEC[:4], draw="rect", junk_at=junk_at))
        return pdf

    def test_structural_image_only_shift_exit_5(self):
        pdf = self.image_only_shift(1)
        self.assertEqual(subprocess.run(["/opt/homebrew/bin/pdftotext", pdf, "-"], stdout=subprocess.PIPE
                                        ).stdout.strip(), b"")  # really image-only: no text anywhere
        code, _, err = run(pdf, "--pages", "all", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 5, err)
        self.assertIn("malformed page tree at", err)
        self.assertEqual(self.pngs(), [])

    def test_structural_clean_image_only_ok(self):
        pdf = self.image_only_shift(None)
        code, _, err = run(pdf, "--pages", "all", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 0, err)

    def test_structural_rotation_mismatch_unit(self):
        self.assertIsNone(page_render.geometry_mismatch((612, 792, 0), (612.4, 792, 0)))
        self.assertIsNotNone(page_render.geometry_mismatch((612, 792, 0), (612.6, 792, 0)))
        self.assertIsNotNone(page_render.geometry_mismatch((612, 792, 90), (612, 792, 0)))

    # ---- single-engine design: malformed trees refused, pypdf alone selects each page ----
    def test_malformed_tree_scan_junk_exit_5(self):
        pdf = fixture("scan_junk.pdf", self.tmp)
        for spec in ("all", "3-5"):
            shutil.rmtree(self.out, ignore_errors=True)
            code, _, err = run(pdf, "--pages", spec, "-o", self.out)
            self.assertEqual(code, 5, (spec, err))
            self.assertIn("malformed page tree at", err)
            self.assertIn("refusing; repair the PDF first", err)
            self.assertEqual(self.pngs(), [])

    def test_malformed_tree_ecf_junk_exit_5(self):
        pdf = fixture("ecf_junk.pdf", self.tmp)
        code, _, err = run(pdf, "--pages", "all", "-o", self.out)
        self.assertEqual(code, 5, err)
        self.assertIn("malformed page tree at", err)
        self.assertEqual(self.pngs(), [])

    def test_wellformed_image_only_scan_each_png_has_own_marker(self):
        pdf = os.path.join(self.tmp, "scan.pdf")
        with open(pdf, "wb") as f:
            f.write(fixtures.build_pdf([(400, 300, 0)] * 6, draw="marker"))
        code, _, err = run(pdf, "--pages", "all", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 0, err)
        for p in range(1, 7):
            w, h, rows = decode_png(os.path.join(self.out, "scan-p%04d.png" % p))
            row = rows[h - 30]  # inside the box (PDF y 20..120 -> pixel rows h-120..h-20)
            dark = [x for x in range(w) if row[x * 3] < 80]
            self.assertTrue(dark, p)
            self.assertEqual(int(round((dark[0] - 10) / 30.0)) + 1, p)

    def test_extracted_page_is_single_page_and_shifting_renderer_cannot_misselect(self):
        pdf = os.path.join(self.tmp, "scan.pdf")
        with open(pdf, "wb") as f:
            f.write(fixtures.build_pdf([(400, 300, 0)] * 6, draw="marker"))
        from pypdf import PdfReader
        one = page_render.extract_single(PdfReader(pdf), 4, self.tmp)
        out = subprocess.run(["/opt/homebrew/bin/pdfinfo", one], stdout=subprocess.PIPE,
                             universal_newlines=True).stdout
        self.assertIn("Pages:           1", out)
        # a renderer that always asks for page N+1 now has nothing to pick: it must fail, never render a wrong page
        code, _, err = run(pdf, "--pages", "2", "-o", self.out,
                           PAGE_RENDER_PDFTOPPM=os.path.join(STUBS, "shift_pdftoppm.py"))
        self.assertEqual(code, 5, err)
        self.assertEqual(self.pngs(), [])

    def test_exact_text_agreement(self):
        self.assertTrue(page_render.texts_agree("PAGE 1  x", "PAGE 1\nx"))
        self.assertFalse(page_render.texts_agree("filed 10/02 page 3 of 9 case 12", "filed 10/02 page 4 of 9 case 12"))

    # ---- round 3: catalog-level settings survive; two independent render paths must agree ----
    def test_ocg_hidden_layer_stays_hidden(self):
        pdf = fixture("ocg.pdf", self.tmp)
        code, _, err = run(pdf, "--pages", "1", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 0, err)
        w, h, rows = decode_png(os.path.join(self.out, "ocg-p0001.png"))
        px = rows[400][400 * 3:400 * 3 + 3]
        self.assertEqual(list(px), [255, 255, 255])

    def test_needappearances_form_passes(self):
        pdf = fixture("form_needapp.pdf", self.tmp)
        code, _, err = run(pdf, "--pages", "all", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.pngs()), 4)

    def test_extract_single_clones_catalog_and_keeps_page_identity(self):
        from pypdf import PdfReader
        r = PdfReader(fixture("ocg.pdf", self.tmp))
        one = page_render.extract_single(r, 3, self.tmp)
        r1 = PdfReader(one)
        self.assertEqual(len(r1.pages), 1)
        self.assertIn("/OCProperties", r1.trailer["/Root"])
        self.assertEqual(r1.pages[0].get_contents().get_data(), r.pages[2].get_contents().get_data())

    def test_render_mismatch_between_paths_exit_5(self):
        pdf = fixture("same.pdf", self.tmp)
        code, _, err = run(pdf, "--pages", "2", "--dpi", "72", "-o", self.out,
                           PAGE_RENDER_PDFTOPPM=os.path.join(STUBS, "gray_for_one.py"))
        self.assertEqual(code, 5, err)
        self.assertIn("render mismatch on page 2", err)
        self.assertEqual(self.pngs(), [])

    # ---- round 4: pypdf-vs-poppler text compare is advisory; pixel identity decides ----
    def kern_pdf(self):
        pdf = os.path.join(self.tmp, "big.pdf")
        with open(pdf, "wb") as f:
            f.write(fixtures.build_pdf([(300, 300, 0)] * 3, draw="kern"))
        return pdf

    def test_text_spacing_difference_warns_but_exits_0(self):
        pdf = self.kern_pdf()
        code, _, err = run(pdf, "--pages", "all", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 0, err)
        self.assertIn("warning: page 1: text differ", err)
        with open(os.path.join(self.out, "manifest.tsv")) as f:
            rows = [l.split("\t") for l in f.read().splitlines()]
        self.assertEqual(rows[0][-1], "text_check")
        self.assertEqual([r[-1] for r in rows[1:]], ["differ"] * 3)

    def test_manifest_text_check_values(self):
        pdf = fixture("form_needapp.pdf", self.tmp)
        self.assertEqual(run(pdf, "--pages", "1", "--dpi", "72", "-o", self.out)[0], 0)
        with open(os.path.join(self.out, "manifest.tsv")) as f:
            self.assertEqual(f.read().splitlines()[1].split("\t")[-1], "skipped-annots")
        self.assertEqual(page_render.text_status("", "x", False), "one-empty")
        self.assertEqual(page_render.text_status("a", "b", False), "differ")
        self.assertEqual(page_render.text_status("a", "a", False), "agree")
        self.assertEqual(page_render.text_status("", "", False), "agree")
        self.assertEqual(page_render.text_status("a", "b", True), "skipped-annots")

    # fix 7: UserUnit
    def test_fix7_userunit_exit_3(self):
        pdf = fixture("uu.pdf", self.tmp)
        code, _, err = run(pdf, "--pages", "all", "--dpi", "72", "-o", self.out)
        self.assertEqual(code, 3, err)
        self.assertIn("page 1", err)
        self.assertIn("UserUnit", err)
        self.assertEqual(self.pngs(), [])

    def test_fix7_userunit_only_checked_for_requested_pages(self):
        pdf = os.path.join(self.tmp, "uu1.pdf")
        data = fixtures.build_named("uu.pdf")
        head, sep, tail = data.partition(b"/UserUnit 2")  # keep page 1's UserUnit 2, reset the rest to 1
        with open(pdf, "wb") as f:
            f.write(head + sep + tail.replace(b"/UserUnit 2", b"/UserUnit 1"))
        self.assertEqual(run(pdf, "--pages", "1", "-o", self.out)[0], 3)
        shutil.rmtree(self.out, ignore_errors=True)
        self.assertEqual(run(pdf, "--pages", "2", "--dpi", "72", "-o", self.out)[0], 0)


class FixtureBuildTests(unittest.TestCase):
    """The fixtures are built, never tracked: two builds must give the same bytes."""

    def test_every_named_fixture_builds_identically_twice(self):
        for name in sorted(fixtures.NAMED):
            self.assertEqual(fixtures.build_named(name), fixtures.build_named(name), name)

    def test_every_named_fixture_is_distinct_and_not_empty(self):
        built = [fixtures.build_named(n) for n in sorted(fixtures.NAMED)]
        self.assertTrue(all(b.startswith(b"%PDF-") and b.rstrip().endswith(b"%%EOF") for b in built))
        self.assertEqual(len(set(built)), len(built))

    def test_default_build_pdf_is_deterministic(self):
        self.assertEqual(fixtures.build_pdf(fixtures.SPEC), fixtures.build_pdf(fixtures.SPEC))

    def test_write_named_writes_the_built_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            path = fixtures.write_named("same.pdf", d, "other name.pdf")
            self.assertEqual(os.path.basename(path), "other name.pdf")
            with open(path, "rb") as f:
                self.assertEqual(f.read(), fixtures.build_named("same.pdf"))

    def test_built_facts(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as d:
            def r(name):
                return PdfReader(fixtures.write_named(name, d))
            for name in ("same.pdf", "crop.pdf", "cropbig.pdf", "inhrot.pdf", "uu.pdf", "ocg.pdf",
                         "form_needapp.pdf", "corrupt.pdf"):
                self.assertEqual(len(r(name).pages), 4, name)
            for name in ("scan_junk.pdf", "ecf_junk.pdf"):
                self.assertEqual(len(r(name).pages), 5, name)
            self.assertEqual([float(v) for v in r("crop.pdf").pages[0]["/CropBox"]], [0, 300, 612, 792])
            self.assertEqual([float(v) for v in r("cropbig.pdf").pages[0]["/CropBox"]], [-50, -50, 662, 842])
            self.assertEqual(r("inhrot.pdf").pages[0].rotation, 90)
            self.assertNotIn("/Rotate", r("inhrot.pdf").trailer["/Root"]["/Pages"]["/Kids"][0])
            self.assertEqual(r("uu.pdf").pages[3]["/UserUnit"], 2)
            self.assertIn("/OCProperties", r("ocg.pdf").trailer["/Root"])
            self.assertIn("/AcroForm", r("form_needapp.pdf").trailer["/Root"])
            self.assertEqual(r("junkkid.pdf").trailer["/Root"]["/Pages"]["/Count"], 4)
            self.assertEqual(len(r("junkkid.pdf").trailer["/Root"]["/Pages"]["/Kids"]), 5)
            self.assertEqual(len(r("scan_junk.pdf").trailer["/Root"]["/Pages"]["/Kids"]), 6)
            self.assertIn(b"PAGE 3", r("same.pdf").pages[2].extract_text().encode())
            self.assertEqual(r("scan_junk.pdf").pages[0].extract_text().strip(), "")
            self.assertIn("HEADER LINE 1", r("ecf_junk.pdf").pages[0].extract_text())


class UnitTests(unittest.TestCase):
    def test_parse_pages(self):
        self.assertEqual(page_render.parse_pages("3,1-2,2", 5), [1, 2, 3])
        self.assertEqual(page_render.parse_pages("ALL", 3), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
