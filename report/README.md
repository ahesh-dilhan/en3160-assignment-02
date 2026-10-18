# LaTeX report

Main source: `230145E_a02.tex`. Measured tables are in `data.tex`; prepared
colour figures are in `figures/`. These assets allow compilation without
access to the raw assignment images.

The design uses a separate cover matching the reference's measured A4 positions,
font sizes, logo placement, and centred text hierarchy. Course/title/date are
adapted to this assignment. Computer Modern serif text, layout rules, tables,
captions and hyperlinks are black. Images, the crest and plotted data retain
colour. The GitHub link points to the assignment repository, not the profile.

This version has five pages: the explicitly requested separate cover plus four
content pages. The assignment brief's four-page total limit therefore needs to
be considered before submission; this layout follows the user's cover request.

The crest was supplied in `C:/Users/User/Downloads/uom_logo.png`, copied to
`assets/report/uom_logo_original.png` and composited on white with its original
colours. It is university identity artwork, not original project artwork.
The sample PDF was used as a visual reference only; its course content was not copied.

From the project root:

```powershell
.\.runtime\python\python.exe scripts/build_report.py
```

The script refreshes figures/tables from `outputs/`, compiles with the local
Tectonic compiler (or one on PATH), and validates page count, identity text,
repository URL and black PDF text/rules while allowing colour images. The first Tectonic run downloads TeX resources. This workspace
uses Tectonic 0.17.0. Output: `output/pdf/230145E_a02.pdf`.

To compile with the prepared figures, from this folder:

```powershell
tectonic --keep-logs --outdir ../output/pdf 230145E_a02.tex
```

Standard LaTeX packages also permit compilation with TeX Live/MiKTeX or Overleaf.
Q3 retains the recorded limitation that its saved corners were selected from
visual inspection; changing the presentation does not change experimental results.
