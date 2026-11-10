# Final reference and citation check — 10 November 2026

Reviewed the current manuscript, SHA-256 `52f8a783cc392dbc8100f6921d8aa33e29845d55470187714f022d4f45d9ea96`, using the supplied P identifiers. Read-only review: the manuscript was not edited.

**Required factual corrections in the bibliography or literature claims: none found.** All 11 references are identifiable. The ten journal/conference DOIs were freshly resolved using publisher-deposited CSL/Crossref metadata; author order, titles, venues, volumes/issues, pages/article numbers, and publication years match the manuscript. The official COCO documentation was also checked. Raw metadata is in `reference_metadata_recheck.json`.

## Reference verification

| Paragraph | Reference | Result and primary source |
|---|---|---|
| P211 | [1] Todorov, Erez, Tassa | Correct, IROS 2012, pp. 5026–5033. [DOI](https://doi.org/10.1109/IROS.2012.6386109); [official MuJoCo recommended citation](https://github.com/google-deepmind/mujoco#citation). |
| P212 | [2] Hart, Nilsson, Raphael | Correct, 4(2), pp. 100–107, 1968. [DOI](https://doi.org/10.1109/TSSC.1968.300136); [original-paper university copy](https://people.stfx.ca/jdelamer/courses/csci-564/_downloads/b2220c66675ddde471ca1795147b8e86/A_Formal_Basis_for_the_Heuristic_Determination_of_Minimum_Cost_Paths.pdf). |
| P213 | [3] Kennedy, Eberhart | Correct, ICNN'95, vol. 4, pp. 1942–1948, 1995. [DOI](https://doi.org/10.1109/ICNN.1995.488968); [original-paper university copy](https://www.cs.tufts.edu/comp/150GA/homeworks/hw3/_reading6%201995%20particle%20swarming.pdf). |
| P214 | [4] Dorigo, Maniezzo, Colorni | Correct, 26(1), pp. 29–41, 1996. [DOI](https://doi.org/10.1109/3477.484436); [author publication list](https://iridia.ulb.ac.be/~mdorigo/HomePageDorigo/publicationsbyyear.php). |
| P215 | [5] Lozano-Pérez, Wesley | Correct, Communications of the ACM 22(10), pp. 560–570, 1979. [DOI](https://doi.org/10.1145/359156.359164); [original-paper author-site copy](https://lis.csail.mit.edu/pubs/tlp/collision-free-planning-cacm.pdf). |
| P216 | [6] Tai-Yu Ma | Correct, Procedia—Social and Behavioral Sciences 111, pp. 330–339, 2014. [DOI](https://doi.org/10.1016/j.sbspro.2014.01.066); [author's institutional record](https://liser.elsevierpure.com/en/publications/an-a-label-setting-algorithm-for-multimodal-resource-constrained-/). |
| P217 | [7] Bingbing Guo, Yuan Sun, Yiyang Chen | **The present author order is correct.** SAGE lists Guo first, Sun second, Chen third. Vol. 47, issue 9, pp. 1715–1724, **June 2025** is correct. Online-first was 19 August 2024; that does not invalidate the manuscript's 2025 issue citation. [SAGE publisher record and abstract](https://journals.sagepub.com/doi/10.1177/01423312241264860). |
| P218 | [8] Yunpeng Yin, Feng Gao, Qiao Sun, Yue Zhao, Yuguang Xiao | Correct, Chinese Journal of Mechanical Engineering 37(1), article 15, 2024. [Springer full text](https://link.springer.com/article/10.1186/s10033-024-01000-0). |
| P219 | [9] Chen Chen, Junbo Lin, Bo You, Jiayu Li, Biao Gao | Correct, Frontiers in Neurorobotics 19, article 1605938, 2025. [Publisher full text](https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2025.1605938/full). |
| P220 | [10] COCO Project | Identifiable official documentation; title and linked 2016 paper agree. Accessed 6 November 2026 is a valid past date. [Official procedure](https://numbbo.github.io/coco-doc/experimental-setup/). |
| P221 | [11] B. Efron | Correct, The Annals of Statistics 7(1), pp. 1–26, 1979. [DOI/publisher record](https://doi.org/10.1214/aos/1176344552). |

Some IEEE, ACM, Elsevier, and older author-site pages were blocked or timed out in this browser session. The successful DOI metadata, original-paper copies, and institutional records provide the fallback evidence. These access failures are not bibliographic defects. Guo's full text remains restricted; the publisher abstract supports the claim checked here.

## Citation claims

- **P8 / [1]: supported.** The original MuJoCo paper remains the citation explicitly recommended by the official project.
- **P10 / [2]–[5]: supported.** The summaries of A*'s cost-plus-heuristic priority, PSO's personal/swarm best updates, Ant System's pheromone/heuristic construction, and collision-free visibility links are accurate. The text makes no global-optimality claim for CLRP.
- **P10 / [6]: supported.** Ma combines A*-based label setting with multiple resource and mode-chain constraints on a multimodal transportation network. The manuscript distinguishes that network setting from its own planar robot paths.
- **P10 / [7]: supported by the publisher abstract.** The PSO/CBF safety-velocity mechanism is correctly described. The manuscript explicitly says it does not reproduce or evaluate their controller.
- **P10 / [8]: supported.** Smart Gait optimizes swing trajectories, gait period/duty, and gait sequence on LittleStrong.
- **P10 / [9]: supported.** Chen et al. combine terrain traversal costs, foothold costs, and free-gait planning, with simulation and physical experiments. The manuscript does not substitute its own assisted diagnostic for those results.
- **P10 / [10]: supported as methodological motivation.** The official procedure discusses initialization, parameter-setting/tuning disclosure, termination, evaluation counts, and timing. The manuscript's statements do not establish formal COCO compliance, but do not claim such compliance either.
- **P76 / [11]: appropriately limited.** “Following the resampling principle” attributes the bootstrap foundation without implying that Efron prescribed this study's particular seed, 5,000 resamples, map grouping, or conditional comparisons.

## Optional wording / citation preferences

These are not required factual corrections:

1. **P10:** “best candidate in the world” could be replaced by “global optimum”; “proven methods” by “established methods.”
2. **P10:** “gait timing” could be specified as “gait period and duty factor.”
3. **P220:** For a scholarly-paper citation, use the named 2016 authors: N. Hansen, T. Tušar, O. Mersmann, A. Auger, and D. Brockhoff, *COCO: The Experimental Procedure*, arXiv:1603.08776 (2016), [DOI](https://doi.org/10.48550/arXiv.1603.08776). The present corporate-author website citation remains identifiable and acceptable as a web reference.

The former sign-description problem is resolved: P74 correctly states that positive relative differences favor CLRP and agrees with P174 and the stated equation.
