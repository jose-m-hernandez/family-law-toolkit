# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jose Miguel Hernandez
"""Hand-built synthetic PDFs (stdlib only). Every page has a distinct size and a big marker."""


def build_pdf(pages, encrypt=False, draw="text", junk_at=None):
    """pages: list of (width, height, rotate). Returns bytes."""
    objs = []  # 1-based object bodies

    def add(b):
        objs.append(b)
        return len(objs)

    cat = add(b"")      # 1 catalog placeholder
    pgs = add(b"")      # 2 pages placeholder
    font = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    kids = []
    for i, (w, h, rot) in enumerate(pages, 1):
        if draw == "marker":  # same-size image-only stand-in: only the x position of a dark box tells pages apart
            text = ("0 g %d 20 20 %d re f" % (10 + 30 * (i - 1), int(h / 3))).encode()
        elif draw == "kern":  # poppler reads "P0", pypdf reads "P 0" (the big300 case)
            text = b"BT /F1 20 Tf 20 100 Td [(P) -300 (0)] TJ ET"
        elif draw == "rect":  # image-only stand-in: no text operators at all
            text = ("0 g 20 20 %d %d re f" % (int(w / 3), int(h / 3))).encode()
        else:
          text = ("BT /F1 %d Tf 20 %d Td (PAGE %d) Tj ET" % (int(min(w, h) / 8), int(h / 2), i)).encode()
        c = add(b"<< /Length %d >>\nstream\n" % len(text) + text + b"\nendstream")
        p = add(("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] /Rotate %d "
                 "/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
                 % (w, h, rot, font, c)).encode())
        kids.append(p)
    if junk_at is not None:  # a non-page object (an annotation) in /Kids: pypdf skips it, poppler counts it
        junk = add(b"<< /Type /Annot /Subtype /Square /Rect [0 0 10 10] >>")
        kids.insert(junk_at, junk)
    objs[cat - 1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[pgs - 1] = ("<< /Type /Pages /Count %d /Kids [%s] >>"
                     % (len(pages), " ".join("%d 0 R" % k for k in kids))).encode()
    out = bytearray(b"%PDF-1.4\n")
    offs = []
    for n, body in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


# 12 pages (so pdftoppm's multi-digit padding matters): distinct sizes; p4 landscape, p7 rotated 90, p10 rotated 270
SPEC = []
for n in range(1, 13):
    SPEC.append((300 + 10 * n, 400 + 10 * n, 0))
SPEC[3] = (700, 450, 0)
SPEC[6] = (320, 520, 90)
SPEC[9] = (330, 530, 270)


# ---- named letter-size fixtures, written into a temporary directory at test set-up ----
#
# Nothing here is a tracked binary. Every file is assembled from fixed text and fixed object
# numbers with the standard library only: no clock, no random id and no compression is used
# (the one deliberate exception, the truncated stream in "corrupt.pdf", is zlib at its fixed
# default level, which is deterministic), so two builds give identical bytes.

import zlib

_FONT_DICT = b"<< /F1 4 0 R /F2 5 0 R >>"
_PROCSET = b"[ /PDF /Text /ImageB /ImageC /ImageI ]"
_PAGE_BODY = (b"1 0 0 1 0 0 cm  BT /F1 12 Tf 14.4 TL ET\n"
              b"BT /F2 60 Tf 72 TL ET\n"
              b"BT 1 0 0 1 100 600 Tm (PAGE %d) Tj T* ET\n"
              b"n %d 100 60 60 re B*\n \n")
_HEADER_BODY = (b"1 0 0 1 0 0 cm  BT /F1 12 Tf 14.4 TL ET\n"
                b"BT /F1 8 Tf 9.6 TL ET\n"
                b"BT 1 0 0 1 40 770 Tm (HEADER LINE 1 PAGE %d OF %d) Tj T* ET\n"
                b"n %d 100 60 60 re B*\n \n")
_IMAGE_BODY = b"1 0 0 1 0 0 cm  BT /F1 12 Tf 14.4 TL ET\nn %d 100 60 60 re B*\n \n"
_HIDDEN_LAYER = b"/OC /oc1 BDC 0 0 1 rg 300 300 200 200 re f EMC"


def _stream(data, extra=b""):
    return b"<< %s/Length %d >>\nstream\n" % (extra, len(data)) + data + b"\nendstream"


def _assemble(objs):
    """objs: list of object bodies, object number = list position + 1. Object 1 is the catalog."""
    out = bytearray(b"%PDF-1.4\n")
    offs = []
    for n, body in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


def build_letter(pages=4, body="text", junk_at=None, broken_page=None, cropbox=None,
                 pages_rotate=None, userunit=None, ocg=False, widget=False):
    """Letter-size pages (612 x 792). body: "text" (PAGE n marker), "header" (a header band of
    plain words, then a box) or "image" (a box only, no text operators shown).
    junk_at: index in /Kids of a non-page object. /Count stays the number of real pages.
    broken_page: 1-based page whose content stream is cut off inside its flate data.
    cropbox: text of the /CropBox array. pages_rotate: /Rotate on the /Pages node only.
    userunit: /UserUnit on every page. ocg: a hidden optional-content layer drawn on every page.
    widget: one text field annotation on page 1 and an /AcroForm with NeedAppearances."""
    objs = [b"", b"", _FONT_DICT,
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding /Name /F1 >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding /Name /F2 >>"]
    # object 1 is the catalog, 2 the page tree, 3 the font dictionary, 4 and 5 the fonts
    ocg_obj = widget_obj = None
    page_nums = []
    props = b""
    if ocg:
        objs.append(b"<< /Type /OCG /Name (Hidden) >>")
        ocg_obj = len(objs)
        props = b" /Properties << /oc1 %d 0 R >>" % ocg_obj
    next_page = len(objs) + 1
    n_objs_per_page = 2 + (1 if ocg else 0)
    widget_obj = next_page + pages * n_objs_per_page if widget else None
    for i in range(1, pages + 1):
        x = 50 + 100 * (i - 1)
        if body == "text":
            data = _PAGE_BODY % (i, x)
        elif body == "header":
            data = _HEADER_BODY % (i, pages, x)
        else:
            data = _IMAGE_BODY % x
        if i == broken_page:
            # the first 36 bytes, deflated, with the last 6 bytes (end-of-data block and checksum) cut off
            objs.append(_stream(zlib.compress(data[:36])[:-6], b"/Filter /FlateDecode "))
        else:
            objs.append(_stream(data))
        c = len(objs)
        contents = b"%d 0 R" % c
        if ocg:
            objs.append(_stream(_HIDDEN_LAYER))
            contents = b"[ %d 0 R %d 0 R ]" % (c, len(objs))
        parts = [b"/Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"]
        if pages_rotate is None:
            parts.append(b"/Rotate 0")
        if cropbox:
            parts.append(b"/CropBox " + cropbox.encode())
        if userunit:
            parts.append(b"/UserUnit %d" % userunit)
        if widget and i == 1:
            parts.append(b"/Annots [ %d 0 R ]" % widget_obj)
        parts.append(b"/Resources << /Font 3 0 R /ProcSet " + _PROCSET + props + b" >>")
        parts.append(b"/Contents " + contents)
        objs.append(b"<< " + b" ".join(parts) + b" >>")
        page_nums.append(len(objs))
    if widget:
        objs.append(b"<< /Type /Annot /Subtype /Widget /FT /Tx /T (field1) /V (FIELD VALUE 1) "
                    b"/Rect [100 400 500 440] /DA (/Helv 24 Tf 0 g) /P %d 0 R >>" % page_nums[0])
    kids = list(page_nums)
    if junk_at is not None:
        objs.append(b"<< /Type /Annot >>")
        kids.insert(junk_at, len(objs))
    extra = b""
    if widget:
        objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Name /Helv >>")
        extra += (b" /AcroForm << /Fields [ %d 0 R ] /NeedAppearances true /DR << /Font << /Helv %d 0 R >> >>"
                  b" /DA (/Helv 0 Tf 0 g) >>" % (widget_obj, len(objs)))
    if ocg:
        extra += b" /OCProperties << /OCGs [ %d 0 R ] /D << /OFF [ %d 0 R ] >> >>" % (ocg_obj, ocg_obj)
    objs[0] = b"<< /Type /Catalog /Pages 2 0 R /PageMode /UseNone" + extra + b" >>"
    rot = b" /Rotate %d" % pages_rotate if pages_rotate is not None else b""
    objs[1] = (b"<< /Type /Pages /Count %d /Kids [ %s ]%s >>"
               % (pages, b" ".join(b"%d 0 R" % k for k in kids), rot))
    return _assemble(objs)


# name of the file a test asks for -> how it is built. The names are the names the tests use,
# and the output PNG names follow them.
NAMED = {
    "same.pdf": {},                                    # four plain text pages
    "junkkid.pdf": dict(junk_at=1),                    # a non-page object at /Kids[1], /Count 4
    "corrupt.pdf": dict(broken_page=2),                # page 2 content cut off inside flate data
    "crop.pdf": dict(cropbox="[0 300 612 792]"),       # CropBox smaller than MediaBox
    "cropbig.pdf": dict(cropbox="[-50 -50 662 842]"),  # CropBox larger than MediaBox
    "inhrot.pdf": dict(pages_rotate=90),               # /Rotate 90 on the /Pages node only
    "uu.pdf": dict(userunit=2),                        # /UserUnit 2 on every page
    "ocg.pdf": dict(ocg=True),                         # blue square in an optional layer that starts hidden
    "form_needapp.pdf": dict(widget=True),             # one text field, NeedAppearances true
    "scan_junk.pdf": dict(pages=5, body="image", junk_at=1),    # image-only pages, junk kid, /Count 5
    "ecf_junk.pdf": dict(pages=5, body="header", junk_at=1),    # header-band text, junk kid, /Count 5
}


def build_named(name):
    return build_letter(**NAMED[name])


def write_named(name, dest_dir, as_name=None):
    """Write the named fixture into dest_dir (a temporary directory) and return its path."""
    import os
    path = os.path.join(dest_dir, as_name or name)
    with open(path, "wb") as f:
        f.write(build_named(name))
    return path
