# Debug Notes - Manga to Kindle Converter

This document captures debugging insights and findings from development sessions.

---

## Session: 2025-12-27

### Issue 1: "Document is empty" Error During Conversion

**Symptom:** Conversion failed with `lxml.etree.ParserError: Document is empty`

**Root Cause:** ebooklib's `EpubHtml.content` expects bytes, not a string. The HTML content was being set as a string with XML declaration.

**Stack Trace:**
```
File "ebooklib/utils.py", line 96, in get_pages
    body = parse_html_string(item.get_body_content())
File "ebooklib/utils.py", line 48, in parse_html_string
    html_tree = html.document_fromstring(s, parser=utf8_parser)
lxml.etree.ParserError: Document is empty
```

**Fix:** In `converter.py`, changed:
```python
# Before (broken)
chapter.content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html>...</html>"""

# After (working)
html_content = f"""<html xmlns="http://www.w3.org/1999/xhtml">...</html>"""
chapter.content = html_content.encode("utf-8")
```

**Key Learnings:**
- ebooklib expects content as bytes
- Don't include XML declaration - ebooklib adds it
- Always encode HTML content with `.encode("utf-8")`

---

### Issue 2: AI Upscaling Producing Black Images

**Symptom:** Real-ESRGAN ncnn-vulkan binary produced completely black output images.

**Root Cause:** Multiple issues:
1. Model files downloaded from GitHub were actually HTML error pages (GitHub LFS redirect)
2. The binary couldn't find valid model files
3. Output showed: `parse magic failed`, `network graph not ready`

**Investigation:**
```bash
# Model files were ~297KB each - too small
ls -la /app/realesrgan/models/
# Checking content revealed HTML instead of binary
head -c 100 /app/realesrgan/models/realesr-animevideov3-x2.bin
# Output: <!DOCTYPE html>...
```

**Fix:** Switched from ncnn-vulkan binary to `realesrgan-ncnn-py` Python package which bundles working models.

```toml
# pyproject.toml
dependencies = [
    ...
    "realesrgan-ncnn-py>=1.1.0",
]
```

**Key Learnings:**
- GitHub raw URLs for LFS files redirect and may return HTML
- Always verify downloaded binary files aren't HTML error pages
- Python packages with bundled models are more reliable than manual downloads

---

### Issue 3: Missing libomp5 Library

**Symptom:** `ImportError: libomp.so.5: cannot open shared object file`

**Root Cause:** The realesrgan-ncnn-py package requires OpenMP for parallel processing.

**Fix:** Added `libomp5` to Dockerfile:
```dockerfile
RUN apt-get install -y --no-install-recommends \
    ...
    libomp5 \
```

---

### Issue 4: Vulkan GPU Not Accessible in Docker

**Symptom:** Real-ESRGAN uses `llvmpipe` (CPU software renderer) instead of RTX 4070 GPU.

**Investigation:**
```bash
# nvidia-smi works - GPU is accessible
docker compose exec backend nvidia-smi
# Shows RTX 4070 correctly

# But Vulkan only finds llvmpipe
docker compose exec backend vulkaninfo --summary
# GPU0: llvmpipe (LLVM 19.1.7, 256 bits) - CPU device
```

**Root Cause:** nvidia-container-toolkit primarily exposes CUDA, not Vulkan. Vulkan requires:
1. NVIDIA ICD file (`/usr/share/vulkan/icd.d/nvidia_icd.json`)
2. NVIDIA GLX library (`libGLX_nvidia.so.0`)
3. Additional NVIDIA runtime libraries

**Attempted Fixes:**
1. Mounted ICD file from host - Failed: "Could not get 'vkCreateInstance' via 'vk_icdGetInstanceProcAddr'"
2. Set `NVIDIA_DRIVER_CAPABILITIES=graphics,compute,utility` - Not sufficient for Vulkan
3. Tested official nvidia/cuda container - Same issue, only llvmpipe available

**Current Status:** UNRESOLVED - AI upscaling disabled in Docker due to slow CPU-only performance.

**Workaround:** Use Lanczos upscaling which is fast and produces good quality results.

**Potential Solutions (not yet tested):**
1. Use PyTorch-based Real-ESRGAN with CUDA (adds ~2GB to image size)
2. Mount all NVIDIA Vulkan libraries from host
3. Use nvidia-docker2 instead of nvidia-container-toolkit
4. Run Real-ESRGAN outside Docker on host

---

### Issue 5: AI Upscaling API Changed

**Symptom:** `Realesrgan.__init__() got an unexpected keyword argument 'scale'`

**Root Cause:** The `realesrgan-ncnn-py` v2.0.0 API differs from documentation.

**Fix:** Updated `ai_upscaler.py`:
```python
# Before (broken)
Realesrgan(gpuid=gpuid, model=model_id, scale=scale)

# After (working)
Realesrgan(gpuid=gpuid, model=model_id)
# Scale is determined by model: 0=x2, 1=x3, 2=x4
```

---

## Configuration Reference

### Docker GPU Passthrough (docker-compose.yml)
```yaml
backend:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `ENABLE_AI_UPSCALING=1` | Enable Real-ESRGAN (disabled by default in Docker) |
| `FORCE_CPU_UPSCALING=1` | Force CPU mode even if GPU available |
| `DISABLE_AI_UPSCALING=1` | Completely disable AI upscaling |

### Required System Libraries (Dockerfile)
```dockerfile
RUN apt-get install -y --no-install-recommends \
    libvulkan1 \
    mesa-vulkan-drivers \
    libomp5 \
    vulkan-tools
```

---

## Performance Notes

| Upscaling Method | Speed | Quality | GPU Required |
|-----------------|-------|---------|--------------|
| None | Instant | Original | No |
| Lanczos | Fast (~100ms/image) | Good | No |
| AI (Real-ESRGAN) CPU | Very Slow (~5-10s/image) | Excellent | No |
| AI (Real-ESRGAN) GPU | Fast (~200ms/image) | Excellent | Yes (Vulkan) |

**Recommendation:** Use Lanczos for Docker deployments until Vulkan GPU support is resolved.

---

## Files Modified

- `backend/app/services/converter.py` - Fixed HTML content encoding
- `backend/app/services/ai_upscaler.py` - Switched to Python package API
- `backend/Dockerfile` - Added libomp5, vulkan-tools, NVIDIA env vars
- `backend/pyproject.toml` - Added realesrgan-ncnn-py dependency
- `docker-compose.yml` - GPU passthrough config, disabled AI upscaling
