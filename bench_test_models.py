#!/usr/bin/env python3
"""
Benchmark script for Ollama models.
Includes:
- Discover all installed models
- Run a fixed prompt on each model
- Measure tokens per second (generation only)
- Report GPU/VRAM usage, RAM usage, and (placeholder) CPU usage
- Report the generated response text
- Report cold‑start time separately
- Unload model after each test
- At the end, output a table sorted by tokens/s (generation only)
"""

import json
import time
from typing import Dict, List

import requests
import psutil

OLLAMA_HOST = "http://172.31.128.1:11434"
PROMPT = "Quem é o presidente do Brasil?"

# --------- Helper functions ---------------------------------

def get_model_tags() -> List[str]:
    """Return list of installed model names."""
    url = f"{OLLAMA_HOST}/api/tags"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return [m["name"] for m in data.get("models", [])]


def get_ps() -> Dict:
    """Return JSON from /api/ps (running models)."""
    url = f"{OLLAMA_HOST}/api/ps"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def unload_model(name: str):
    """Unload a model immediately (keep_alive=0)."""
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {"model": name, "keep_alive": 0}
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()


def test_model(name: str, prompt: str) -> Dict:
    """Send prompt to model and return metrics.
    Includes generation TPS, cold‑start time, GPU/VRAM usage, RAM usage, and the response text.
    """
    # ---- Cold‑start measurement (load time) ----
    load_url = f"{OLLAMA_HOST}/api/generate"
    load_payload = {"model": name, "prompt": "", "stream": False}
    load_start = time.time()
    load_resp = requests.post(load_url, json=load_payload, timeout=60)
    load_resp.raise_for_status()
    load_elapsed = time.time() - load_start
    load_data = load_resp.json()
    cold_start_ms = load_data.get("load_duration", 0) / 1_000_000  # ns to ms
    cold_start = cold_start_ms if cold_start_ms else load_elapsed * 1000

    # ---- Generation measurement ----
    gen_url = f"{OLLAMA_HOST}/api/generate"
    gen_payload = {"model": name, "prompt": prompt, "stream": False}
    gen_start = time.time()
    gen_resp = requests.post(gen_url, json=gen_payload, timeout=60)
    gen_elapsed = time.time() - gen_start
    gen_resp.raise_for_status()
    data = gen_resp.json()

    # Tokens generated
    eval_count = data.get("eval_count") or 0
    total_tokens = eval_count

    # Generation time (exclude cold‑start)
    gen_time = data.get("eval_duration", 0) / 1_000_000_000  # ns -\u003e s
    tps = total_tokens / gen_time if gen_time > 0 else 0

    # GPU/VRAM and RAM usage from /api/ps
    ps_data = get_ps()
    entry = next((m for m in ps_data.get("models", []) if m.get("model") == name), None)
    size_vram = entry.get("size_vram") if entry else 0
    size_total = entry.get("size") if entry else 0

    # Percentages using system total memory as placeholder for VRAM
    total_mem = psutil.virtual_memory().total
    gpu_percent = (size_vram / total_mem * 100) if total_mem else 0
    ram_percent = (size_total / total_mem * 100) if total_mem else 0

    return {
        "text": data.get("response", ""),
        "tokens": total_tokens,
        "elapsed": gen_elapsed,
        "tps": tps,
        "cold_start_ms": cold_start,
        "gpu_bytes": size_vram,
        "gpu_percent": gpu_percent,
        "ram_bytes": size_total,
        "ram_percent": ram_percent,
    }

# --------- Main ------------------------------------------------

def main():
    models = get_model_tags()
    if not models:
        print("No models found.")
        return
    print(f"Found {len(models)} models: {', '.join(models)}")

    results = []

    for name in models:
        print(f"\n ")
        print (f"\n ##########################################")
        print(f"\n ## Testing model: '{name}'...")
        print (f"\n ##########################################")
        try:
            result = test_model(name, PROMPT)
            print(f"  Prompt sent: {PROMPT}")
            print(f"  Cold‑start time: {result['cold_start_ms']:.1f} ms")
            print(f"  Response: {result['text']}\n")
            print(f"  Tokens generated: {result['tokens']}")
            print(f"  Time elapsed (generation): {result['elapsed']:.2f} s")
            print(f"  Tokens per second (generation only): {result['tps']:.2f}")
            print(f"  GPU/VRAM used: {result['gpu_bytes']:,} bytes ({result['gpu_percent']:.1f}% of total memory) ")
            print(f"  RAM used: {result['ram_bytes']:,} bytes ({result['ram_percent']:.1f}% of total memory) ")

            results.append({"model": name, **result})
        except Exception as e:
            print(f"  Error testing model: {e}")
        finally:
            try:
                unload_model(name)
                print(f"  Unloaded model '{name}'.")
            except Exception as e:
                print(f"  Error unloading model: {e}")

    # Sort by tokens per second (generation only) descending
    results.sort(key=lambda r: r["tps"], reverse=True)

    # Print table
    header = [
        "Model", "Tokens/s", "Cold‑start ms", "GPU (bytes)", "GPU %", "RAM (bytes)", "RAM %", "Response"
    ]
    print("\n\n=== Benchmark Summary (sorted by Tokens/s) ===")
    print("{:<30} {:>10} {:>15} {:>15} {:>7} {:>15} {:>7} {}".format(*header))
    for r in results:
        print(
            f"{r['model']:<30} {r['tps']:>10.2f} {r['cold_start_ms']:>15.1f} {r['gpu_bytes']:>15,d} {r['gpu_percent']:>7.1f} {r['ram_bytes']:>15,d} {r['ram_percent']:>7.1f} {r['text'][:50]}"
        )

if __name__ == "__main__":
    main()
