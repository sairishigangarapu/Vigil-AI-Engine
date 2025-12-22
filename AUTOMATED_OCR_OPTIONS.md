# Automated OCR Installation (No Manual Downloads)

## ⚠️ The Reality on Windows:

**Tesseract** and **Poppler** are **C++ compiled binaries**, not Python packages. They can't be installed via `pip`. However, there are some automated approaches:

---

## Option 1: Chocolatey (Windows Package Manager) ⭐ BEST

If you have Chocolatey installed:

```powershell
# Install Chocolatey first (if not installed)
# Run PowerShell as Administrator:
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Then install Tesseract and Poppler
choco install tesseract -y
choco install poppler -y
```

**Pros:** Fully automated, adds to PATH automatically  
**Cons:** Requires admin rights, need to install Chocolatey first

---

## Option 2: Conda (If Using Anaconda/Miniconda)

```bash
conda install -c conda-forge tesseract
conda install -c conda-forge poppler
```

**Pros:** Works within conda environment  
**Cons:** Tesseract via conda can be unreliable on Windows

---

## Option 3: Use Pre-Built Python Wheels (Experimental)

Some packages bundle Tesseract, but they're not official:

```bash
pip install pytesseract-windows
```

**Cons:** Not maintained, outdated versions

---

## Option 4: Docker Container 🐳 (Most Automated)

Create a Docker container with everything pre-installed:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

CMD ["python", "backend/main.py"]
```

**Pros:** Completely automated, works everywhere  
**Cons:** Need Docker Desktop for Windows

---

## Option 5: Cloud-Based OCR (No Local Install) ☁️

Use cloud OCR services instead:

### Google Cloud Vision API
```python
from google.cloud import vision

def extract_text_with_cloud_ocr(pdf_path):
    client = vision.ImageAnnotatorClient()
    # Convert PDF to image and send to Google
    # ... implementation
```

### Azure Computer Vision
```python
from azure.cognitiveservices.vision.computervision import ComputerVisionClient

def extract_text_with_azure(pdf_path):
    # Use Azure's Read API
    # ... implementation
```

**Pros:** No local dependencies, high accuracy  
**Cons:** Costs money, requires API keys

---

## Option 6: PowerShell Auto-Download Script 📦

I can create a script that downloads and installs everything automatically:

```powershell
# auto_install_ocr.ps1
$ErrorActionPreference = "Stop"

Write-Host "🚀 Auto-installing OCR dependencies..." -ForegroundColor Green

# Create temp directory
$tempDir = "$env:TEMP\ocr_install"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

# Download Tesseract installer
Write-Host "⬇️ Downloading Tesseract..." -ForegroundColor Yellow
$tessUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
$tessInstaller = "$tempDir\tesseract-setup.exe"
Invoke-WebRequest -Uri $tessUrl -OutFile $tessInstaller

# Silent install Tesseract
Write-Host "📦 Installing Tesseract..." -ForegroundColor Yellow
Start-Process -FilePath $tessInstaller -ArgumentList "/S" -Wait

# Download Poppler
Write-Host "⬇️ Downloading Poppler..." -ForegroundColor Yellow
$popplerUrl = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
$popplerZip = "$tempDir\poppler.zip"
Invoke-WebRequest -Uri $popplerUrl -OutFile $popplerZip

# Extract Poppler
Write-Host "📦 Installing Poppler..." -ForegroundColor Yellow
$popplerDest = "C:\poppler"
Expand-Archive -Path $popplerZip -DestinationPath $popplerDest -Force

# Cleanup
Remove-Item -Recurse -Force $tempDir

Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host "🔄 Restart your terminal and run: python backend\check_ocr_setup.py"
```

**Run with:**
```powershell
powershell -ExecutionPolicy Bypass -File auto_install_ocr.ps1
```

---

## Option 7: Use EasyOCR (Python-Only Alternative) 🐍

Replace Tesseract with EasyOCR (pure Python):

```bash
pip install easyocr
```

**Implementation:**
```python
import easyocr

def extract_text_with_easyocr(pdf_path):
    reader = easyocr.Reader(['en'])
    # Convert PDF to images
    images = convert_from_path(pdf_path, dpi=300)
    
    text = ""
    for img in images:
        # Convert PIL Image to numpy array
        import numpy as np
        img_array = np.array(img)
        result = reader.readtext(img_array)
        text += ' '.join([item[1] for item in result])
    
    return text
```

**Pros:** Pure Python, no external executables  
**Cons:** Slower, larger downloads (300+ MB models), still needs Poppler for PDF→Image

---

## My Recommendation:

### For Development (Quick & Dirty):
**Option 6: PowerShell Auto-Install Script**  
→ I can create this for you right now!

### For Production (Proper Setup):
**Option 1: Chocolatey**  
→ Industry standard for Windows package management

### For Deployment (Server/Cloud):
**Option 4: Docker**  
→ Works on any platform, completely reproducible

---

## What Would You Prefer?

1. 🔧 **I'll create the PowerShell auto-install script** (runs once, installs everything)
2. 🐳 **I'll create a Docker setup** (best for deployment)
3. 🐍 **I'll switch to EasyOCR** (pure Python, but slower)
4. ☁️ **I'll integrate cloud OCR** (Google/Azure)

Let me know which approach you'd like! 🚀
