HEXAPOD FINAL SIMULATION PACKAGE

START HERE
1. IEEE_Access_Hexapod_Final_Manuscript.docx: full editable 19-page article.
2. Matching PDF: fixed-layout reading copy.
3. Research_Preview.png: quick result comparison.
4. Comparison_Offline.html: double-click to inspect all 576 fresh primary planning records without a local server.
5. tables/All_1200_Final_Attempts.csv: every new scheduled record, including rejected plans and failed missions.

WHAT WAS IMPLEMENTED
Shared safe follower with alignment hysteresis, checked waypoint connectors, braking and bounded checked recovery; actual OMPL 2.0.1 RRT*, RRT* with a common candidate-pool incumbent, and RRTConnect plus shared final polishing; two-profile development selection per method; fresh standard/shifted worlds; weight and budget sensitivity; exact saved-primary-route controller replays; independent audit; improved missing-value explanations; direct local download buttons; full journal revision and real electrical-data ingestion/calibration templates.

WHAT THE RESULTS MEAN
The proposal admits 90/96 primary attempts. See the article for every control and the conditional paired score results; it does not win every experiment or every metric. Revised safe tracking yields 12/12 scheduled proposal successes versus 12/12 legacy successes on the exact same saved routes. V6 names the mission pipeline and final protocol, while the route optimizer remains V4. The earlier V5 adaptive planner returned identical routes to V4 and was not promoted as a better algorithm.

EVIDENCE
S1: unchanged original 1,232 attempts, 24 test worlds. S2: separate 800 attempts, 48 new test worlds. S3: final 1,200 scheduled records, 48 new test worlds, 12 phases. Total 3,232 records are not 3,232 independent maps. Each primary method in S3 has two repeats on the same 48 worlds. Sensitivity and physics replays reuse subsets. SHA256SUMS.json hashes every package payload. The full earlier 18-page report remains in prior_full_report.

WEBSITE ON THE ORIGINAL COMPUTER
http://127.0.0.1:8771/ — experiment console.
http://127.0.0.1:8771/comparison/ — side-by-side charts.
Choose “Load completed final comparison” to restore the final primary dataset. Saved phase links distinguish planning, weights, budgets and assisted execution. Use “Use selected run in charts” after selecting another saved phase. Final DOCX/PDF/ZIP download links appear in the console. This is a local service, not a public website. The offline HTML is the portable alternative.

REMAINING AUTHOR AND SCIENTIFIC WORK
The package is finalized for its present simulation scope and supervisor review, not guaranteed journal acceptance. Author full identity, institution, email, biography, ORCID, funding, declarations and public evidence archive need confirmation. Review the contribution and references with your supervisor. Simulation still uses prescribed body assistance and gravity compensation. Terrain exposure is a proxy and battery use is a nominal ledger. No real battery reading, unassisted locomotion or physical robot result was obtained. Empty electrical templates are a workflow, not completed hardware validation. Broader native heading-state and unrestricted continuous swarm controls remain useful future comparisons. No paper has been submitted or published.

VERIFICATION
All manuscript pages and scientific figures were visually reviewed. Fifty automated software checks passed. The final 1,200-record audit passed. Dashboard build, raw-data row reconciliation and loopback HTTP delivery were checked. No enabled browser surface was available; browser filter/theme/export interactions were not visually certified.
