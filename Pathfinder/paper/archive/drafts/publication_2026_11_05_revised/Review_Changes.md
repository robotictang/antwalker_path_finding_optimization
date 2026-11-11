# Revision changes 5 November 2026

## Scientific and editorial changes

- Retitled and refocused the Introduction, Abstract, Discussion and Conclusions around constrained body-route planning and the measured value of its stages.
- Added Algorithm 1 and Table 1 for implementation and selected settings, checked against the retained source. Removed the repeated numerical parameter lists from prose while retaining Gaussian initialization, point representation and budget rules.
- Added verified references to Ma's resource-constrained label-setting work and Guo et al.'s 2025 PSO/control-barrier study. These contextual comparisons do not claim to reproduce or outperform those methods. Renumbered all citations.
- Explained score denominators as fixed trade-offs, correlated distance/time/battery terms, and the arithmetic reserve policy. No calibration, tuning rationale or sensitivity result was invented.
- Identified non-worsening incumbent retention as an intended design property; quantified acceptance and computation remain the empirical findings.
- Preserved conditional score denominators, all ties/losses/rejections, the interval spanning zero, and the effect of omitting map 24.
- Condensed the assistance study and combined completion/contact outcomes. Preserved the four corrected preliminary runs, detector definition, realized compensation settings and restricted scope.

## Display changes from the preceding manuscript

| Previous material | Revised treatment |
|---|---|
| Figure 1 robot capture | Retained unchanged as Figure 1 |
| Figure 2 first-map overlap | Removed |
| Figure 3 acceptance bars | Removed; counts remain in Table 2 |
| Table 3 and Figure 4 paired means/intervals | Table 3 retained; plot removed |
| Table 4 map-family counts | Replaced by complete prose counts in Section 6.2 |
| Table 5 computation | Retained as Table 4 |
| Figure 5 map effects | Retained as Figure 2 |
| Table 6 full omission ranges | Shortened in Section 6.3; full unchanged analysis retained |
| Table 7 map-24 metrics | Replaced by numerical component comparisons in Section 6.4 |
| Figure 6 selected route | Retained as Figure 3 with post-hoc selection stated |
| Tables 8 and 9 motion/contact results | Combined as Table 5; timeouts stated explicitly |
| Figure 7 distance plot | Removed; distance and time ranges remain in Section 6.5 |
| Table 1 model descriptions | Replaced by explicit model values in Section 3.1 |

The new Table 1 presents planner settings rather than the removed model table. No observation was discarded from the analysis. Removed displays remain preserved in the preceding revision.

## Verification

The QA directory records structure, template formatting, font embedding, numbering, self-contained wording, raw-data reconciliation, source locks, image identity and the previous-file integrity check. New derived-study claims and experiments: zero. The preceding manuscripts and every shared raw/result file remain byte-for-byte unchanged.

The publication still requires the deliberately deferred author/contact information and final author/supervisor scientific approval. Additional baselines, objective sensitivity, harder unseen maps and hardware tests were not run and are not presented as completed work. The revised wording does not establish universal superiority, physical walking or electrical savings.
