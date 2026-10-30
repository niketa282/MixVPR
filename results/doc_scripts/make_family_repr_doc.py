"""Family x representation comparison document (RGB/grayscale x geometric/photometric).

Run from the repo root with python-docx on PYTHONPATH:
    PYTHONPATH=~/pylib python results/doc_scripts/make_family_repr_doc.py
Prints the numbers used for the written findings; the findings themselves are in FINDINGS below.
"""
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SEEDS = [190223, 1, 2]
GEO_S = ['crop', 'perspective', 'rotate', 'translate', 'shear']
GEO_M = ['geo_k1', 'geo_k2', 'geo_k3']
PHO_S = ['brightness', 'contrast', 'autocontrast', 'blur']
PHO_M = ['phot_k1', 'phot_k2', 'phot_k3']
GEO, PHO = GEO_S + GEO_M, PHO_S + PHO_M
SETS = [('pitts30k_test', 'Pitts30k'), ('pitts250k_test', 'Pitts250k'), ('msls_val', 'MSLS'),
        ('sf_xl_small', 'SF-XL'), ('tokyo247', 'Tokyo 24/7'), ('amstertime', 'AmsterTime'),
        ('st_lucia', 'St Lucia'), ('eynsham', 'Eynsham'), ('nordland', 'Nordland'), ('svox', 'SVOX (all)'),
        ('svox_night', 'SVOX Night'), ('svox_overcast', 'SVOX Overcast'), ('svox_rain', 'SVOX Rain'),
        ('svox_snow', 'SVOX Snow'), ('svox_sun', 'SVOX Sun')]
KEYS = [k for k, _ in SETS]
NAME = dict(SETS)
GROUPS = [('General', KEYS[:8]), ('Seas./weather', [k for k in KEYS[8:] if k != 'svox_night']),
          ('Night', ['svox_night']), ('All 15', KEYS)]
GREY = RGBColor(0x5f, 0x5e, 0x58)


def load(suffix):
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')[KEYS]
    g = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in SEEDS], keys=SEEDS)
    return dict(p=p, R1=p.groupby(level=1).mean(), g=g.groupby(level=1).mean(),
                up=g.groupby(level=1).agg(lambda v: bool((v > 0).all())),
                dn=g.groupby(level=1).agg(lambda v: bool((v < 0).all())))


R, G = load(''), load('_gray')
missing = [c for c in GEO + PHO if c not in G['g'].index]
if missing:
    raise SystemExit(f'grayscale results missing for: {missing}')

GEN, SEA = GROUPS[0][1], GROUPS[1][1]


def a(rep, c, keys=KEYS):
    return rep['g'].loc[c, keys].mean()


def fam(rep, conds, keys=KEYS):
    return rep['g'].loc[conds, keys].mean(axis=1).mean()


def n_up(rep, c):
    return int(rep['up'].loc[c].sum())


def n_dn(rep, c):
    return int(rep['dn'].loc[c].sum())


night = 'svox_night'
FINDINGS = {
    1: [
        ('Single transforms help about equally.',
         f'Geometric singles average {fam(R, GEO_S):+.2f} and photometric singles {fam(R, PHO_S):+.2f} over the 15 '
         f'test sets; the best of each is perspective ({a(R, "perspective"):+.2f}) and contrast ({a(R, "contrast"):+.2f}).'),
        ('Mixed photometric is the strongest RGB family.',
         f'Mixed photometric averages {fam(R, PHO_M):+.2f} against {fam(R, GEO_M):+.2f} for mixed geometric; phot_k3 '
         f'({a(R, "phot_k3"):+.2f}) is the best geometric or photometric condition and improves {n_up(R, "phot_k3")} test sets in all '
         'three seeds.'),
        ('The families help in different places.',
         f'On the general benchmarks the best mixed conditions are level on average (geo_k2 {a(R, "geo_k2", GEN):+.2f}, '
         f'phot_k3 {a(R, "phot_k3", GEN):+.2f}), but geometric leads on SF-XL (geo_k2 '
         f'{R["g"].loc["geo_k2", "sf_xl_small"]:+.1f} vs. phot_k3 {R["g"].loc["phot_k3", "sf_xl_small"]:+.1f}) and MSLS, '
         f'and photometric on Tokyo 24/7 (phot_k1 {R["g"].loc["phot_k1", "tokyo247"]:+.1f} vs. geo_k2 '
         f'{R["g"].loc["geo_k2", "tokyo247"]:+.1f}). Photometric '
         f'augmentation dominates at night (contrast {R["g"].loc["contrast", night]:+.1f}, phot_k3 '
         f'{R["g"].loc["phot_k3", night]:+.1f}, against at most {R["g"].loc[GEO, night].max():+.1f} for any geometric '
         f'condition) and is also ahead on the other seasonal/weather sets (phot_k3 {a(R, "phot_k3", SEA):+.2f} vs. '
         f'geo_k2 {a(R, "geo_k2", SEA):+.2f}).'),
        ('Brightness does not help at night, contrast does.',
         f'Brightness gives {R["g"].loc["brightness", night]:+.1f} on SVOX Night and contrast '
         f'{R["g"].loc["contrast", night]:+.1f}. Contrast reduction in torchvision blends the image towards its grey '
         'mean and so also weakens colours, which fits the colour-cast explanation of the night gap (see the night '
         'analysis).'),
    ],
    2: [
        ('On grayscale, geometric augmentation is the stronger single family.',
         f'Geometric singles average {fam(G, GEO_S):+.2f} against {fam(G, PHO_S):+.2f} for photometric singles; mixed '
         f'conditions are level (geometric {fam(G, GEO_M):+.2f}, photometric {fam(G, PHO_M):+.2f}).'),
        ('Mixed conditions of both families are reliable.',
         f'geo_k1/k2 and phot_k1/k2/k3 each improve {min(n_up(G, c) for c in ["geo_k1", "geo_k2", "phot_k1", "phot_k2", "phot_k3"])}'
         f'–{max(n_up(G, c) for c in ["geo_k1", "geo_k2", "phot_k1", "phot_k2", "phot_k3"])} of 15 test sets in all '
         f'three seeds; the best are phot_k3 ({a(G, "phot_k3"):+.2f}) and geo_k2 ({a(G, "geo_k2"):+.2f}).'),
        ('The night pattern changes once colour is removed.',
         f'On grayscale, contrast helps much less at night ({G["g"].loc["contrast", night]:+.1f}, vs. '
         f'{R["g"].loc["contrast", night]:+.1f} on RGB) while brightness now helps ({G["g"].loc["brightness", night]:+.1f}, '
         f'vs. {R["g"].loc["brightness", night]:+.1f} on RGB), and geometric augmentation also helps '
         f'(geo_k2 {G["g"].loc["geo_k2", night]:+.1f}). This suggests that, once the representation has removed the colour '
         'cast, the remaining night difficulty is closer to a brightness and viewpoint problem.'),
    ],
    3: [
        ('Every geometric augmentation helps grayscale more than RGB.',
         f'The interaction is positive for all eight geometric conditions (from '
         f'{min(a(G, c) - a(R, c) for c in GEO):+.2f} to {max(a(G, c) - a(R, c) for c in GEO):+.2f} points), on '
         f'{min(int((G["g"].loc[c, KEYS] > R["g"].loc[c, KEYS]).sum()) for c in GEO)}–'
         f'{max(int((G["g"].loc[c, KEYS] > R["g"].loc[c, KEYS]).sum()) for c in GEO)} of 15 test sets each.'),
        ('Perspective is the least representation-dependent geometric transform;',
         f'crop and geo_k1 the most (perspective {a(G, "perspective") - a(R, "perspective"):+.2f}, crop '
         f'{a(G, "crop") - a(R, "crop"):+.2f}, geo_k1 {a(G, "geo_k1") - a(R, "geo_k1"):+.2f}).'),
        ('In absolute terms grayscale is ahead on average, driven by night and AmsterTime;',
         'RGB is ahead on most daytime test sets (see the absolute table).'),
    ],
    4: [
        ('Photometric augmentation does not uniformly favour grayscale.',
         f'Unlike geometric augmentation, the interaction is mixed: contrast helps RGB more '
         f'({a(R, "contrast"):+.2f} vs. {a(G, "contrast"):+.2f}), phot_k3 is about equal ({a(R, "phot_k3"):+.2f} vs. '
         f'{a(G, "phot_k3"):+.2f}), while brightness ({a(R, "brightness"):+.2f} vs. {a(G, "brightness"):+.2f}) and phot_k2 '
         f'({a(R, "phot_k2"):+.2f} vs. {a(G, "phot_k2"):+.2f}) help grayscale more.'),
        ('Colour-related benefits shrink on grayscale, intensity-related ones grow.',
         f'At night, contrast falls from {R["g"].loc["contrast", night]:+.1f} (RGB) to {G["g"].loc["contrast", night]:+.1f} '
         f'(grayscale) and brightness rises from {R["g"].loc["brightness", night]:+.1f} to '
         f'{G["g"].loc["brightness", night]:+.1f}: photometric augmentation partly does the job that removing colour '
         'already does.'),
    ],
    5: [
        ('Representation and family interact.',
         f'For RGB, mixed photometric is clearly the strongest family ({fam(R, PHO_M):+.2f} vs. {fam(R, GEO_M):+.2f} for '
         f'mixed geometric); for grayscale, the mixed families are level ({fam(G, PHO_M):+.2f} vs. {fam(G, GEO_M):+.2f}) '
         f'and geometric singles are stronger than photometric singles ({fam(G, GEO_S):+.2f} vs. {fam(G, PHO_S):+.2f}).'),
        ('Colour is the main obstacle at night, and both remedies target it.',
         f'Night R@1: RGB {R["R1"].loc["none", night]:.1f} % → best RGB photometric {R["R1"].loc[PHO, night].max():.1f} %; '
         f'grayscale {G["R1"].loc["none", night]:.1f} % → best grayscale condition {G["R1"].loc[GEO + PHO, night].max():.1f} %. '
         'Removing colour helps far more than any photometric augmentation on RGB, and the two partly overlap.'),
        ('RandAugment remains the strongest single reference, especially for grayscale at night.',
         f'Average gain over 15 test sets: RGB RandAugment {a(R, "randaugment"):+.2f}, grayscale RandAugment '
         f'{a(G, "randaugment"):+.2f}, against at most {max(a(R, c) for c in GEO + PHO):+.2f} (RGB) and '
         f'{max(a(G, c) for c in GEO + PHO):+.2f} (grayscale) for any geometric or photometric condition. Grayscale '
         f'RandAugment reaches {G["R1"].loc["randaugment", night]:.1f} % on SVOX Night, the best night result in the study. '
         f'A geometric or photometric condition matches or beats the better RandAugment model on '
         f'{sum(max(R["R1"].loc[GEO + PHO, k].max(), G["R1"].loc[GEO + PHO, k].max()) >= max(R["R1"].loc["randaugment", k], G["R1"].loc["randaugment", k]) - 0.005 for k in KEYS)} '
         'of 15 test sets.'),
        ('Geometric augmentation is the robust default for daytime and viewpoint change;',
         f'its gains on the general benchmarks are similar for both representations (geo_k2: RGB {a(R, "geo_k2", GEN):+.2f}, '
         f'grayscale {a(G, "geo_k2", GEN):+.2f}).'),
    ],
}

doc = Document()
st = doc.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(10.5)
doc.sections[0].left_margin = doc.sections[0].right_margin = Cm(2.0)
tno, fno = [0], [0]


def border(cell, edge, sz):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn('w:tcBorders'))
    if b is None:
        b = OxmlElement('w:tcBorders'); tcPr.append(b)
    el = OxmlElement(f'w:{edge}')
    el.set(qn('w:val'), 'single'); el.set(qn('w:sz'), str(sz)); el.set(qn('w:color'), '000000')
    b.append(el)


def caption(text, kind='Table'):
    n = tno if kind == 'Table' else fno
    n[0] += 1
    p = doc.add_paragraph()
    r = p.add_run(f'{kind} {n[0]}. '); r.bold = True
    p.add_run(text)
    if kind == 'Table':
        p.paragraph_format.keep_with_next = True


def table(header, rows, widths, font=9, rules=(), bold=()):
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for row in t.rows:
        for j, w in enumerate(widths):
            row.cells[j].width = Cm(w)
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(font)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
        border(c, 'top', 12); border(c, 'bottom', 6)
    for i, cells in enumerate(rows, 1):
        rc = t.rows[i].cells
        for j, cell in enumerate(cells):
            parts = cell if isinstance(cell, list) else [(cell, False)]
            par = rc[j].paragraphs[0]
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.space_after = Pt(0)
            par.paragraph_format.keep_with_next = i < len(rows)
            for text, small in parts:
                r = par.add_run(text); r.font.size = Pt(font - 1.5 if small else font)
                r.bold = (i, j) in bold and not small
                if small:
                    r.font.color.rgb = GREY
        if cells[0] in rules:
            for c in rc: border(c, 'bottom', 4)
        if i == len(rows):
            for c in rc: border(c, 'bottom', 12)
    doc.add_paragraph()


def section(landscape):
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    w, h = s.page_width, s.page_height
    if (landscape and w < h) or (not landscape and w > h):
        s.page_width, s.page_height = h, w
    s.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    s.left_margin = s.right_margin = Cm(1.8 if landscape else 2.0)


def f(v):
    return '0.00' if round(v, 2) == 0 else f'{v:+.2f}'


def bullets(items):
    for head, body in items:
        p = doc.add_paragraph(style='List Bullet')
        r = p.add_run(head + ' '); r.bold = True
        p.add_run(body)


def gavg(rep, c, keys):
    return rep['g'].loc[c, keys].mean()


def n_up(rep, c):
    return int(rep['up'].loc[c].sum())


def n_dn(rep, c):
    return int(rep['dn'].loc[c].sum())


def family_rows(rep):
    """Summary rows for one representation: family means, best single, best mixed, per group."""
    rows = []
    for lab, conds in [('Geometric singles (mean)', GEO_S), ('Photometric singles (mean)', PHO_S),
                       ('Geometric mixed (mean)', GEO_M), ('Photometric mixed (mean)', PHO_M)]:
        rows.append([lab] + [f(rep['g'].loc[conds, ks].mean(axis=1).mean()) for _, ks in GROUPS])
    for lab, conds in [('Best geometric', GEO), ('Best photometric', PHO)]:
        cells = [lab]
        for _, ks in GROUPS:
            a = rep['g'].loc[conds, ks].mean(axis=1)
            cells.append([(f(a.max()), False), (f' {a.idxmax()}', True)])
        rows.append(cells)
    rows.append(['RandAugment (reference)'] + [f(rep['g'].loc['randaugment', ks].mean()) for _, ks in GROUPS])
    return rows


def condition_rows(rep, conds):
    rows = []
    for c in conds:
        rows.append([c] + [f(gavg(rep, c, ks)) for _, ks in GROUPS] + [f'{n_up(rep, c)} / {n_dn(rep, c)}'])
    return rows


def per_set_rows(rep):
    rows, bold = [], set()
    for i, (k, name) in enumerate(SETS, 1):
        bg, bp = rep['g'].loc[GEO, k].idxmax(), rep['g'].loc[PHO, k].idxmax()
        vg, vp = rep['g'].loc[bg, k], rep['g'].loc[bp, k]
        win = 'geometric' if vg > vp + 0.005 else ('photometric' if vp > vg + 0.005 else 'tie')
        rows.append([name, [(f(vg), False), (f' {bg}', True)], [(f(vp), False), (f' {bp}', True)], win,
                     f(rep['g'].loc['randaugment', k])])
        if rep['up'].loc['randaugment', k] or rep['dn'].loc['randaugment', k]:
            bold.add((i, 4))
        if rep['up'].loc[bg, k] or rep['dn'].loc[bg, k]:
            bold.add((i, 1))
        if rep['up'].loc[bp, k] or rep['dn'].loc[bp, k]:
            bold.add((i, 2))
    return rows, bold


def repr_rows(conds):
    rows = []
    for c in conds:
        cells = [c]
        for _, ks in GROUPS[:3]:
            cells += [f(gavg(R, c, ks)), f(gavg(G, c, ks))]
        ia = gavg(G, c, KEYS) - gavg(R, c, KEYS)
        sets = int((G['g'].loc[c, KEYS] > R['g'].loc[c, KEYS]).sum())
        cells += [f(ia), f'{sets}/15']
        rows.append(cells)
    return rows


GROUP_HDR = [g for g, _ in GROUPS]

# ======================================================================= intro
doc.add_heading('Augmentation family × input representation: RGB and grayscale, geometric and photometric', level=1)
doc.add_paragraph('MixVPR (ResNet-50) trained on GSV-Cities for 50 epochs, three seeds per condition (190223, 1, 2), '
                  'tested on 15 test sets. All values are changes in Recall@1 (percentage points) from the '
                  'no-augmentation model of the same representation, computed within each seed and averaged, unless '
                  'stated otherwise.')
for t in [
    'Geometric: crop, perspective, rotate, translate, shear (single) and geo_k1/k2/k3 (k random geometric transforms '
    'per image). Photometric: brightness, contrast, autocontrast, blur (single) and phot_k1/k2/k3.',
    'Test-set groups: General = 8 general benchmarks; Seas./weather = Nordland and the SVOX subsets except Night (6); '
    'Night = SVOX Night, shown separately because its effects are much larger than elsewhere; All 15 = every test set.',
    '"Better / worse" = number of test sets (of 15) where the change had that direction in all three seeds.',
    'RandAugment, the original MixVPR augmentation policy, is shown in every table as a reference (an extra row below '
    'a rule, or an extra column). It mixes geometric and colour operations, so it belongs to neither family.',
]:
    doc.add_paragraph(t, style='List Bullet')

# ======================================================================= 1 & 2: family comparisons
for num, rep, rname in [(1, R, 'RGB'), (2, G, 'Grayscale')]:
    section(False)
    doc.add_heading(f'{num}. {rname}: geometric vs. photometric', level=2)
    caption(f'{rname}: family summaries per test-set group (mean R@1 change). "Best" rows show the strongest single '
            'or mixed condition of each family.')
    table([''] + GROUP_HDR, family_rows(rep), [5.2, 2.6, 2.8, 2.4, 2.6], font=9.5,
          rules=('Photometric mixed (mean)', 'Best photometric'))
    caption(f'{rname}: every condition, mean R@1 change per group, and test sets better / worse in all three seeds.')
    table(['Condition'] + GROUP_HDR + ['Better / worse'], condition_rows(rep, GEO + PHO + ['randaugment']),
          [2.6, 2.1, 2.5, 2.1, 2.1, 2.6], font=9, rules=('shear', 'geo_k3', 'blur', 'phot_k3'))
    rows, bold = per_set_rows(rep)
    caption(f'{rname}: best geometric vs. best photometric condition on each test set (single or mixed), with the '
            'RandAugment reference. Bold: consistent in all three seeds.')
    table(['Test set', 'Best geometric', 'Best photometric', 'Larger gain', 'RandAugment (ref.)'], rows,
          [2.8, 3.8, 3.8, 2.6, 2.6], font=9,
          rules=('Eynsham',), bold=bold)
    doc.add_heading('Findings', level=3)
    bullets(FINDINGS[num] if 'FINDINGS' in globals() else [])

# ======================================================================= 3 & 4: representation comparisons
for num, conds, fname in [(3, GEO, 'geometric'), (4, PHO, 'photometric')]:
    section(True)
    doc.add_heading(f'{num}. RGB vs. grayscale: {fname} augmentation', level=2)
    caption(f'Mean R@1 change from each representation\'s own baseline for the {fname} conditions, RGB vs. grayscale, '
            'per group. Interaction = grayscale gain − RGB gain over all 15 test sets (positive: the augmentation '
            'helps grayscale more); last column: test sets where the grayscale gain is larger.')
    hdr = ['Condition'] + [f'{g} {r}' for g in GROUP_HDR[:3] for r in ('RGB', 'Gray')] + ['Interaction', 'Gray > RGB']
    table(hdr, repr_rows(conds + ['randaugment']), [2.6] + [2.3] * 6 + [2.4, 2.3], font=8.5,
          rules=('shear', 'geo_k3') if fname == 'geometric' else ('blur', 'phot_k3'))
    caption(f'Absolute Recall@1 (%) averaged over all 15 test sets, RGB vs. grayscale, for the no-augmentation model '
            f'and each {fname} condition.')
    rows = [[c, f'{R["R1"].loc[c, KEYS].mean():.2f}', f'{G["R1"].loc[c, KEYS].mean():.2f}',
             f(G['R1'].loc[c, KEYS].mean() - R['R1'].loc[c, KEYS].mean()),
             f'{int((G["R1"].loc[c, KEYS] > R["R1"].loc[c, KEYS]).sum())}/15'] for c in ['none'] + conds + ['randaugment']]
    table(['Condition', 'RGB', 'Grayscale', 'Gray − RGB', 'Sets gray higher'], rows, [3.2, 2.6, 2.6, 2.6, 3.2],
          font=9, rules=('none', conds[-1]))
    doc.add_heading('Findings', level=3)
    bullets(FINDINGS[num] if 'FINDINGS' in globals() else [])

# ======================================================================= 5: 2 x 2
section(False)
doc.add_heading('5. Both families, both representations', level=2)
caption('Family × representation summary over all 15 test sets: mean change of the single transforms, the best single '
        'and best mixed condition, and the number of conditions in the family that improve at least 10 test sets in '
        'all three seeds. Last column: RandAugment reference for that representation (the same for both families).')
rows = []
for rname, rep in [('RGB', R), ('Grayscale', G)]:
    for fam, s_, m_ in [('geometric', GEO_S, GEO_M), ('photometric', PHO_S, PHO_M)]:
        bs = rep['g'].loc[s_, KEYS].mean(axis=1); bm = rep['g'].loc[m_, KEYS].mean(axis=1)
        rows.append([f'{rname}, {fam}', f(bs.mean()), [(f(bs.max()), False), (f' {bs.idxmax()}', True)],
                     [(f(bm.max()), False), (f' {bm.idxmax()}', True)],
                     f'{sum(n_up(rep, c) >= 10 for c in s_ + m_)} of {len(s_ + m_)}',
                     f(rep['g'].loc['randaugment', KEYS].mean())])
table(['', 'Singles mean', 'Best single', 'Best mixed', 'Broadly reliable', 'RandAugment (ref.)'], rows,
      [3.4, 2.2, 3.2, 3.2, 2.4, 2.6],
      font=9.5, rules=('RGB, photometric',))
caption('Best condition per test set across all 30 combinations (2 representations × 15 geometric and photometric '
        'conditions), absolute Recall@1 (%), with the no-augmentation RGB model and RandAugment (RGB and grayscale) '
        'for reference.')
rows = []
for k, name in SETS:
    cand = [(R['R1'].loc[c, k], 'RGB', c) for c in GEO + PHO] + [(G['R1'].loc[c, k], 'Gray', c) for c in GEO + PHO]
    v, r_, c_ = max(cand)
    rows.append([name, f'{R["R1"].loc["none", k]:.2f}', [(f'{v:.2f}', False), (f' {r_} {c_}', True)],
                 f(v - R['R1'].loc['none', k]), f'{R["R1"].loc["randaugment", k]:.2f}',
                 f'{G["R1"].loc["randaugment", k]:.2f}'])
table(['Test set', 'RGB none', 'Best geometric/photometric', 'Gain vs. RGB none', 'RGB RandAug.', 'Gray RandAug.'],
      rows, [2.6, 1.8, 5.0, 2.2, 2.1, 2.1], font=8.5,
      rules=('Eynsham',))
doc.add_heading('Findings', level=3)
bullets(FINDINGS[5] if 'FINDINGS' in globals() else [])

doc.save('results/family_by_representation.docx')
print('saved results/family_by_representation.docx, tables', tno[0])
