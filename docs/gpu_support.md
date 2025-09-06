# GPU Support Guide

This guide explains how to enable optional Intel® Iris® Xe acceleration in Personal RAG Copilot.

## Iris Xe Capabilities
- Integrated Gen12 graphics with up to 96 Execution Units
- Supports OpenVINO™ for FP32/FP16/INT8 inference
- Best suited for light to medium workloads; no FP64 or XMX matrix engines

## Driver Installation
### Windows
1. Install the latest [Intel Graphics Driver](https://www.intel.com/support) for Iris Xe.
2. (Optional) Install the [oneAPI Base Toolkit](https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit.html) for Level Zero/SYCL development.

### Linux
1. Ensure a recent kernel with i915 drivers.
2. Install OpenCL runtime packages:
   ```bash
   sudo apt install intel-opencl-icd
   ```
3. (Optional) Add oneAPI components for SYCL/Level Zero:
   ```bash
   sudo apt install intel-level-zero-gpu level-zero
   ```

## Exporting Models to OpenVINO
1. Install Optimum and OpenVINO tooling:
   ```bash
   pip install optimum[openvino]
   ```
2. Export the encoder model:
   ```bash
   optimum-cli export openvino --model sentence-transformers/all-MiniLM-L6-v2 openvino_encoder
   ```
3. Export the reranker (optional):
   ```bash
   optimum-cli export openvino --model BAAI/bge-reranker-v2-m3 openvino_reranker
   ```
4. Point the application to the exported directories via configuration.

## Configuration Options
Edit `config/default_settings.yaml` or use environment variables:
- `device_preference`: `auto`, `cpu`, `gpu_openvino`, `gpu_xpu`
- `precision`: `fp32`, `fp16`, or `int8`

Example to force GPU acceleration:
```bash
export DEVICE_PREFERENCE=gpu_openvino
export PRECISION=fp16
```

## Limitations and Fallback
- Iris Xe shares system memory; large models may run out of VRAM.
- When `device_preference` is `auto`, the system automatically falls back to CPU if drivers or resources are unavailable.
- Mixed precision may reduce quality for some models.

## Reverting to CPU
Set the device preference back to CPU:
```bash
export DEVICE_PREFERENCE=cpu
```
Or update `device_preference: cpu` in `config/default_settings.yaml`.
