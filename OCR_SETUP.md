# OCR Setup Instructions

The system now supports **OCR (Optical Character Recognition)** to extract text from scanned/image-based PDFs automatically!

## What is OCR?

OCR allows the system to "read" text from images and scanned documents. When you upload a PDF that contains scanned pages (like a photographed document), the system will:
1. Detect that normal text extraction found little/no text
2. Automatically convert PDF pages to images
3. Use Tesseract OCR to extract text from the images
4. Proceed with analysis as normal

## Installation Steps

### 1. Install Python Packages (Already Done ✅)

```bash
pip install pytesseract pdf2image Pillow
```

### 2. Install Tesseract OCR Executable (Required!)

**For Windows:**

1. Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
   - Direct link: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe

2. Run the installer (tesseract-ocr-w64-setup-*.exe)
   - Install to default location: `C:\Program Files\Tesseract-OCR\`
   - Make sure to check "Add to PATH" during installation

3. Verify installation:
   ```cmd
   tesseract --version
   ```
   You should see something like: `tesseract 5.3.3`

### 3. Install Poppler (Required for PDF to Image Conversion)

**For Windows:**

1. Download Poppler for Windows from: http://blog.alivate.com.au/poppler-windows/
   - Or use this direct link: https://github.com/oschwartz10612/poppler-windows/releases/

2. Extract the zip file to a location like: `C:\Program Files\poppler-24.02.0\`

3. Add Poppler to PATH:
   - Open Environment Variables
   - Add `C:\Program Files\poppler-24.02.0\Library\bin` to your PATH
   - Restart your terminal

4. Verify installation:
   ```cmd
   pdfinfo -v
   ```

### 4. Configure Tesseract Path (If Not in PATH)

If Tesseract is not in your PATH, you need to tell pytesseract where to find it:

Edit `backend/video_processor.py` and add this line at the top of the `extract_text_with_ocr` function:

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Testing OCR

Once everything is installed, restart the backend server and try uploading a scanned PDF. You should see in the logs:

```
   ⚠️ WARNING: Very little text extracted (0 chars).
   🔍 Attempting OCR to extract text from scanned PDF...
   📸 Converting PDF pages to images for OCR...
   ✅ Converted 3 pages to images
   🔍 Running OCR on page 1/3...
   ✅ Page 1: Extracted 542 characters
   ...
   ✅ OCR Complete: Extracted 1635 characters from 3 pages
```

## Troubleshooting

### Error: "Tesseract is not installed"
- Make sure Tesseract is installed and in your PATH
- Try running `tesseract --version` in cmd
- If that doesn't work, add the full path to tesseract.exe in the code

### Error: "Could not convert PDF to images"
- Make sure Poppler is installed and in your PATH
- Try running `pdfinfo -v` in cmd
- Add Poppler's bin folder to PATH if needed

### Error: "OCR extracted no text"
- The PDF might be blank or very low quality
- Try increasing DPI in the code: `convert_from_path(pdf_path, dpi=400)`
- The images might need preprocessing (denoising, contrast adjustment)

## Supported Languages

By default, OCR uses English (`lang='eng'`). To support other languages:

1. Download language data from: https://github.com/tesseract-ocr/tessdata
2. Place .traineddata files in: `C:\Program Files\Tesseract-OCR\tessdata\`
3. Update the OCR function: `pytesseract.image_to_string(image, lang='eng+fra')` for English + French

## Performance Notes

- OCR is slower than normal text extraction (expect 2-5 seconds per page)
- Higher DPI = better accuracy but slower processing
- Large PDFs may take a while to process
- The system automatically falls back to OCR only when needed
