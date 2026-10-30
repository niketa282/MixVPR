"""All Recall@1 results in the format of the thesis tables (R@1 mean ± std over three seeds, one column per test set).

For each input (RGB, grayscale) and each block of conditions (geometric, photometric, augmentation policies,
strength sweep) two tables are produced: general benchmarks and condition-change benchmarks. Bold = best mean in
the column within that table.

Outputs results/thesis_tables.docx and results/thesis_tables.tex (booktabs + adjustbox). Run from the repo root with
python-docx on PYTHONPATH:
    python results/doc_scripts/make_thesis_tables.py
"""
import pandas as pd
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SEEDS = [190223, 1, 2]
GEN = [('pitts30k_test', 'Pitts30k'), ('pitts250k_test', 'Pitts250k'), ('msls_val', 'MSLS'), ('sf_xl_small', 'SF-XL'),
       ('tokyo247', 'Tokyo 24/7'), ('amstertime', 'AmsterTime'), ('st_lucia', 'St Lucia'), ('eynsham', 'Eynsham')]
CHG = [('nordland', 'Nordland'), ('svox', 'SVOX'), ('svox_night', 'Night'), ('svox_overcast', 'Overcast'),
       ('svox_rain', 'Rain'), ('svox_snow', 'Snow'), ('svox_sun', 'Sun')]
GROUPS = [('general benchmarks', GEN), ('condition-change benchmarks', CHG)]

# blocks: (title, {input: [row groups]}) ; a row group is a list of (label, condition); rules separate groups
BLOCKS = [
    ('Geometric augmentation', {
        'rgb': [[('none', 'none')], [(c, c) for c in ('crop', 'perspective', 'rotate', 'translate', 'shear')],
                [(c, c) for c in ('geo_k1', 'geo_k2', 'geo_k3')]],
        'gray': [[('none', 'none')], [(c, c) for c in ('crop', 'perspective', 'rotate', 'translate', 'shear')],
                 [(c, c) for c in ('geo_k1', 'geo_k2', 'geo_k3')]]}),
    ('Photometric augmentation', {
        'rgb': [[('none', 'none')], [(c, c) for c in ('brightness', 'contrast', 'autocontrast', 'blur')],
                [(c, c) for c in ('phot_k1', 'phot_k2', 'phot_k3')]],
        'gray': [[('none', 'none')], [(c, c) for c in ('brightness', 'contrast', 'autocontrast', 'blur')],
                 [(c, c) for c in ('phot_k1', 'phot_k2', 'phot_k3')]]}),
    ('Augmentation policies', {
        'rgb': [[('none', 'none')], [('RandAugment', 'randaugment'), ('TrivialAugment', 'trivialaugment')]],
        'gray': [[('none', 'none')], [('RandAugment', 'randaugment')]]}),
    ('Strength sweep', {
        'rgb': [[('none', 'none')],
                [('perspective 0.1', 'perspective_0.1'), ('perspective 0.2*', 'perspective'),
                 ('perspective 0.3', 'perspective_0.3'), ('perspective 0.4', 'perspective_0.4')],
                [('contrast ±0.2', 'contrast_0.8-1.2'), ('contrast ±0.4*', 'contrast'),
                 ('contrast ±0.6', 'contrast_0.4-1.6'), ('contrast ±0.8', 'contrast_0.2-1.8')]],
        'gray': [[('none', 'none')],
                 [('shear ±2.5°', 'shear_2.5'), ('shear ±5°*', 'shear'), ('shear ±7.5°', 'shear_7.5'),
                  ('shear ±10°', 'shear_10')],
                 [('brightness ±0.2', 'brightness_0.8-1.2'), ('brightness ±0.4*', 'brightness'),
                  ('brightness ±0.6', 'brightness_0.4-1.6'), ('brightness ±0.8', 'brightness_0.2-1.8')]]}),
]
INPUTS = [('rgb', 'RGB', ''), ('gray', 'grayscale', '_gray')]


def stats(suffix):
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    g = d.groupby(['condition', 'dataset']).R1
    return g.mean(), g.std(), d.groupby('condition').seed.nunique()


def gains(suffix):
    """Per-seed change from the same seed's no-augmentation model: mean, std and number of seeds > 0."""
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')
    g = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in SEEDS], keys=SEEDS)
    gg = g.groupby(level=1)
    return gg.mean(), gg.std(), gg.agg(lambda v: int((v > 0).sum())), \
        gg.agg(lambda v: bool((v > 0).all() or (v < 0).all()))


def build_tables(with_gains=False):
    """Yield dicts describing every table (shared by the Word and LaTeX writers)."""
    for key, name, suffix in INPUTS:
        mean, sd, nseeds = stats(suffix)
        gm, gs, gpos, gsame = gains(suffix)
        for title, by_input in BLOCKS:
            groups = by_input[key]
            for gname, cols in GROUPS:
                rows = []
                for gi, grp in enumerate(groups):
                    for label, cond in grp:
                        assert nseeds[cond] == len(SEEDS), (cond, nseeds[cond])
                        rows.append((label, cond, gi))
                best = {k: max(round(mean[c, k], 2) for _, c, _ in rows) for k, _ in cols}
                cap = (f'Recall@1 (%) for {name} on the {gname}, {title.lower()}, mean ± standard deviation over '
                       f'three seeds.')
                if title == 'Strength sweep':
                    cap += ' * = default strength used in the main experiments.'
                yield dict(kind='abs', input=name, block=title, group=gname, caption=cap, cols=cols, rows=rows,
                           best=best, mean=mean, sd=sd)
                if with_gains:
                    grows = [(label, cond, gi) for label, cond, gi in rows if cond != 'none']
                    gcap = (f'Change in Recall@1 relative to no augmentation (percentage points) for {name} on the '
                            f'{gname}, {title.lower()}: mean ± standard deviation of the per-seed difference, and '
                            f'number of seeds with a positive change. Bold: same sign in all three seeds and larger '
                            f'than the standard deviation.')
                    yield dict(kind='gain', input=name, block=title, group=gname, caption=gcap, cols=cols,
                               rows=grows, mean=gm.stack(), sd=gs.stack(), pos=gpos, same=gsame)


# ------------------------------------------------------------------ Word
def border(cell, edge, sz):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn('w:tcBorders'))
    if b is None:
        b = OxmlElement('w:tcBorders'); tcPr.append(b)
    el = OxmlElement(f'w:{edge}')
    el.set(qn('w:val'), 'single'); el.set(qn('w:sz'), str(sz)); el.set(qn('w:color'), '000000')
    b.append(el)


def write_docx(tables, out):
    doc = Document()
    st = doc.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(10)
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = sec.page_height, sec.page_width
    sec.left_margin = sec.right_margin = Cm(1.5)
    doc.add_heading('Recall@1 tables: all conditions, RGB and grayscale', level=1)
    doc.add_paragraph('Same format as the thesis tables: Recall@1 (%) per test set, mean ± standard deviation over '
                      'three seeds (190223, 1, 2). Bold: best mean in the column within each table. Each table '
                      'repeats the no-augmentation row of the same input as the baseline. Each R@1 table is followed '
                      'by the change from that baseline, computed per seed (as in the geometric results document).')
    n = 0
    cur = None
    for t in tables:
        if (t['input'], t['block']) != cur:
            cur = (t['input'], t['block'])
            doc.add_heading(f'{t["input"].capitalize()}: {t["block"].lower()}', level=2)
        n += 1
        p = doc.add_paragraph(); r = p.add_run(f'Table {n}. '); r.bold = True; p.add_run(t['caption'])
        p.paragraph_format.keep_with_next = True
        cols = t['cols']
        tb = doc.add_table(rows=1 + len(t['rows']), cols=1 + len(cols))
        tb.alignment = WD_TABLE_ALIGNMENT.CENTER
        tb.autofit = False
        widths = [3.2] + [2.65] * len(cols)
        for row in tb.rows:
            for j, w in enumerate(widths):
                row.cells[j].width = Cm(w)
        for j, h in enumerate(['Condition'] + [c[1] for c in cols]):
            c = tb.rows[0].cells[j]
            rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9)
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            border(c, 'top', 12); border(c, 'bottom', 6)
        prev_g = 0
        for i, (label, cond, gi) in enumerate(t['rows'], 1):
            rc = tb.rows[i].cells
            if gi != prev_g:
                for c in tb.rows[i - 1].cells: border(c, 'bottom', 4)
                prev_g = gi
            par = rc[0].paragraphs[0]; par.add_run(label).font.size = Pt(9)
            for j, (k, _) in enumerate(cols, 1):
                m, s = t['mean'][cond, k], t['sd'][cond, k]
                par = rc[j].paragraphs[0]; par.alignment = WD_ALIGN_PARAGRAPH.CENTER
                grey = RGBColor(0x5F, 0x5E, 0x58)
                if t['kind'] == 'gain':
                    v = '0.00' if round(m, 2) == 0 else f'{m:+.2f}'
                    r1 = par.add_run(v); r1.font.size = Pt(8.5)
                    r1.bold = bool(t['same'].loc[cond, k]) and abs(m) > s
                    for txt in (f' ±{s:.2f}', f' ({t["pos"].loc[cond, k]}/{len(SEEDS)})'):
                        r2 = par.add_run(txt); r2.font.size = Pt(6.5); r2.font.color.rgb = grey
                    continue
                r1 = par.add_run(f'{m:.2f}'); r1.font.size = Pt(9); r1.bold = round(m, 2) == t['best'][k]
                r2 = par.add_run(f' ±{s:.2f}'); r2.font.size = Pt(6.5); r2.font.color.rgb = grey
            for c in rc:
                c.paragraphs[0].paragraph_format.space_after = Pt(0)
                c.paragraphs[0].paragraph_format.keep_with_next = i < len(t['rows'])
        for c in tb.rows[-1].cells: border(c, 'bottom', 12)
        doc.add_paragraph()
    doc.save(out)


# ------------------------------------------------------------------ LaTeX
def tex_escape(s):
    return s.replace('%', r'\%').replace('±', r'$\pm$').replace('°', r'$^\circ$').replace('_', r'\_').replace('*', r'$^*$')


def write_tex(tables, out):
    L = ['% Recall@1 tables in the thesis format. Requires \\usepackage{booktabs} and \\usepackage{adjustbox}.',
         '% Generated by results/doc_scripts/make_thesis_tables.py', '']
    for t in tables:
        cols = t['cols']
        key = (t['input'][:3] + '_' + t['block'].split()[0] + '_' + t['group'].split()[0]).lower().replace('-', '')
        L += [r'\begin{table}[htbp]', r'\centering', r'\small', r'\setlength{\tabcolsep}{3.5pt}',
              f'\\caption{{{tex_escape(t["caption"])}}}', f'\\label{{tab:{key}}}',
              r'\begin{adjustbox}{max width=\linewidth}',
              r'\begin{tabular}{l' + 'r' * len(cols) + '}', r'\toprule',
              'Condition & ' + ' & '.join(c[1] for c in cols) + r' \\', r'\midrule']
        prev_g = 0
        for label, cond, gi in t['rows']:
            if gi != prev_g:
                L.append(r'\midrule'); prev_g = gi
            cells = []
            for k, _ in cols:
                m, s = t['mean'][cond, k], t['sd'][cond, k]
                v = f'{m:.2f}'
                v = f'\\textbf{{{v}}}' if round(m, 2) == t['best'][k] else v
                cells.append(f'{v}\\,{{\\scriptsize$\\pm${s:.2f}}}')
            L.append(f'{tex_escape(label)} & ' + ' & '.join(cells) + r' \\')
        L += [r'\bottomrule', r'\end{tabular}', r'\end{adjustbox}', r'\end{table}', '']
    open(out, 'w').write('\n'.join(L))


if __name__ == '__main__':
    tables = list(build_tables(with_gains=True))
    write_docx(tables, 'results/thesis_tables.docx')
    write_tex([t for t in tables if t['kind'] == 'abs'], 'results/thesis_tables.tex')
    print(f'{len(tables)} tables -> results/thesis_tables.docx, results/thesis_tables.tex')
