# LaTeX report

Main source: `230145E_a02.tex`. Measured tables are in `data.tex`; prepared
monochrome figures are in `figures/`. These assets allow compilation without
access to the raw assignment images.

The design uses a university title block, Computer Modern serif typography,
black text and rules, unshaded tables, and numbered captions. The title block
shares page one with Q1 to preserve the four-page maximum, including the front
page. Photographs are grayscale; plots use black markers and line patterns.
Hyperlinks print black.

The crest was supplied in `C:/Users/User/Downloads/uom_logo.png`, copied to
`assets/report/uom_logo_original.png`, composited on white, and converted to
black and white. It is university identity artwork, not original project artwork.
The sample PDF was used as a visual reference only; its course content was not copied.

From the project root:

```powershell
.\.runtime\python\python.exe scripts/build_report.py
```

The script refreshes figures/tables from `outputs/`, compiles with the local
Tectonic compiler (or one on PATH), and validates page count, identity text,
and PDF colours. The first Tectonic run downloads TeX resources. This workspace
uses Tectonic 0.17.0. Output: `output/pdf/230145E_a02.pdf`.

To compile with the prepared figures, from this folder:

```powershell
tectonic --keep-logs --outdir ../output/pdf 230145E_a02.tex
```

Standard LaTeX packages also permit compilation with TeX Live/MiKTeX or Overleaf.
Q3 retains the recorded limitation that its saved corners were selected from
visual inspection; changing the presentation does not change experimental results.
