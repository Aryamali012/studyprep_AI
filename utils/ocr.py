
from PIL import Image, ImageOps
import pytesseract
import fitz  
import io
import os


def image_preprocess(pil_img: Image.Image) -> Image.Image:
    # basic preprocessing: grayscale, increase size for better OCR
    img = ImageOps.grayscale(pil_img)
    # optional: adaptive thresholding, denoise can be added
    img = img.resize((int(img.width * 1.5), int(img.height * 1.5)))
    return img

def ocr_image(pil_img: Image.Image, lang: str = "eng") -> str:
    img = image_preprocess(pil_img)
    return pytesseract.image_to_string(img, lang=lang)

def extract_text_from_pdf(pdf_path: str, lang: str = "eng") -> str:
    """
    Tries two ways:
    1) If PDF has embedded text, use page.get_text("text")
    2) Otherwise render page to image and run pytesseract
    Returns combined text for all pages.
    """
    doc = fitz.open(pdf_path)
    pages_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Try to get selectable text first
        text = page.get_text("text").strip()
        if text:
            pages_text.append(text)
            continue

        # else render page to image and OCR
        pix = page.get_pixmap(dpi=200)  # increase dpi for better OCR
        img_bytes = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_bytes))
        page_text = ocr_image(pil_img, lang=lang)
        pages_text.append(page_text)

    return "\n\n---PAGE_BREAK---\n\n".join(pages_text)
