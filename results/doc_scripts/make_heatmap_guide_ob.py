"""Word guide explaining every element of the red/green RGB gain heatmap. Run from MixVPR."""
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SEEDS = [190223, 1, 2]
d = pd.concat([pd.read_csv(f'results/seed{s}/test_results.csv') for s in SEEDS])
r1 = d.pivot_table(index=['condition', 'seed'], columns='dataset', values='R1')

doc = Document()
st = doc.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(11)
s = doc.sections[0]
s.orientation = WD_ORIENT.LANDSCAPE
s.page_width, s.page_height = s.page_height, s.page_width
s.left_margin = s.right_margin = Cm(1.8); s.top_margin = s.bottom_margin = Cm(1.5)


def border(cell, edge, sz):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn('w:tcBorders'))
    if b is None:
        b = OxmlElement('w:tcBorders'); tcPr.append(b)
    el = OxmlElement(f'w:{edge}')
    el.set(qn('w:val'), 'single'); el.set(qn('w:sz'), str(sz)); el.set(qn('w:color'), '000000')
    b.append(el)


def table(header, rows, widths, font=10):
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for row in t.rows:
        for j, w in enumerate(widths):
            row.cells[j].width = Cm(w)
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(font)
        border(c, 'top', 12); border(c, 'bottom', 6)
    for i, cells in enumerate(rows, 1):
        for j, text in enumerate(cells):
            c = t.rows[i].cells[j]
            r = c.paragraphs[0].add_run(text); r.font.size = Pt(font)
            c.paragraphs[0].paragraph_format.space_after = Pt(2)
            if i == len(rows):
                border(c, 'bottom', 12)
    doc.add_paragraph()


def bullet(head, body=''):
    p = doc.add_paragraph(style='List Bullet')
    if head:
        r = p.add_run(head + (' ' if body else '')); r.bold = True
    p.add_run(body)


# ---------------------------------------------------------------- page 1: figure
doc.add_heading('Reading the augmentation heatmap (RGB, three seeds)', level=1)
doc.add_picture('results/figures/gain_heatmap_rgb_orangeblue.png', width=Cm(25.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
cap = doc.add_paragraph()
r = cap.add_run('Figure 1. '); r.bold = True
cap.add_run('Change in Recall@1 (percentage points) relative to training without augmentation, for each geometric '
            'augmentation (rows) and test set (columns). MixVPR with RGB input; mean over three seeds (190223, 1, 2). '
            'Orange: better than no augmentation; blue: worse; grey: no change. Outlined cells with bold numbers: '
            'the change has the same direction in all three seeds.')

# ---------------------------------------------------------------- page 2: parts of the figure
doc.add_section()
s2 = doc.sections[-1]
s2.orientation = WD_ORIENT.PORTRAIT
s2.page_width, s2.page_height = s2.page_height, s2.page_width
s2.left_margin = s2.right_margin = Cm(2.2)

doc.add_heading('1. What the figure is', level=2)
doc.add_paragraph('A heatmap is a table drawn as coloured cells. Each cell answers one question: "on this test set, '
                  'did training with this augmentation give a higher or lower Recall@1 than training with no '
                  'augmentation, and by how much?" The figure has three dimensions: the rows (y-axis), the columns '
                  '(x-axis) and the colour of each cell (the third dimension, often called z).')

doc.add_heading('2. Every part of the figure', level=2)
table(['Part', 'What it shows', 'How to read it'], [
    ['y-axis (rows)', 'The 8 augmentation conditions. Top five: single transforms (crop, perspective, rotate, '
     'translate, shear). Bottom three: mixed conditions geo_k1, geo_k2, geo_k3 (1, 2 or 3 randomly chosen '
     'transforms per image).', 'Read along a row to see how one augmentation behaves across all test sets.'],
    ['x-axis (columns)', 'The 15 test sets. Left group: general benchmarks (cities, street level). Right group: test '
     'sets with seasonal or weather/lighting change (Nordland and the SVOX subsets).', 'Read down a column to compare '
     'all augmentations on one test set.'],
    ['Colour (z)', 'The size and direction of the change in Recall@1 compared with "none" (no augmentation), in '
     'percentage points.', 'Orange = better, blue = worse, light grey = about the same. Darker = bigger change.'],
    ['Number in each cell', 'The exact value of that change, e.g. +4.7 means Recall@1 was 4.7 points higher than '
     'without augmentation; −3.1 means 3.1 points lower; 0.0 means no change.', 'Use the number for exact values; the '
     'colour is just a quick visual guide.'],
    ['Black box outline + bold number', 'The change had the same direction in all three training runs (seeds): '
     'better in all three, or worse in all three.', 'Outlined = a reliable effect. No outline = the runs disagreed, so '
     'the average may be luck.'],
    ['Colour bar (right)', 'The key from colour to value, from −5 (dark blue, worse) to +5 (dark orange, better), '
     'with 0 in grey.', 'Values beyond ±5 would get the darkest colour; none of the cells here reach that.'],
    ['White lines', 'Horizontal: separates single transforms (above) from mixed conditions (below). Vertical: '
     'separates general benchmarks (left) from seasonal/weather test sets (right).', 'Only for grouping; they carry no '
     'data.'],
    ['Group titles (top)', '"General benchmarks" and "Seasonal and weather/lighting change" name the two column '
     'groups.', '—'],
], [3.2, 7.6, 5.8], font=9.5)

doc.add_heading('3. What "none" is and why it is not a row', level=2)
doc.add_paragraph('"none" is the model trained without any augmentation. Every cell is measured against it, so it '
                  'would be a row of zeros and is left out. A cell is therefore not a Recall@1 score itself but the '
                  'difference between two scores.')

# ---------------------------------------------------------------- worked example
doc.add_heading('4. Worked example: how one cell is calculated', level=2)
k = 'nordland'
rows, diffs = [], []
for s in SEEDS:
    a, b = r1.loc[('perspective', s), k], r1.loc[('none', s), k]
    diffs.append(a - b)
    rows.append([f'Seed {s}', f'{b:.2f}', f'{a:.2f}', f'{a - b:+.2f}', 'better' if a > b else 'worse'])
rows.append(['Mean', '', '', f'{sum(diffs) / 3:+.2f}', f'{sum(x > 0 for x in diffs)} of 3 better'])
doc.add_paragraph('The cell for perspective on Nordland shows +4.7 with a box outline. It is calculated from the '
                  'three training runs of each condition:')
table(['Run', 'none R@1', 'perspective R@1', 'Change', 'Direction'], rows, [3.0, 3.0, 3.4, 3.0, 3.4])
doc.add_paragraph(f'The cell value is the mean change, {sum(diffs) / 3:+.2f}, shown rounded as +4.7. Because the change '
                  'is positive in all three runs, the cell is outlined and the number is bold.')
k2 = 'nordland'
rows, diffs = [], []
for s in SEEDS:
    a, b = r1.loc[('geo_k2', s), k2], r1.loc[('none', s), k2]
    diffs.append(a - b)
    rows.append([f'Seed {s}', f'{b:.2f}', f'{a:.2f}', f'{a - b:+.2f}', 'better' if a > b else 'worse'])
doc.add_paragraph('Compare geo_k2 on Nordland, which shows +2.7 without an outline:')
table(['Run', 'none R@1', 'geo_k2 R@1', 'Change', 'Direction'], rows, [3.0, 3.0, 3.4, 3.0, 3.4])
doc.add_paragraph('The average is clearly positive, but one run was worse than no augmentation, so the effect is '
                  'not reliable enough to be outlined.')

doc.add_heading('5. Colour and outline together', level=2)
for h, b in [
    ('Dark orange, outlined:', 'large and reliable improvement (e.g. perspective on Nordland, geo_k2 on SVOX Sun).'),
    ('Pale orange, outlined:', 'small but reliable improvement (e.g. most cells for Pitts30k and Pitts250k).'),
    ('Dark colour, not outlined:', 'large average change that did not appear in every run, so treat with caution '
     '(e.g. geo_k1 on Nordland, +3.0).'),
    ('Blue, outlined:', 'reliably worse than no augmentation (e.g. crop and translate on Tokyo 24/7, geo_k1 on '
     'SVOX Night).'),
    ('Grey:', 'no meaningful change, usually because the test set is already near 100 % (St Lucia, SVOX (all)).'),
]:
    bullet(h, b)

doc.add_heading('6. What the figure does not show', level=2)
for t in [
    'The actual Recall@1 scores (e.g. that Nordland is around 72–77 % and St Lucia around 99.7 %); only the change.',
    'How much the runs varied, as a number; the outline only says whether they agreed in direction.',
    'Grayscale results; this figure is RGB only. A matching grayscale figure will follow.',
]:
    bullet('', t)

doc.add_heading('7. Main patterns in this figure', level=2)
for h, b in [
    ('Mixed rows are the most reliably orange.', 'geo_k2 and geo_k3 have 10 outlined orange cells each and no outlined blue.'),
    ('Perspective is the best single transform.', '8 outlined orange cells, none blue, and the strongest single-'
     'transform cell (Nordland +4.7). Crop is the weakest.'),
    ('Urban benchmarks (first four columns) improve almost everywhere.', 'SF-XL shows the largest gains, up to +4.2 '
     'for geo_k2.'),
    ('Tokyo 24/7 is the exception.', 'Crop (−3.1) and translate (−2.0) are reliably worse there.'),
    ('SVOX Sun and Nordland respond most among the weather/seasonal sets;', 'SVOX Night is not helped by geometric '
     'augmentation.'),
    ('Near-ceiling test sets barely change:', 'St Lucia, SVOX (all) and SVOX Overcast.'),
]:
    bullet(h, b)

doc.add_heading('A note on the colours', level=2)
doc.add_paragraph('Orange (better) and blue (worse) were chosen because this pair stays distinguishable for readers '
                  'with the common forms of colour blindness and in black-and-white print, unlike red/green. The '
                  'numbers and outlines carry the same information, so the figure does not rely on colour alone.')

doc.save('results/gain_heatmap_rgb_guide_orangeblue.docx')
print('saved results/gain_heatmap_rgb_guide_orangeblue.docx')
