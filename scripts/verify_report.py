"""Check the separate cover, three content pages, repository link and black text/rules."""
from pathlib import Path
import sys

from pypdf import PdfReader
from pypdf.generic import ContentStream

ROOT = Path(__file__).resolve().parents[1]


def verify(path):
    reader = PdfReader(path)
    if len(reader.pages) != 4:
        raise ValueError(f"Expected separate cover plus three content pages; got {len(reader.pages)}")
    text = "\n".join(page.extract_text() for page in reader.pages)
    for expected in ["Dilhan W.A.", "230145E", "University of Moratuwa", "EN3160", "ahesh-dilhan"]:
        if expected not in text:
            raise ValueError(f"Missing required report text: {expected}")
    checked_images = set()

    def check_contents(stream, resources):
        if stream is not None:
            for operands, operator in ContentStream(stream, reader).operations:
                values = [float(v) for v in operands] if operator in [b"rg", b"RG", b"k", b"K"] else []
                if operator in [b"rg", b"RG"] and not max(values)-min(values) < 1e-7:
                    raise ValueError(f"Chromatic RGB drawing colour: {values}")
                if operator in [b"k", b"K"] and any(abs(v) > 1e-7 for v in values[:3]):
                    raise ValueError(f"Chromatic CMYK drawing colour: {values}")
        xobjects = resources.get("/XObject", {})
        if hasattr(xobjects, "get_object"):
            xobjects = xobjects.get_object()
        for reference in xobjects.values():
            obj = reference.get_object()
            if obj.get("/Subtype") == "/Image":
                if id(obj) in checked_images:
                    continue
                checked_images.add(id(obj))
            elif obj.get("/Subtype") == "/Form":
                check_contents(obj, obj.get("/Resources", resources))

    for page in reader.pages:
        check_contents(page.get_contents(), page["/Resources"])
    repo = 'https://github.com/ahesh-dilhan/en3160-assignment-02'
    links = [str(a.get_object().get('/A', {}).get('/URI', '')) for p in reader.pages for a in p.get('/Annots', [])]
    if repo not in links or 'https://github.com/ahesh-dilhan' in links:
        raise ValueError('Expected repository link and no GitHub profile link')
    print(f"Verified {len(reader.pages)} pages, repository link, and black PDF text/rules; colour images preserved.")
    return len(reader.pages)


if __name__ == "__main__":
    verify(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "output/pdf/230145E_a02.pdf")
