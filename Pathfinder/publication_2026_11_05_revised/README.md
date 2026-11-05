# Revised IJ3C manuscript

The current article is **Constrained Route Planning for a Simulated Hexapod**. This revision has 9 pages, three figures, five tables, three equations and eleven references. It focuses on the benefit and computational cost of the planning stages and presents motion as a bounded simulator diagnostic.

- [PDF manuscript](IJ3C_Manuscript.pdf)
- [Editable Word manuscript](IJ3C_Manuscript.docx)
- [Complete plain-language text](IJ3C_Manuscript.md)
- [Revision notes](Review_Changes.md)
- [Template review](Template_Review.md)
- [Evidence map](Evidence_Map.md)
- [Preceding preserved revision](../publication_2026_11_04_robot_figure/README.md)

## Editing and evidence

Edit [source/article.md](source/article.md) for the narrative outline and fixed methods. [source/revision_content.py](source/revision_content.py) supplies the revised abstract, result paragraphs, algorithm and table definitions. [source/build_manuscript.py](source/build_manuscript.py) assembles these over the retained journal sample. Earlier content modules supply the existing analyses and native plots before the final editorial overrides.

The relative links raw_study/ and template/ reuse the preceding revision's unchanged evidence and official sample. Immutable result files also use relative links; the two builder-generated analysis summaries are separate identical copies. Keep the preceding revision alongside this folder when copying the project. This avoids duplicating the large evidence directories. The Word and PDF manuscripts are standalone reading copies.

All 640 planning attempts and sixteen valid motion executions are unchanged. There are no new simulation runs, tuned settings or sensitivity-study results. The robot image is the unchanged direct MuJoCo capture. Author/contact details remain as previously deferred; acknowledgment placement remains outside the article in [Deferred_Disclosure.md](Deferred_Disclosure.md).

The authoring environment uses the Codex bundled Python runtime, with matplotlib and its missing dependencies in a task-local directory. The renderer uses bundled LibreOffice and Poppler through the existing compatible loader. Scientific execution versions reported in the paper describe the saved experiments, not the document-building environment.
