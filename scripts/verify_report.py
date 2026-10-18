"""Check page count, required text, embedded images and PDF drawing colours."""
from pathlib import Path
import sys

from pypdf import PdfReader
from pypdf.generic import ContentStream

ROOT = Path(__file__).resolve().parents[1]


def verify(path):
    reader = PdfReader(path)
    if len(reader.pages) != 4:
        raise ValueError(f"Expected four pages including front page; got {len(reader.pages)}")
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
                if obj.get("/ColorSpace") != "/DeviceGray" and not obj.get("/ImageMask", False):
                    raise ValueError(f"Unexpected image colour space: {obj.get('/ColorSpace')}")
            elif obj.get("/Subtype") == "/Form":
                check_contents(obj, obj.get("/Resources", resources))

    for page in reader.pages:
        check_contents(page.get_contents(), page["/Resources"])
    print(f"Verified {len(reader.pages)} pages, required identity text, and monochrome PDF resources.")
    return len(reader.pages)


if __name__ == "__main__":
    verify(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "output/pdf/230145E_a02.pdf")
