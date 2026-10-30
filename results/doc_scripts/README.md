Scripts that build the Word result documents in results/.

They need python-docx, which is not in the mixvpr env. Install it into a separate folder and run from the repo root:

    python -m pip install --target ~/pylib python-docx
    PYTHONPATH=~/pylib python results/doc_scripts/make_geo_vs_phot_v2.py

Main scripts:
- make_geo_vs_phot_v2.py  -> results/geometric_vs_photometric_rgb.docx
- make_gray_all_docx.py   -> results/grayscale_results_all_datasets(_with_randaugment).docx
- make_all_docx_v2.py     -> results/geometric_results_all_datasets(_with_randaugment).docx (RGB)
- make_phot_docx.py       -> results/photometric_results_rgb.docx
- make_full_tables.py     -> results/rgb_gray_full_results.docx
- make_gray_doc.py        -> results/grayscale_results.docx
- make_workbook*.py       -> results/geo_workbook(_gray).docx
