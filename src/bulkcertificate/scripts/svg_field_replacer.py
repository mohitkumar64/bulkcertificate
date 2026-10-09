from pathlib import Path
import xml.etree.ElementTree as ET

def replace_svg_fields(
    svg_path: str | Path,
    fields: dict[str, str],
) -> bytes:
    """Load an SVG template, replace fields, and return SVG bytes."""

    svg_path = Path(svg_path)

    tree = ET.parse(svg_path)
    root = tree.getroot()

    SVG_NS = "http://www.w3.org/2000/svg"

    for field_id, value in fields.items():
        element = root.find(f".//*[@id='{field_id}']")

        if element is None:
            raise ValueError(
                f"SVG field with id '{field_id}' was not found"
            )

        tspans = element.findall(f".//{{{SVG_NS}}}tspan")

        if tspans:
            tspans[0].text = str(value)

            for tspan in tspans[1:]:
                tspan.text = ""

            element.text = None
        else:
            element.text = str(value)

    return ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True,
    )



    
