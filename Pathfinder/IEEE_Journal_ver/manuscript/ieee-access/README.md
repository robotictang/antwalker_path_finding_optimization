# IEEE Access review source

Open **manuscript.tex** as the main document. This directory contains the article source, editable author metadata, the figures and the support files from the official [IEEE Access LaTeX template](https://ieeeaccess.ieee.org/authors/preparing-your-article/) dated May 13, 2026. The official support files are copied unchanged.

Select **pdfLaTeX**. With TeX Live installed, build from this directory:

    pdflatex -halt-on-error -interaction=nonstopmode manuscript.tex
    pdflatex -halt-on-error -interaction=nonstopmode manuscript.tex

The bibliography is embedded in the source. There is no separate BibTeX step.

The byline, affiliations and corresponding-author fields in **author-details.tex** are review placeholders. Confirm author order, affiliations, email, biographies and funding information before preparing the submission version. The draft contains an AI-use acknowledgment for author review. Journal-assigned publication metadata uses placeholders.
