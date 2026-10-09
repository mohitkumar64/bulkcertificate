"""Certificate generator — SVG template → PDF bytes.

The rest of the application should not know about SVG/XML internals.
"""

from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF


# ---------- internal helpers ----------

def _replace_svg_fields(svg_path: str | Path, fields: dict[str, str]) -> bytes:
    """Load an SVG template, replace fields by element IDs, return SVG bytes."""
    tree = ET.parse(str(svg_path))
    root = tree.getroot()

    SVG_NS = "http://www.w3.org/2000/svg"

    for field_id, value in fields.items():
        element = root.find(f".//*[@id='{field_id}']")

        if element is None:
            raise ValueError(f"SVG field with id '{field_id}' was not found")

        tspans = element.findall(f".//{{{SVG_NS}}}tspan")

        if tspans:
            tspans[0].text = str(value)
            for tspan in tspans[1:]:
                tspan.text = ""
            element.text = None
        else:
            element.text = str(value)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _svg_bytes_to_pdf(svg_bytes: bytes) -> bytes:
    """Convert SVG bytes to PDF bytes via svglib + ReportLab."""
    drawing = svg2rlg(BytesIO(svg_bytes))

    if drawing is None:
        raise ValueError("Failed to parse SVG")

    output = BytesIO()
    renderPDF.drawToFile(drawing, output)
    return output.getvalue()


# ---------- public API ----------

def generate_certificate(template_path: str | Path, fields: dict[str, str]) -> bytes:
    """Generate a single certificate PDF from the SVG template.

    Args:
        template_path: Path to the immutable SVG template.
        fields: Mapping of SVG element IDs to replacement values.

    Returns:
        PDF file contents as bytes.
    """
    svg_bytes = _replace_svg_fields(template_path, fields)
    return _svg_bytes_to_pdf(svg_bytes)
