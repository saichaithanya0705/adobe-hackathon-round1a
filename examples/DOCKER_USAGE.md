# 🐳 Docker Usage Guide - Production Deployment

## 🎯 **Docker-First Approach**

This solution is designed with Docker-first architecture for production deployment, scalability, and consistent execution across environments.

## 🏗️ **Container Architecture**

### **Base Image**
- **Platform**: `python:3.10-slim` (AMD64 compatible)
- **Size**: Optimized for minimal footprint
- **Security**: Non-root user execution
- **Performance**: Efficient resource utilization

### **Container Features**
- ✅ **Isolated Environment**: No external dependencies
- ✅ **Network Disabled**: `--network none` for security
- ✅ **Volume Mounting**: Secure file access
- ✅ **Platform Specific**: AMD64 architecture support

## 🚀 **Production Commands**

### **Exact Hackathon Format**
```bash
# Build Command (Exact Specification)
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .

# Run Command (Exact Specification)
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  mysolutionname:somerandomidentifier
```

### **Development Commands**
```bash
# Build with custom tag
docker build --platform linux/amd64 -t pdf-heading-extractor:latest .

# Run with custom tag
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-heading-extractor:latest
```

## 📁 **Volume Mounting**

### **Required Mounts**
```bash
# Input directory (read-only)
-v $(pwd)/input:/app/input

# Output directory (write)
-v $(pwd)/output:/app/output
```

### **Directory Structure Inside Container**
```
/app/
├── input/          # Mounted from host
├── output/         # Mounted from host
├── src/            # Application code
├── requirements.txt
└── main processing files
```

## 🔧 **Advanced Docker Usage**

### **Custom Resource Limits**
```bash
# Memory limit (recommended: 2GB)
docker run --rm \
  --memory=2g \
  --cpus=2 \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-heading-extractor
```

### **Debug Mode**
```bash
# Interactive debugging
docker run -it --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-heading-extractor \
  /bin/bash
```

### **Logging and Monitoring**
```bash
# Capture logs
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/logs:/app/logs \
  --network none \
  pdf-heading-extractor 2>&1 | tee processing.log
```

## 📊 **Performance Optimization**

### **Multi-Core Processing**
```bash
# Utilize multiple CPU cores
docker run --rm \
  --cpus=4 \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-heading-extractor
```

### **Batch Processing**
```bash
# Process large batches efficiently
docker run --rm \
  --memory=4g \
  --cpus=4 \
  -v $(pwd)/batch_input:/app/input \
  -v $(pwd)/batch_output:/app/output \
  --network none \
  pdf-heading-extractor
```

## 🔒 **Security Features**

### **Network Isolation**
```bash
# Complete network isolation (required)
--network none
```

### **User Security**
```bash
# Run as non-root user (built into image)
# No additional flags needed
```

### **File System Security**
```bash
# Read-only root filesystem
docker run --rm \
  --read-only \
  --tmpfs /tmp \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-heading-extractor
```

## 🏭 **Production Deployment**

### **CI/CD Pipeline**
```bash
# Build stage
docker build --platform linux/amd64 -t pdf-extractor:${BUILD_ID} .

# Test stage
docker run --rm \
  -v $(pwd)/test_input:/app/input \
  -v $(pwd)/test_output:/app/output \
  --network none \
  pdf-extractor:${BUILD_ID}

# Deploy stage
docker tag pdf-extractor:${BUILD_ID} pdf-extractor:latest
```

### **Kubernetes Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdf-heading-extractor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pdf-extractor
  template:
    metadata:
      labels:
        app: pdf-extractor
    spec:
      containers:
      - name: pdf-extractor
        image: pdf-heading-extractor:latest
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: input-volume
          mountPath: /app/input
        - name: output-volume
          mountPath: /app/output
```

## 📈 **Monitoring & Metrics**

### **Container Health Check**
```bash
# Check container status
docker ps -a

# View container logs
docker logs <container_id>

# Monitor resource usage
docker stats <container_id>
```

### **Performance Metrics**
```bash
# Processing time measurement
time docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-heading-extractor
```

## 🔧 **Troubleshooting**

### **Common Docker Issues**
```bash
# Permission denied
sudo docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-heading-extractor

# Platform compatibility
docker build --platform linux/amd64 -t pdf-heading-extractor .

# Memory issues
docker run --rm --memory=4g -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-heading-extractor
```

### **Volume Mount Issues**
```bash
# Verify paths
ls -la input/
ls -la output/

# Check permissions
chmod 755 input/ output/
```

## 🎯 **Best Practices**

1. **Always use platform flag**: `--platform linux/amd64`
2. **Always disable network**: `--network none`
3. **Use resource limits**: `--memory` and `--cpus`
4. **Monitor performance**: Use `docker stats`
5. **Clean up containers**: Use `--rm` flag
6. **Version your images**: Use specific tags

---

**🐳 Docker Excellence**: Production-ready containerization for scalable PDF processing!
