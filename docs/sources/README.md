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
