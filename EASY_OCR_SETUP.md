# 2-Step OCR Setup (No PATH Configuration!)

The backend now automatically finds Tesseract and Poppler. Just install them anywhere!

## Step 1: Install Tesseract OCR

1. **Download:** https://github.com/UB-Mannheim/tesseract/wiki
2. **Run installer:** `tesseract-ocr-w64-setup-5.3.3.20231005.exe`
3. **Install location:** 
   - Default: `C:\Program Files\Tesseract-OCR` ✅ (automatically detected)
   - Or custom location (update code manually)

**That's it!** The backend will find it automatically.

---

## Step 2: Install Poppler (PDF to Image)

### Option A: Quick Manual Install (Recommended)

1. **Download:** https://github.com/oschwartz10612/poppler-windows/releases/
2. **Get:** `Release-24.08.0-0.zip` (latest version)
3. **Extract to:** `C:\poppler\`
   - Final path should be: `C:\poppler\poppler-24.08.0\Library\bin\`

**Done!** The backend will find it automatically.

### Option B: PowerShell Auto-Download

Run this in PowerShell (as Administrator):

```powershell
# Create folder
New-Item -ItemType Directory -Force -Path "C:\poppler"

# Download Poppler
$url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
$output = "C:\poppler\poppler.zip"
Invoke-WebRequest -Uri $url -OutFile $output

# Extract
Expand-Archive -Path $output -DestinationPath "C:\poppler" -Force
Remove-Item $output

Write-Host "✅ Poppler installed to C:\poppler"
```

---

## Step 3: Verify Installation

```bash
python backend\check_ocr_setup.py
```

Should show:
```
✅ Python Packages
✅ Tesseract OCR
✅ Poppler
✅ OCR Test

🎉 All OCR dependencies are installed and working!
```

---

## What the Code Does Automatically:

The backend checks these locations in order:

**For Tesseract:**
1. `C:\Program Files\Tesseract-OCR\tesseract.exe`
2. `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`
3. `C:\portable_ocr\tesseract\tesseract.exe`

**For Poppler:**
1. `C:\poppler\poppler-24.08.0\Library\bin`
2. `C:\Program Files\poppler\Library\bin`
3. `C:\portable_ocr\poppler\Library\bin`

**No PATH modification needed!** ✨

---

## Custom Locations?

If you installed somewhere else, add your path to the lists in:
`backend/video_processor.py` lines 806-817 (Tesseract) and 819-830 (Poppler)

---

## Test with Scanned PDF:

1. Upload any scanned PDF (image-based)
2. Backend will automatically:
   - Detect it's scanned (< 50 chars extracted)
   - Convert pages to images
   - Run OCR with Tesseract
   - Extract all text
   - Send to Gemini for analysis
3. See results in frontend!

**Expected log output:**
```
🔧 Found Tesseract at: C:\Program Files\Tesseract-OCR\tesseract.exe
🔧 Found Poppler at: C:\poppler\poppler-24.08.0\Library\bin
📸 Converting PDF pages to images for OCR...
✅ Converted 3 pages to images
🔍 Running OCR on page 1/3...
✅ Page 1: Extracted 542 characters
🔍 Running OCR on page 2/3...
✅ Page 2: Extracted 618 characters
🔍 Running OCR on page 3/3...
✅ Page 3: Extracted 475 characters
✅ OCR Complete: Extracted 1635 characters from 3 pages
```

---

## Downloads:

**Tesseract:**  
https://github.com/UB-Mannheim/tesseract/wiki  
(Click "Tesseract at UB Mannheim" → Download Windows installer)

**Poppler:**  
https://github.com/oschwartz10612/poppler-windows/releases/  
(Download latest `Release-X.X.X-X.zip`)

---

## Troubleshooting:

**"Tesseract NOT found":**
- Make sure you installed to `C:\Program Files\Tesseract-OCR`
- Or add your custom path to the code

**"Poppler NOT found":**
- Extract the ZIP to `C:\poppler\`
- Should have: `C:\poppler\poppler-24.08.0\Library\bin\pdfinfo.exe`

**Still not working?**
- Check `backend\LIVE_DEBUG.txt` for detailed logs
- Run `python backend\check_ocr_setup.py` for diagnostics
