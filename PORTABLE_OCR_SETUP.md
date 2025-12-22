# Portable OCR Setup (No PATH Required)

This guide shows how to set up OCR without modifying system PATH variables.

## Option 1: Direct Path Configuration (Simplest)

### Step 1: Install Tesseract
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Run `tesseract-ocr-w64-setup-5.3.3.20231005.exe`
3. Install to default location: `C:\Program Files\Tesseract-OCR`
4. **DON'T worry about PATH** - we'll configure it in code

### Step 2: Install Poppler
1. Download: https://github.com/oschwartz10612/poppler-windows/releases/
2. Download `Release-24.08.0-0.zip` (latest version)
3. Extract to: `C:\poppler\` (create this folder)
4. You should now have: `C:\poppler\poppler-24.08.0\Library\bin\`

### Step 3: Configure Backend (Already Done!)
The code in `backend/video_processor.py` is already set up for this.
Just uncomment line 812 if Tesseract isn't in `C:\Program Files\Tesseract-OCR\`

### Step 4: Test
```bash
python backend\check_ocr_setup.py
```

---

## Option 2: Portable Installation Script

Run this PowerShell script to download and configure everything automatically:

```powershell
# Create portable OCR folder
$ocrPath = "C:\portable_ocr"
New-Item -ItemType Directory -Force -Path $ocrPath

# Download Tesseract (you'll need to do this manually from GitHub)
# Place tesseract.exe in C:\portable_ocr\tesseract\

# Download Poppler
$popplerUrl = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
$popplerZip = "$ocrPath\poppler.zip"
Invoke-WebRequest -Uri $popplerUrl -OutFile $popplerZip
Expand-Archive -Path $popplerZip -DestinationPath "$ocrPath\poppler" -Force
Remove-Item $popplerZip

Write-Host "✅ Poppler installed to: $ocrPath\poppler"
Write-Host "⚠️ Still need to install Tesseract manually"
```

---

## Option 3: Use Conda/Virtual Environment (Most Isolated)

If you're using conda or want complete isolation:

```bash
# This won't work on Windows - Tesseract needs manual install
# But you can try:
conda install -c conda-forge tesseract
```

---

## Quick Fix: Manual Path Setting

Edit `backend/video_processor.py` line 812:

**Find this line (currently commented):**
```python
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**Uncomment it:**
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**For Poppler**, add this line at the top of `extract_text_with_ocr()`:
```python
poppler_path = r'C:\poppler\poppler-24.08.0\Library\bin'
```

Then modify the conversion line:
```python
images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
```

---

## What You Actually Need:

**Tesseract:**
- Just install it: https://github.com/UB-Mannheim/tesseract/wiki
- Default location works: `C:\Program Files\Tesseract-OCR`
- Code already configured for this path

**Poppler:**
- Extract to any folder
- Tell the code where it is (see below)

---

## Current Status:

✅ Python packages installed  
⏳ Tesseract - Install to `C:\Program Files\Tesseract-OCR` (default)  
⏳ Poppler - Extract anywhere, configure path in code

The OCR code will **automatically find Tesseract** if installed to the default location. For Poppler, we just need to tell `pdf2image` where to find it.
