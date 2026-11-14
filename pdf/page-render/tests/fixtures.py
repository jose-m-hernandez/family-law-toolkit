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
