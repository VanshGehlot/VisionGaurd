#!/usr/bin/env bash
set -euo pipefail

export MIOPEN_USER_DB_PATH="${MIOPEN_USER_DB_PATH:-$(pwd)/miopen}"
export MIOPEN_FIND_MODE="${MIOPEN_FIND_MODE:-FAST}"
export VLLM_ROCM_USE_AITER="${VLLM_ROCM_USE_AITER:-1}"
export SAFETENSORS_FAST_GPU="${SAFETENSORS_FAST_GPU:-1}"
export VLLM_USE_TRITON_FLASH_ATTN="${VLLM_USE_TRITON_FLASH_ATTN:-0}"
export VLLM_ENABLE_PREFIX_CACHING="${VLLM_ENABLE_PREFIX_CACHING:-1}"

vllm serve Qwen/Qwen2.5-VL-7B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --trust-remote-code \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.85 \
  --mm-encoder-tp-mode data
