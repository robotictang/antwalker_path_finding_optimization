# Revised robot illustration

The current article uses a direct static capture of the primary MuJoCo model as Figure 1 on page 2. The image is centered at 4.5 inches wide, reduced from the preceding 6-inch screenshot. The manuscript remains 10 pages with seven figures, nine tables and three equations.

- [Word manuscript](IJ3C_Manuscript.docx)
- [Matching PDF](IJ3C_Manuscript.pdf)
- [Robot image](figures/simulation_overview.png)
- [Narrative source](IJ3C_Manuscript.md)
- [Template review](Template_Review.md)
- [Evidence map](Evidence_Map.md)
- [Previous template-checked manuscript](../publication_2026_11_04_template_checked/README.md)

The 2400 by 1500 image shows the robot at the walking initialization used in research/execution.py. It was captured directly with MuJoCo EGL, without advancing physics or launching a live viewer or server. The surrounding world geometry is hidden in the renderer; a gray floor, even lighting and a closer camera isolate the robot. Robot geometry and the frozen source model file are unchanged. No AI image generation or pixel editing was used. The caption identifies the image as a static model view.

The original image bytes are embedded once in the Word file (about 533 pixels per inch at the selected width); the PDF exports at 300 pixels per inch. The source model hash, camera, initialization state and display changes are recorded in results/screenshot_provenance.json. The capture script is source/capture_robot.py and uses the scientific system Python runtime.

Only the Figure 1 description and caption changed in the article. All numerical study results and other research text are unchanged. The original supplied screenshot remains in figures/previous_user_screenshot.png, and preceding revisions remain preserved.

All ten final pages were visually inspected. Template formatting, embedded fonts, figure/table/citation order, capture identity and source/data consistency checks pass. Author fields remain unfilled and the acknowledgment stays outside the article in Deferred_Disclosure.md, following earlier instructions. No journal submission has been made.
