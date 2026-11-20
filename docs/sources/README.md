# Sources

`fc4055.xml` and `fc4055.txt` hold California Family Code section 4055, the
version added by Stats. 2023, ch. 213, sec. 3, operative September 1, 2024.
The calculator's formula follows this text and no other source. Where the text
is silent, the report labels the toolkit's own reading. The minimum wage is a
number the person enters.

## Where it comes from

The Legislature's bulk data at downloads.leginfo.legislature.ca.gov: file
`pubinfo_2025.zip`, member `LAW_SECTION_TBL_21615.lob`. `fc4055.xml` was
extracted from that member on 2026-10-19. A copy extracted on 2026-11-02 from a
fresh download has the same sha256. The Legislature republishes this file, and
its member names can change, so a later download may differ.

## Check it

From this directory, run:

    shasum -a 256 fc4055.xml fc4055.txt

It should print:

    63803b8acd6555bc395704bec61ebcbc1a8b7556e0a2a783e12e2f0253e8a463  fc4055.xml
    aa644b4255702ff9f542648a835da29cd26da468d7a2748f62153870cde9b998  fc4055.txt

`fc4055.txt` is `fc4055.xml` with each closing `</p>` turned into a line
break, the other tags removed, HTML entities decoded, and spaces around line
breaks trimmed. `tests/test_sources.py` repeats that conversion and checks
both hashes.

## FC 4061 and FC 4062

`fc4061.xml` / `fc4061.txt` and `fc4062.xml` / `fc4062.txt` hold California
Family Code sections 4061 (apportionment of additional expenses) and 4062
(additional child support), each the version added by Stats. 2023, ch. 213,
sec. 3 (SB 343), operative September 1, 2024. The support command's
additional-child-support section builds on them; the spec,
`docs/specs/add-ons.md`, quotes them.

### Where they come from

The same Legislature bulk data as FC 4055, retrieved 2026-11-19 from
https://downloads.leginfo.legislature.ca.gov/pubinfo_2025.zip (the server
reported last-modified Mon, 16 Nov 2026 05:26:36 GMT; zip sha256
`d8898186fa37ff83855efdb5b3a136c60710c4b4cd2377513610d766c9fb935d`). The
table `LAW_SECTION_TBL.dat` names each section's text file: `FAM4061.20232133`
is `LAW_SECTION_TBL_21567.lob`, and `FAM4062.20232133` is
`LAW_SECTION_TBL_34598.lob`. Those two members, unchanged, are
`fc4061.xml` and `fc4062.xml`. The member names differ between downloads: in
this download FC 4055 is `LAW_SECTION_TBL_21561.lob`, and its sha256 is the
same as `fc4055.xml`'s, which is how this download was checked against the
earlier one. The Legislature's section web pages (leginfo.legislature.ca.gov)
refused an automated fetch on 2026-11-19, so they were not used.

The `.lob` members hold the section text only. The history line in each
section's record (`Repealed (in Sec. 8) and added by Stats. 2023, Ch. 213, Sec.
3. (SB 343) Effective January 1, 2024. Operative September 1, 2024, by its own
provisions.` for 4061; the same with `Sec. 10` for 4062) is in
`LAW_SECTION_TBL.dat`, not in the files here.

### Check them

From this directory, run:

    shasum -a 256 fc4061.xml fc4061.txt fc4062.xml fc4062.txt

It should print:

    443f3671108fdeece78465bfb7ef3c6bf491ed8d10b3725e580d49faeda3a56a  fc4061.xml
    df2c6cbafc688c86987bbb44639356bf215e752626b862cc704a9221101bf2ad  fc4061.txt
    5040d4045b0d0e334b984d4ce2e5ab98e6d335b21763c2db07124e2edbbbc355  fc4062.xml
    689fd81466a045404e94e935bbfa8e1bd0a2a31b38a86e965851d7d5c1c10fbb  fc4062.txt

The `.txt` files are made from the `.xml` files by the same conversion as
`fc4055.txt`. `tests/test_sources.py` pins these four hashes and repeats that
conversion for each pair.
