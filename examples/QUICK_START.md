# 🚀 Quick Start Guide - PDF Heading Extraction

## ⚡ **5-Minute Setup**

Get started with PDF heading extraction in under 5 minutes!

## 📋 **Prerequisites**

- **Docker** (recommended) OR **Python 3.8+**
- **PDF files** to process
- **5 minutes** of your time

## 🐳 **Method 1: Docker (Recommended)**

### **Step 1: Build Container**
```bash
# Clone/download the repository
cd round_1a

# Build Docker image
docker build --platform linux/amd64 -t pdf-heading-extractor .
```

### **Step 2: Prepare Files**
```bash
# Add your PDF files to input directory
cp your_document.pdf input/

# Verify input directory
ls input/
# Should show: your_document.pdf
```

### **Step 3: Run Processing**
```bash
# Process all PDFs in input directory
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-heading-extractor
```

### **Step 4: Check Results**
```bash
# View generated JSON files
ls output/
# Should show: your_document.json

# View extracted headings
cat output/your_document.json
```

## 🐍 **Method 2: Local Python**

### **Step 1: Install Dependencies**
```bash
# Install required packages
pip install -r requirements.txt
```

### **Step 2: Prepare Files**
```bash
# Add PDF files to input directory
cp your_document.pdf input/
```

### **Step 3: Run Processing**
```bash
# Option A: Main processor
python src/process_pdfs.py

# Option B: Alternative extractor
python src/extract_headings.py
```

### **Step 4: Check Results**
```bash
# View results
cat output/your_document.json
```

## 📊 **Expected Output**

### **Sample JSON Structure**
```json
{
  "title": "Understanding AI",
  "outline": [
    {
      "level": "H1",
      "text": "Introduction",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "What is AI?",
      "page": 2
    },
    {
      "level": "H3",
      "text": "History of AI",
      "page": 3
    }
  ]
}
```

## ⚡ **Performance Expectations**

| Document Size | Processing Time | Memory Usage |
|---------------|-----------------|--------------|
| 10 pages | < 1 second | < 50MB |
| 25 pages | 1-2 seconds | < 100MB |
| 50 pages | 2-5 seconds | < 200MB |
| 100 pages | 5-8 seconds | < 400MB |

## 🔧 **Troubleshooting**

### **Common Issues & Solutions**

#### **Docker Issues**
```bash
# Permission denied
sudo docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-heading-extractor

# Platform issues
docker build --platform linux/amd64 -t pdf-heading-extractor .
```

#### **Python Issues**
```bash
# Module not found
pip install --upgrade pip
pip install -r requirements.txt

# Path issues
python -m src.process_pdfs
```

#### **File Issues**
```bash
# No output generated
# Check if PDF contains text (not just images)
# Verify file permissions

# Empty JSON
# PDF may not have clear heading structure
# Try alternative extractor: python src/extract_headings.py
```

## 🎯 **Advanced Usage**

### **Batch Processing**
```bash
# Process multiple PDFs at once
cp *.pdf input/
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-heading-extractor
```

### **Custom Configuration**
```bash
# For development and testing
python src/process_pdfs.py --debug
python src/extract_headings.py --verbose
```

## 📈 **Next Steps**

### **Integration**
- Use JSON output in your applications
- Build document navigation systems
- Create automated table of contents

### **Customization**
- Modify detection strategies in source code
- Adjust heading level assignments
- Add custom pattern recognition

### **Production Deployment**
- Use Docker for scalable deployment
- Implement batch processing workflows
- Add monitoring and logging

## 📞 **Need Help?**

- **Documentation**: Check `/docs/` directory
- **Technical Details**: See `docs/TECHNICAL_SPECS.md`
- **Performance**: Review `docs/PERFORMANCE_ANALYSIS.md`
- **Issues**: Verify input PDF format and content

---

**🎉 Congratulations!** You're now ready to extract headings from any PDF document with professional-grade accuracy and speed!
