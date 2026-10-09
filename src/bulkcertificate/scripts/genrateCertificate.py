
from xhtml2pdf import pisa
from pathlib import Path
from .svg_field_replacer import replace_svg_fields
SCRIPT_DIR = Path(__file__).parent
from io import BytesIO
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF


def svg_to_pdf(svg_bytes: bytes) -> bytes:
    drawing = svg2rlg(BytesIO(svg_bytes))

    if drawing is None:
        raise ValueError("Failed to parse SVG")

    output = BytesIO()

    renderPDF.drawToFile(
        drawing,
        output,
    )

    return output.getvalue()





def generate_certificate(name, output_path):
   
    svg_bytes = replace_svg_fields(
            str(SCRIPT_DIR / "bitmap.svg"),
            {
                "text1": "Siddharth",
            
            },
        )
    
    pdf_bytes = svg_to_pdf(svg_bytes)
 

    Path("test_certificate.pdf").write_bytes(pdf_bytes)

   

  