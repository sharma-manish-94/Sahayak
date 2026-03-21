# Local LLM Setup (Ollama)

## Why Use a Local LLM?

During development you iterate fast — testing prompts, tool selection, response formatting. Every Sonnet API call costs money. A local model via Ollama costs nothing and responds in ~1-3 seconds for 8-14B models.

| Mode | Model | Cost | Quality | Use When |
|------|-------|------|---------|----------|
| **Production** | Claude Sonnet | ~$3/M input, $15/M output | Excellent multilingual + tool use | Demo, pitch video, real users |
| **Dev (local)** | Qwen 2.5 14B | Free | Good tool use, decent Hindi | Prompt iteration, tool plumbing, UI testing |
| **Dev (local)** | Llama 3.1 8B | Free | Basic tool use | Fast iteration, English-only testing |
| **Dev (local)** | Gemma 3 12B | Free | Good reasoning | Testing logic, scheme search |

## Setup

### 1. Install Ollama

```bash
# Windows (winget)
winget install Ollama.Ollama

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull a Model

```bash
# Recommended: best balance of tool use + multilingual for Sahayak
ollama pull qwen2.5:14b

# Lighter alternative (faster, less accurate)
ollama pull llama3.1:8b

# Another option (good reasoning)
ollama pull gemma3:12b
```

**Disk space**: ~8GB for 14B models, ~4.5GB for 8B models.

**RAM**: 14B models need ~10GB RAM, 8B models need ~6GB. If your machine has <16GB RAM, stick with 8B.

### 3. Verify Ollama is Running

```bash
# Should show the model you pulled
ollama list

# Test it works
ollama run qwen2.5:14b "Say hello in Hindi"
# Expected: नमस्ते or similar
```

Ollama runs a local server at `http://localhost:11434` automatically.

## Configuration

Sahayak ships two config files:

| File | Primary Model | Fallback | Cost |
|------|---------------|----------|------|
| `openclaw.sahayak.json` | Claude Sonnet | Ollama Qwen 2.5 14B | API costs (Sonnet) |
| `openclaw.sahayak.dev.json` | Ollama Qwen 2.5 14B | Llama 3.1 8B, Gemma 3 12B | Free |

### Using the Dev Config (Free)

Copy the dev config to your OpenClaw config location:

```bash
# Linux/macOS
cp sahayak/openclaw.sahayak.dev.json ~/.openclaw/openclaw.json

# Windows
copy sahayak\openclaw.sahayak.dev.json %USERPROFILE%\.openclaw\openclaw.json
```

Or set via environment variable:

```bash
export OPENCLAW_CONFIG_PATH=./sahayak/openclaw.sahayak.dev.json
```

### Using Production Config (Sonnet + Ollama Fallback)

```bash
cp sahayak/openclaw.sahayak.json ~/.openclaw/openclaw.json
```

In this mode, Sonnet is primary. If the Anthropic API is down or you hit rate limits, it falls back to the local Ollama model automatically.

### Switching Models Without Changing Config

You can override the model at the CLI level:

```bash
# Force Ollama for this session
openclaw gateway run --model ollama/qwen2.5:14b

# Force Sonnet for this session
openclaw gateway run --model anthropic/claude-sonnet-4-20250514
```

## Model Recommendations for Sahayak

### Tool Use Capability

Sahayak relies heavily on tool calling (8 MCP tools). Not all local models handle tool use well.

| Model | Tool Use | Hindi | Compound Queries | Recommendation |
|-------|----------|-------|------------------|----------------|
| `qwen2.5:14b` | Strong | Good | Handles well | **Best for Sahayak dev** |
| `qwen2.5:7b` | Moderate | OK | Sometimes misses | OK for simple tests |
| `llama3.1:8b` | Moderate | Weak | Often misses | English-only testing |
| `gemma3:12b` | Good | Moderate | Good | Good alternative |
| `mistral:7b` | Moderate | Weak | Poor | Not recommended |
| `phi4:14b` | Good | Moderate | Good | Good alternative |

### Hindi/Multilingual Quality

For testing Hindi responses, `qwen2.5:14b` is the best local option. It understands Devanagari, handles Hinglish, and generates readable Hindi. Smaller models tend to mix scripts or produce garbled Hindi.

Quick test:

```bash
ollama run qwen2.5:14b "गेहूं का भाव बताओ भोपाल में। कृपया हिंदी में जवाब दें।"
```

If the response is coherent Hindi, the model works for Sahayak dev.

## Dev Config Anatomy

```json
{
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://localhost:11434/v1",
        "api": "openai-completions",
        "apiKey": "ollama-local",
        "models": [
          {
            "id": "qwen2.5:14b",
            "name": "Qwen 2.5 14B (local)",
            "reasoning": false,
            "input": ["text"],
            "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 },
            "contextWindow": 32768,
            "maxTokens": 8192
          }
        ]
      }
    }
  },

  "agents": {
    "list": [{
      "id": "sahayak",
      "model": {
        "primary": "ollama/qwen2.5:14b",
        "fallbacks": ["ollama/llama3.1:8b", "ollama/gemma3:12b"]
      }
    }]
  }
}
```

Key points:
- `baseUrl`: Ollama's OpenAI-compatible endpoint at `/v1`
- `api: "openai-completions"`: Tells OpenClaw to use the OpenAI chat completions protocol
- `apiKey: "ollama-local"`: Dummy key (Ollama doesn't need auth locally)
- `cost: all zeros`: Local models are free — shows $0.00 in usage tracking
- `fallbacks`: If the primary model fails (e.g., Ollama crashed), tries the next model

## Adding a Custom Model

If you pull a different model from Ollama, add it to the config:

```bash
# Pull the model
ollama pull deepseek-r1:14b
```

Then add to the `models` array in your config:

```json
{
  "id": "deepseek-r1:14b",
  "name": "DeepSeek R1 14B",
  "reasoning": true,
  "input": ["text"],
  "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 },
  "contextWindow": 65536,
  "maxTokens": 8192
}
```

And reference it in the agent:

```json
"model": {
  "primary": "ollama/deepseek-r1:14b"
}
```

## Connecting to a Remote Ollama Instance

If you run Ollama on a more powerful machine (e.g., a GPU server):

```bash
# On the server
OLLAMA_HOST=0.0.0.0 ollama serve
```

Then update your config:

```json
"ollama": {
  "baseUrl": "http://192.168.1.100:11434/v1"
}
```

## Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is listening
curl http://localhost:11434/api/tags
# Should return {"models":[...]}

# If not, start it
ollama serve
```

### Model Not Found

```bash
# List pulled models
ollama list

# If model is missing, pull it
ollama pull qwen2.5:14b
```

### Slow Responses

- Check GPU usage: `nvidia-smi` (NVIDIA) or Task Manager → GPU
- If running on CPU only, expect 5-15 seconds per response for 14B models
- Switch to a 7-8B model for faster iteration: `ollama/qwen2.5:7b`
- Close other GPU-intensive apps

### Tool Calls Not Working

Some local models have weak tool use. Symptoms:
- Agent responds with text but never calls MCP tools
- Agent calls wrong tool or with wrong parameters
- Agent hallucinates tool responses instead of calling them

Fixes:
1. Use `qwen2.5:14b` (best local tool use for Sahayak)
2. Switch to Sonnet for tool-heavy testing
3. Simplify the system prompt for local models (fewer instructions = better adherence)

### Out of Memory

```bash
# Check model memory usage
ollama ps

# If OOM, use a smaller model
ollama pull qwen2.5:7b
# Update config: "primary": "ollama/qwen2.5:7b"
```

## Cost Comparison

Rough estimates for a typical dev session (100 interactions):

| Setup | Input Tokens | Output Tokens | Cost |
|-------|-------------|---------------|------|
| Claude Sonnet (all) | ~200K | ~100K | ~$2.10 |
| Ollama dev + Sonnet demo | ~20K (Sonnet) | ~10K (Sonnet) | ~$0.21 |
| Ollama only | 0 | 0 | $0.00 |

**Recommendation**: Use `openclaw.sahayak.dev.json` for daily development. Switch to `openclaw.sahayak.json` when testing the final demo flow or recording the pitch video.
