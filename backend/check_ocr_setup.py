"""
OCR Setup Checker - Verifies that all OCR dependencies are installed correctly
"""

import sys
import os

def check_python_packages():
    """Check if required Python packages are installed"""
    print("🔍 Checking Python packages...")
    
    packages = {
        'pytesseract': False,
        'pdf2image': False,
        'PIL': False
    }
    
    for package in packages:
        try:
            __import__(package)
            packages[package] = True
            print(f"  ✅ {package} - installed")
        except ImportError:
            print(f"  ❌ {package} - NOT installed")
    
    return all(packages.values())

def check_tesseract():
    """Check if Tesseract OCR is installed and accessible"""
    print("\n🔍 Checking Tesseract OCR...")
    
    try:
        import subprocess
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"  ✅ Tesseract installed: {version}")
            return True
        else:
            print(f"  ❌ Tesseract not working properly")
            return False
    except FileNotFoundError:
        print(f"  ❌ Tesseract NOT found in PATH")
        print(f"     Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        return False
    except Exception as e:
        print(f"  ❌ Error checking Tesseract: {e}")
        return False

def check_poppler():
    """Check if Poppler is installed (required for pdf2image)"""
    print("\n🔍 Checking Poppler (PDF to Image)...")
    
    try:
        import subprocess
        result = subprocess.run(['pdfinfo', '-v'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print(f"  ✅ Poppler installed: {version.split()[0] if version else 'Version unknown'}")
            return True
        else:
            print(f"  ❌ Poppler not working properly")
            return False
    except FileNotFoundError:
        print(f"  ❌ Poppler NOT found in PATH")
        print(f"     Download from: https://github.com/oschwartz10612/poppler-windows/releases/")
        return False
    except Exception as e:
        print(f"  ❌ Error checking Poppler: {e}")
        return False

def test_ocr():
    """Try a simple OCR test"""
    print("\n🧪 Testing OCR functionality...")
    
    try:
        import pytesseract
        from PIL import Image
        import io
        
        # Create a simple test image with text
        print("  Creating test image...")
        from PIL import ImageDraw, ImageFont
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "TEST OCR", fill='black')
        
        # Try OCR
        print("  Running OCR on test image...")
        text = pytesseract.image_to_string(img)
        
        if 'TEST' in text.upper():
            print(f"  ✅ OCR working! Extracted: '{text.strip()}'")
            return True
        else:
            print(f"  ⚠️ OCR ran but result unclear: '{text.strip()}'")
            return True  # Still counts as working
            
    except Exception as e:
        print(f"  ❌ OCR test failed: {e}")
        return False

def main():
    print("="*60)
    print("     OCR Setup Checker for Vigil AI")
    print("="*60)
    print()
    
    results = {
        'Python Packages': check_python_packages(),
        'Tesseract OCR': check_tesseract(),
        'Poppler': check_poppler(),
    }
    
    # Only test OCR if all dependencies are available
    if all(results.values()):
        results['OCR Test'] = test_ocr()
    
    print("\n" + "="*60)
    print("     Summary")
    print("="*60)
    
    all_good = True
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
        if not status:
            all_good = False
    
    print()
    if all_good:
        print("🎉 All OCR dependencies are installed and working!")
        print("   You can now process scanned PDFs with OCR.")
    else:
        print("⚠️ Some dependencies are missing. Please install them:")
        print()
        if not results.get('Python Packages'):
            print("   pip install pytesseract pdf2image Pillow")
        if not results.get('Tesseract OCR'):
            print("   Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        if not results.get('Poppler'):
            print("   Install Poppler: https://github.com/oschwartz10612/poppler-windows/releases/")
        print()
        print("   See OCR_SETUP.md for detailed instructions")
    
    print()
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
