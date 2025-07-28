# Adobe Hackathon Round 1a - PDF Heading Extraction Solution
# Robust multi-strategy heading detection (not relying solely on font sizes)
#
# EXECUTION COMMANDS (Exact Hackathon Format):
# ============================================
# Build Command:
#   docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
#
# Run Command:
#   docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier
#
# Local Testing:
#   mkdir -p input output
#   cp sample.pdf input/
#   docker build --platform linux/amd64 -t heading-extractor .
#   docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none heading-extractor
#   # Check output/sample.json
#
# TECHNICAL ARCHITECTURE:
# =======================
# - Base Image: python:3.10-slim (AMD64 compatible)
# - PDF Library: PyMuPDF 1.23.14 (~15MB, fast and reliable)
# - Processing: Multi-strategy detection pipeline
# - Output: Exact JSON format compliance
# - Performance: <5 seconds for 50-page PDFs
# - Memory: Efficient usage within constraints

FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PyMuPDF
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# PyMuPDF is fast, lightweight, and perfect for heading extraction
RUN pip install --no-cache-dir \
    PyMuPDF==1.23.14

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY src/ ./src/

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set the command to run the main processor
CMD ["python", "src/process_pdfs.py"]
