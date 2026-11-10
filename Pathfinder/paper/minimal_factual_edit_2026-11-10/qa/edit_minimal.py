from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree
import argparse
import hashlib
import json

BASE = Path('/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder')
SOURCE = Path('/home/dewayne/Downloads/NoReferences(1).docx')
OUTPUT = BASE / 'paper/NoReferences-Minimal-Factual-Corrections-Highlighted.docx'
QA = Path(__file__).resolve().parent
EXPECTED = '1628c0a4df261e42f4e83d27561e09de2e17157f532851ac4d21802696e6f1d2'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W, 'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'

# Each entry is a local factual correction, not a stylistic rewrite.
PATCHES = [
 (4, 'For the landmark search case, the number of acceptances decreases to 93 and the mean search time drops to 0.196 s from 0.376 s.', 'Removing landmark search retains 93 acceptances and reduces mean search time from 0.376 to 0.196 s.', 'Landmark removal does not reduce acceptance.'),
 (4, 'The conditional mean paired-map relative score improvement for complete CLRP is 0.924% compared to the score improvement for this reduced version.', 'Complete CLRP has a conditional mean paired-map relative score improvement of 0.924% over this reduced version.', 'The comparison concerns route scores, not a comparison of two improvements.'),
 (4, 'This is the case because this time frame contains zero and it does not show any significant mean score gain.', 'This statistical interval contains zero and does not demonstrate a mean score advantage.', 'A bootstrap interval is not a time window; superiority is not established.'),
 (4, 'Each diagnostic is comprised of 16 executions', 'A separate diagnostic comprises 16 executions', 'There is one diagnostic with 16 executions.'),
 (4, 'Both Full and Half Scale assistance finish all four missions.', 'Full and half-scale assistance each finish all four missions.', 'The assistance settings are separate conditions.'),
 (4, 'Both ZAs do none and TO at 180s.', 'Both zero-assistance conditions complete none and time out at 180 s.', 'State the measured outcome without undefined abbreviations.'),
 (4, "Assisted executions have no contact under the 6' test.", 'Assisted executions have no detected foot contact under the six-foot criterion.', 'The detector covers six foot geometries, not all contacts or a distance.'),
 (7, "Even a short ride can be cancelled, or there's not enough battery left to reach a charging station.", 'Even a short route can miss its deadline or leave insufficient battery reserve to reach a charging station.', 'The task constraint is arrival time, not cancellation.'),
 (7, 'end-of-trip local path manipulation', 'final local route refinement during planning', 'Refinement occurs during planning, not after execution.'),
 (9, 'A* uses an estimated cost to reach a point and the sum of the costs already incurred to get to the point and the estimate of the remaining cost [2].', 'A* uses the sum of the cost incurred to reach a point and a heuristic estimate of the remaining cost [2].', 'Restore the two-part A* evaluation.'),
 (12, 'All experiments are performed on foot: Walking mode,', 'All experiments use walking mode;', 'Walking-mode selection is not validation of foot-driven locomotion.'),
 (17, 'These body velocities remain the same at scale 0 for the assistance operation.', 'At scale 0, these direct body-velocity corrections are disabled.', 'Zero direct assistance does not freeze physical velocities.'),
 (19, 'a set of points', 'an ordered sequence of points', 'A route has an order.'),
 (22, 'In this case the clip function will only accept the first argument from the range [0, 2].', 'The clip function maps the intermediate value g to the final difficulty d in [0, 2].', 'Clipping bounds the output, not admissible input.'),
 (22, 'The heights are measured in nine locations', 'The heights are sampled in nine locations', 'Heights come from the simulator terrain model.'),
 (22, 'Slope is the mean sampled height (computed on 0.25 m grid) gradient magnitude (arctangent of the gradient magnitude of the mean sampled height).', 'Slope is the arctangent of the gradient magnitude of the footprint-averaged sampled height field on the 0.25 m grid.', 'Restore the implemented slope proxy.'),
 (22, 'The difficulty is measured up to a maximum of every 0.125 m in each segment of a route.', 'Difficulty is sampled at intervals no greater than 0.125 m along each route segment.', 'State the maximum sample spacing.'),
 (22, 'The sum of all segments is the total exposure R.', 'The sum of segment exposures is the total exposure R.', 'Exposure is summed, not segment length alone.'),
 (24, 'For smooth and mild or higher quality grades', 'For terrain grades 0, 1 and 2', 'These are configured semantic grades, not measured physical terrain quality.'),
 (28, 'above 10^−8', 'at most 10⁻⁸', 'Correct the reversed raw-excess tolerance.'),
 (28, 'Positive excesses above the limits are divided by the respective limits and added together if they are large in size.', 'Larger positive excesses are divided by their corresponding limits and summed.', 'Only excesses above the raw tolerance contribute.'),
 (31, 'rank of a candidate is increased', 'rank of a candidate improves', 'Lower lexicographic rank keys are preferred.'),
 (31, 'This means that if both methods have a limit on the number of full routes which can be evaluated, then the numbers of geometric queries will be the same.', 'A common limit on full route evaluations does not imply equal numbers of geometric queries.', 'Equal ceilings do not imply equal recorded work.'),
 (31, 'The common ceiling is increased by route evaluations made during the route initialization.', 'Route evaluations during initialization count toward the fixed common ceiling.', 'Initialization consumes the fixed 240-evaluation allowance.'),
 (36, 'according to their distance from start to destination and vice versa', 'by the sum of their distances to the start and destination', 'Restore the implemented landmark ordering.'),
 (36, 'Keep a maximum of 44 points (start and destination).', 'Keep a maximum of 44 points, including the start and destination.', 'The node cap includes both endpoints.'),
 (38, 'Keep only rank increases.', 'Keep only improvements in rank.', 'Avoid reversing the lower-is-better ranking rule.'),
 (43, 'noL = landmark search, noP = final adjustment.', 'noL omits landmark search; noP omits final adjustment.', 'The names identify removed stages.'),
 (66, 'Both methods are given', 'Each method is given', 'All six configurations share the nominal limits.'),
 (66, 'Route evaluations when the application is initialized', 'Route evaluations during method initialization', 'The initial route search is charged per method.'),
 (66, "A method may stop at either limit, when it's search procedures end.", 'A method may stop below both limits when its search procedures end.', 'Search procedures may finish before exhausting either cap.'),
 (66, 'nominal search directions', 'destination-based lower bounds', 'Match the shared graph.bounds preparation.'),
 (69, '4 open, 4 cluttered, 4 rough and 4 corridor', 'open, cluttered, rough and corridor', 'Remove unsupported family counts; the following two/eight counts are correct.'),
 (71, 'When the number of accepted profiles is equal, the profile with the lowest average score out of the accepted profiles is chosen.', 'When acceptance counts are equal, the profile with the lowest mean score among accepted attempts is chosen.', 'Selection compares accepted attempts and their scores, not accepted profiles.'),
 (71, 'cognitive/social ration of 1.6', 'cognitive and social coefficients of 1.6', 'Both coefficients equal 1.6; this is not a ratio.'),
 (71, '60 points,', '60 points, 12 labels per state,', 'The alternative CLRP profile also changes labels per state from 8 to 12.'),
 (73, 'Only one method of acceptance and both methods of rejection count.', 'Attempts accepted by only one method and attempts rejected by both methods are counted separately.', 'Preserve distinct paired outcome categories.'),
 (73, 'Ties are any difference between Qc and Qv that is less than or equal to 10^−8.', 'Ties are absolute differences between Qc and Qv of at most 10⁻⁸.', 'A large negative signed difference is not a tie.'),
 (75, 'The reported mean and median are the averages of the paired relative score differences on the map.', 'The reported mean and median summarize the within-map averages of paired relative score differences.', 'Restore the map-weighted estimand.'),
 (75, 'The resulting means is the average influence of each map.', "The resulting means show each omitted map's influence on the overall mean.", 'Leave-one-map-out means describe influence, not an average influence statistic.'),
 (77, 'The final comparison consists of 16 missions, all four missions under each of four conditions.', 'The final comparison consists of 16 executions: four missions under each of four conditions.', 'Distinguish missions from repeated executions under conditions.'),
 (77, 'Low tilt refers to the behavior of the assisted controller and is a direct adjustment of roll and pitch angular velocities based on the orientation feedback.', "Low tilt describes the assisted controller's behavior; roll and pitch angular velocities are directly adjusted using orientation feedback.", 'Tilt is a measured orientation quantity, not a velocity adjustment.'),
 (80, 'each get 93 of 96 shots off', 'each accept 93 of 96 attempts', 'These counts are route acceptances.'),
 (80, 'Each failed attempt in a main-test causes a violation of a resource constraint.', 'All 20 rejected main-test attempts exceed the predicted outbound deadline; their battery and terrain-exposure checks pass.', 'State the actual rejection mechanism and scope.'),
 (132, 'All corridor Map resource rejections are made on the corridor Map.', 'All resource rejections occur on corridor maps.', 'Identify where all observed rejections occur.'),
 (132, 'All methods make 24 of 24 attempts', 'All methods accept 24 of 24 attempts', 'Distinguish acceptance from number of scheduled attempts.'),
 (132, 'The corridor acceptance rate is 21 of 24 for CLRP, 22 of 24 for PSO-P, 18 of 24 for CLRP noP and 24 of 24 for ACO-P.', 'Corridor acceptance is 21 of 24 for CLRP, PSO-P, ACO-P and CLRP noL; 22 of 24 for PSO-C; and 18 of 24 for CLRP noP.', 'Correct the method-specific corridor counts.'),
 (132, 'Table 4. Search work is performed more than 96 times; evaluations include completed collision free routes.', 'Table 4 summarizes search work over 96 attempts per method; evaluations count complete collision-free routes.', 'The summary covers 96 attempts for each method.'),
 (169, 'The route-evaluation limit is not necessarily equal for all of the common limits:', 'Common route-evaluation limits do not imply equal search effort:', 'The nominal caps are equal; realized effort differs.'),
 (171, 'Without it, the mean of the other 30 paired maps is 0.690% and -0.060% without it.', 'The full 31-map mean is 0.690%; omitting Map 24 gives −0.060% over the remaining 30 maps.', 'Assign the two means to their correct samples.'),
 (171, 'primary sample that has not been preserved', 'unchanged primary sample', 'The primary sample is preserved; omission is a separate analysis.'),
 (174, 'This influence is the reason for the positive mean, the median being equal to zero and an equal number of lower and higher score pairs against PSO-C.', 'This map drives the positive mean, which coexists with a zero map-level median and equal attempt-level lower- and higher-score counts against PSO-C.', 'Separate map influence on the mean from other descriptive summaries.'),
 (181, 'It takes both full and half-scale assistance to finish all four missions.', 'Full and half-scale assistance each finish all four missions.', 'The two assistance conditions each complete 4/4.'),
 (181, '16 completed, valid executions', '16 valid executions, of which eight complete', 'Only eight of the 16 valid executions complete.'),
 (203, 'The mission time shall be considered completed and include 8 seconds of station service.', 'Completed mission times include 8 seconds of station service.', 'Service is included in successful elapsed times, not a completion definition.'),
 (203, 'Gravity compensation provides a range of traveled distances at timeout of 0.324 to 0.326 m, while without gravity compensation, the range of traveled distances at timeout is 0.376 to 0.381 m.', 'Under zero direct assistance, traveled distances at timeout are 0.324 to 0.326 m with leg-body gravity compensation and 0.376 to 0.381 m without it.', 'Keep direct assistance and gravity-compensation conditions distinct.'),
 (203, 'These results show the following of a path with direct body assistance only, but not propulsion via foot–ground interaction.', 'These results demonstrate route following with direct body assistance and do not validate propulsion via foot–ground interaction.', 'The selected-foot detector does not prove absence of every propulsion mechanism.'),
 (203, 'The model will move about a short distance without any help, and will not complete any of the four missions in 180 s (with gravity turned on or off confirmed).', 'Under zero direct assistance, small horizontal displacements occur, but none of the four missions completes within 180 s, with leg-body gravity compensation either enabled or verified disabled.', 'Environmental gravity is not disabled; displacement does not validate self-propulsion.'),
 (205, 'Removing it results in a loss of 3 acceptances on the corridor maps', 'Removing it loses three acceptances, all repetitions of one corridor map (seed 2140011)', 'The acceptance gain is concentrated in one map.'),
 (205, 'Rank of incumbent route cannot deteriorate in last stage as modifications can be allowed only if incentive is the retention of the route.', 'The retained route cannot worsen in rank within a run because only rank-improving modifications are kept.', 'State the actual within-run incumbent property.'),
 (205, 'There is no evidence that the mean score is higher for CLRP than for PSO-C.', 'The study does not demonstrate a mean paired-map relative score advantage for CLRP over PSO-C.', 'Restore the intended lower-is-better conditional comparison.'),
 (205, 'When the interval is zero', 'When the interval contains zero', 'The bootstrap interval spans zero; it is not identically zero.'),
 (205, 'There is one more PSO-C attempt', 'PSO-C accepts one additional scheduled attempt', 'Trial budgets are equal; outcomes differ.'),
 (207, 'Final local refinement improves the acceptance from 90 to 93 out of 96 attempts on 32 maps for the main test.', 'Final local refinement improves acceptance from 90 to 93 out of 96 attempts on 32 main-test maps; the three additional acceptances are repetitions of one corridor map.', 'Qualify the acceptance finding in the conclusion.'),
 (207, 'landmark search improves acceptance by 0.924%', 'landmark search leaves acceptance unchanged at 93 of 96', 'The 0.924% effect is conditional score improvement, not acceptance improvement.'),
 (207, 'PSO-C has one more chance.', 'PSO-C accepts one additional scheduled attempt.', 'Do not imply unequal trial budgets.'),
 (207, 'There are 16 valid motion executions which each give a separate diagnostic.', 'There are 16 valid motion executions in a separate diagnostic.', 'There is one diagnostic, not 16 independent diagnostics.'),
 (207, 'Assistance is given to full scale and half-scale to complete all four missions.', 'Full-scale and half-scale assistance each complete all four missions.', 'State completion separately for the two assistance conditions.'),
 (207, 'The zero-assistance condition was either none or time out at 180 s, both with and without leg-body gravity compensation verified.', 'Both zero-assistance conditions complete none and time out at 180 s, with leg-body gravity compensation enabled or verified disabled.', 'Restore both zero-assistance outcomes and verified settings.'),
]


def text_of(p):
    return ''.join(p.xpath('.//w:t/text()', namespaces=NS))


def write_text(run, text):
    node = run.find('w:t', NS)
    assert node is not None
    node.text = text
    node.set(XML_SPACE, 'preserve')


def replace_span(p, old, new):
    nodes = p.xpath('.//w:t', namespaces=NS)
    text = ''.join(n.text or '' for n in nodes)
    assert text.count(old) == 1, (old, text.count(old))
    start = text.index(old)
    end = start + len(old)
    selected = []
    pos = 0
    for n in nodes:
        value = n.text or ''
        if pos < end and pos + len(value) > start:
            run = n.getparent()
            assert run.tag == f'{{{W}}}r' and run.getparent() is p
            assert [etree.QName(c).localname for c in run if c.tag != f'{{{W}}}rPr'] == ['t'], etree.tostring(run)
            selected.append((run, value, max(0, start-pos), min(len(value), end-pos)))
        pos += len(value)
    assert selected
    first_run, first_text, lo, _ = selected[0]
    last_run, last_text, _, hi = selected[-1]
    insertion = p.index(first_run)
    pieces = []
    if lo:
        prefix = deepcopy(first_run)
        write_text(prefix, first_text[:lo])
        pieces.append(prefix)
    replacement = etree.Element(f'{{{W}}}r')
    props = first_run.find('w:rPr', NS)
    props = deepcopy(props) if props is not None else etree.Element(f'{{{W}}}rPr')
    for h in props.findall('w:highlight', NS):
        props.remove(h)
    highlight = etree.SubElement(props, f'{{{W}}}highlight')
    highlight.set(f'{{{W}}}val', 'yellow')
    replacement.append(props)
    t = etree.SubElement(replacement, f'{{{W}}}t')
    t.set(XML_SPACE, 'preserve')
    t.text = new
    pieces.append(replacement)
    if hi < len(last_text):
        suffix = deepcopy(last_run)
        write_text(suffix, last_text[hi:])
        pieces.append(suffix)
    for run, *_ in selected:
        p.remove(run)
    for i, run in enumerate(pieces):
        p.insert(insertion+i, run)
    assert text_of(p) == text[:start] + new + text[end:]


def repair_sample_size_padding(root):
    table = root.xpath('//w:tbl', namespaces=NS)[2]
    rows = table.findall('w:tr', NS)
    changes = []
    cells = [(i, 1, row.findall('w:tc', NS)[1], 0) for i, row in enumerate(rows)]
    cells.append((0, 0, rows[0].findall('w:tc', NS)[0], 30))
    for row, column, cell, padding in cells:
        before_text = text_of(cell)
        props = cell.find('w:tcPr', NS)
        if props is None:
            props = etree.Element(f'{{{W}}}tcPr')
            cell.insert(0, props)
        margins = props.find('w:tcMar', NS)
        if margins is None:
            margins = etree.Element(f'{{{W}}}tcMar')
            valign = props.find('w:vAlign', NS)
            props.insert(props.index(valign) if valign is not None else len(props), margins)
        for edge in ['left', 'right']:
            margin = margins.find('w:'+edge, NS)
            if margin is None:
                margin = etree.SubElement(margins, f'{{{W}}}{edge}')
            margin.set(f'{{{W}}}w', str(padding))
            margin.set(f'{{{W}}}type', 'dxa')
        for run in cell.xpath('.//w:r[w:t]', namespaces=NS):
            rpr = run.find('w:rPr', NS)
            if rpr is None:
                rpr = etree.Element(f'{{{W}}}rPr')
                run.insert(0, rpr)
            for h in rpr.findall('w:highlight', NS):
                rpr.remove(h)
            h = etree.SubElement(rpr, f'{{{W}}}highlight')
            h.set(f'{{{W}}}val', 'yellow')
        assert text_of(cell) == before_text
        changes.append(dict(table=3, row=row, column=column, text=before_text,
                            change='Cell padding only; text/numerical value unchanged; yellow highlight added.'))
    return changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--replace-generated', action='store_true')
    args = parser.parse_args()
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED, 'Source changed; re-review before editing.'
    with ZipFile(SOURCE) as zin:
        root = etree.fromstring(zin.read('word/document.xml'))
        paragraphs = root.xpath('/w:document/w:body//w:p', namespaces=NS)
        original_texts = [text_of(p) for p in paragraphs]
        log = []
        for pid, old, new, reason in PATCHES:
            p = paragraphs[pid-1]
            replace_span(p, old, new)
            log.append(dict(paragraph=pid, old=old, new=new, reason=reason))
        updated_texts = [text_of(p) for p in paragraphs]
        expected_texts = list(original_texts)
        for pid, old, new, _ in PATCHES:
            assert expected_texts[pid-1].count(old) == 1
            expected_texts[pid-1] = expected_texts[pid-1].replace(old, new, 1)
        assert updated_texts == expected_texts
        highlights = root.xpath('//w:r[w:rPr/w:highlight[@w:val="yellow"]]', namespaces=NS)
        assert len(highlights) == len(PATCHES)
        assert [text_of(r) for r in highlights] != []
        abstract = updated_texts[3]
        assert len(abstract.split()) <= 250, len(abstract.split())
        format_changes = repair_sample_size_padding(root)
        assert [text_of(p) for p in paragraphs] == expected_texts
        highlights = root.xpath('//w:r[w:rPr/w:highlight[@w:val="yellow"]]', namespaces=NS)
        print(json.dumps(dict(patches=len(PATCHES), changed_paragraphs=len({p[0] for p in PATCHES}), abstract_words=len(abstract.split()), formatting_only_cells=len(format_changes), yellow_highlighted_runs=len(highlights)), indent=2))
        if not args.write:
            return
        xml = etree.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
        assert not OUTPUT.exists() or args.replace_generated, 'Do not overwrite an existing deliverable.'
        with ZipFile(OUTPUT, 'w') as zout:
            for info in zin.infolist():
                value = xml if info.filename == 'word/document.xml' else zin.read(info.filename)
                zout.writestr(info, value)
    (QA/'changes.json').write_text(json.dumps(log, indent=2, ensure_ascii=False)+'\n')
    (QA/'formatting_changes.json').write_text(json.dumps(format_changes, indent=2, ensure_ascii=False)+'\n')
    (QA/'output_paragraphs.txt').write_text('\n'.join(f'P{i:03d} '+t for i,t in enumerate(updated_texts,1) if t.strip())+'\n')
    print(str(OUTPUT))


if __name__ == '__main__':
    main()
