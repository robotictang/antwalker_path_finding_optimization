# IEEE Access LaTeX manuscript with author biographies

Open **manuscript.tex** as the main document and use **pdfLaTeX**. Upload the
complete source ZIP to Overleaf, or extract it into a new folder and build
from that folder with TeX Live.

    pdflatex -halt-on-error -interaction=nonstopmode manuscript.tex
    pdflatex -halt-on-error -interaction=nonstopmode manuscript.tex

The bibliography is embedded in the manuscript. The source includes the
IEEE Access class and support files, the research figures, and all nine
supplied author portraits.

Edit the byline, affiliations, and contact emails in **author-details.tex**.
The two email addresses come from the Word manuscript. The corresponding
author role is left open for confirmation. Publication dates, DOI, volume,
and year are assigned by the journal.

Edit the biographies in **author-biographies.tex**. They appear in byline
order after the references. Their text and portraits come from the latest
author biography document. The displayed names follow the article byline.

The appendix uses the standard LaTeX multicol package for two-column prose
and full-width tables. The reported table entries and results are preserved.
