HEXAPOD SUPERVISOR REVIEW - 29 OCTOBER 2026

Open these first:
1. Research_Preview.png: quick visual summary.
2. IEEE_Access_Hexapod_Validated_Manuscript.pdf: full 18-page paper.
3. The matching .docx: editable manuscript using the official IEEE Access template.
4. Comparison_Offline.html: double-click to inspect fresh primary results without the local server. Choose PSO + polishing or ACO + polishing as baseline. Choosing V4 will correctly show ties with V5.

Local website: http://127.0.0.1:8771/comparison/
Experiment console: http://127.0.0.1:8771/
Use "Load completed V5 comparison" for the extension. Use "Load preserved V4 comparison" for the original campaign. Saved phase links distinguish physics, planning, candidate caps and budget tests.

WHAT CHANGED
Added 800 scheduled attempts across nine phases, 8 fresh development worlds and 48 fresh primary test worlds. Each competitive method received two development profiles. Parameters and sources were frozen before test outcomes. Feature-removal controls, shorter budgets, an 80-route-candidate ceiling, all-metric-call counters and assistance sensitivity were added.

MAIN FINDING
V4 and V5 each admit 94/96 fresh primary attempts. Polished PSO and ACO each admit 92/96. V4 and V5 return identical saved route coordinates in all 96 matched attempts; V5 takes more planner time on average. V4 therefore remains recommended. Paired mean gains over polished controls are about 1.42% and 1.41%, with world-level uncertainty in the paper. Median world improvement is zero; one 41.1% improvement has a large influence on the mean. Physics failures are retained; planning admission does not guarantee mission completion. Exact results and diagnostics are in tables and source/extension_analysis.json.

EVIDENCE AND REPRODUCTION
S1 retains the original 1,232-attempt evidence ZIP unchanged. S2 contains the 800-attempt campaign, original source snapshots and original model XML. A separate reproduction copy includes assets with documented path-only relocation. SHA256SUMS.json inventories package payloads. Repeated seeds and secondary phases do not create additional independent worlds. Audits check internal provenance and arithmetic, not physical realism.

REVIEW STATUS: SHARE WITH CAVEATS
Read the limitations before submission. Dynamic execution can fail despite planning admission. Assistance blending is not unassisted locomotion; gravity compensation remains active. Battery coefficients are nominal and mechanical work is not electrical consumption. No physical robot or real battery measurement was performed. Broader external planner implementations and out-of-distribution maps remain future work.

Author shown as Tomato. Affiliation, corresponding email, biography, funding and declarations need author confirmation. Public repository/DOI has not been assigned. Final technical review, reference checks and novelty assessment remain for the author and supervisor. The AI-assistance disclosure is retained. No paper has been submitted or published.

VERIFICATION LIMIT
All final manuscript pages and scientific figures were visually reviewed. The dashboard was built and its served snapshot/HTTP delivery verified. No browser surface was available for interactive visual testing; browser-only filter, theme and export interactions have not been visually certified.
