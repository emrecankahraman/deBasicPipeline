"""
CHECK SYSTEM CAPABILITIES
- CUDA/GPU availability
- CPU cores
- Memory
- Recommended device for embeddings
"""

import torch
import psutil
import os

print("\n" + "="*70)
print("SYSTEM CAPABILITY CHECK")
print("="*70)

# CUDA/GPU Check
print("\n[GPU/CUDA]")
cuda_available = torch.cuda.is_available()
print(f"  CUDA available: {cuda_available}")

if cuda_available:
    gpu_count = torch.cuda.device_count()
    print(f"  GPU count: {gpu_count}")
    
    for i in range(gpu_count):
        gpu_name = torch.cuda.get_device_name(i)
        gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
        print(f"    GPU {i}: {gpu_name} ({gpu_memory:.1f} GB)")
    
    recommended_device = "cuda"
    print(f"\n  Recommended device: {recommended_device}")
else:
    print(f"  Recommended device: cpu")
    recommended_device = "cpu"

# CPU Check
print(f"\n[CPU]")
cpu_count = psutil.cpu_count(logical=True)
cpu_physical = psutil.cpu_count(logical=False)
print(f"  Logical cores: {cpu_count}")
print(f"  Physical cores: {cpu_physical}")
print(f"  CPU percent: {psutil.cpu_percent(interval=1)}%")

# Memory Check
print(f"\n[MEMORY]")
memory = psutil.virtual_memory()
print(f"  Total: {memory.total / (1024**3):.1f} GB")
print(f"  Available: {memory.available / (1024**3):.1f} GB")
print(f"  Used: {memory.used / (1024**3):.1f} GB ({memory.percent}%)")

# Torch info
print(f"\n[TORCH]")
print(f"  PyTorch version: {torch.__version__}")
print(f"  Torch device: {torch.device(recommended_device)}")

print("\n" + "="*70)
print(f"RECOMMENDATION: Use '{recommended_device.upper()}' for embeddings")
print("="*70 + "\n")
