# Running the Ollama Model Benchmark

## Overview
This repository contains a simple Python script that:

1. Discovers all models installed in the Ollama server.
2. Runs each model with a fixed prompt.
3. Measures token‑per‑second throughput.
4. Unloads the model after testing.

The script is intentionally lightweight and can be executed on any machine with Python 3.8+ and `requests`.

## Prerequisites

- **Python 3.8 or newer**
- **`requests` library** – install with `pip install requests`
- **Ollama server** running locally or reachable at `http://172.31.128.1:11434`

> **Note:** The script uses the public Ollama HTTP API. If your Ollama instance uses a different address or requires authentication, adjust `OLLAMA_HOST` in the script accordingly.

## Installation

```bash
# Clone the repository (or just copy the script into your project)
git clone https://github.com/your-org/ollama-benchmark.git
cd ollama-benchmark

# (Optional) Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt  # or: pip install requests
```

If you prefer not to use a virtual environment, you can simply run `pip install requests` globally.

## Usage

```bash
# Make the script executable (optional)
chmod +x bench_test_models.py

# Run the benchmark
./bench_test_models.py
```

The script will print output similar to the following:

```
Found 3 models: llama2, mistral, gpt2

Testing model 'llama2'...
  Prompt sent: Hello, Ollama!
  Tokens generated: 45
  Time elapsed: 1.23 s
  Tokens per second: 36.60
  Unloaded model 'llama2'.

Testing model 'mistral'...
  Prompt sent: Hello, Ollama!
  Tokens generated: 40
  Time elapsed: 0.98 s
  Tokens per second: 40.82
  Unloaded model 'mistral'.
```

You can customize the prompt by editing the `PROMPT` variable near the top of `bench_test_models.py`.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file.

---

### Troubleshooting

- **Connection errors** – Ensure the Ollama server is running and accessible at the host/port defined in `OLLAMA_HOST`.
- **Empty model list** – Verify that at least one model is installed by running `curl http://172.31.128.1:11434/api/tags` manually.
- **Permission errors** – If running on Windows or with restricted permissions, try running the terminal as an administrator.

---

Happy benchmarking!