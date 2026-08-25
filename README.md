# PromptPrompt — AI-Powered Prompt Optimizer

**PromptPrompt** turns vague ideas into well-engineered prompts for any LLM. Instead of guessing how to phrase a request, it acts as a consultant: it asks clarifying questions, applies research-backed prompting techniques, and auto-launches the refined prompt in your browser.

---

## Repository Structure

```
.
├── main.py                   # Entry point — wires all components and runs setup
├── api_client.py             # Provider layer — Groq/Gemini/Claude/GPT connectors behind one interface
├── cli.py                    # Rich terminal UI — input, display, and interaction loops
├── optimizer.py              # Core logic — generates clarifying questions and optimizes prompts
├── weblauncher.py            # Automation — opens browser or Claude Code with the final prompt
├── storage.py                # Saves each session as a timestamped .txt file
├── requirements.txt          # Core Python dependencies (CLI)
├── requirements-providers.txt # Optional SDKs for the Gemini/Claude/GPT backends
├── requirements-eval.txt     # Extra dependencies for tests2.py/tests3.py (evaluation only)
├── Open Source Tools.md      # Survey of evaluation tools used in the project
│
├── prompts/                  # Prompt templates loaded at runtime
│   ├── system.txt                    # AI optimizer persona
│   ├── prompting_practices.txt       # Best-practices library injected at optimization
│   ├── task_generate_questions.txt   # Instruction for Step 2 (clarification)
│   └── task_optimize.txt             # Instruction for Steps 3–5 (final optimization)
│
├── tests2.py                 # Evaluation script — token, semantic, ROUGE, TF-IDF metrics
└── tests3.py                 # Relevance score comparison — before vs after (30 cases)
```

---

## How It Works

PromptPrompt uses a **3-tier adaptive system** that classifies task complexity and applies the appropriate prompting techniques automatically.

| Tier | Example tasks | Techniques applied |
|------|---------------|--------------------|
| **1 — Simple** | "Explain blockchain" | Zero-shot, basic role, minimal structure |
| **2 — Medium** | "Write LinkedIn posts about leadership" | Role-based, contextual, few-shot (2–3 examples), XML structure |
| **3 — Complex** | "Complete content marketing strategy" | Advanced role, deep context, few-shot (3–5), chain-of-thought, full XML, guidelines |

### The 5-Step Workflow

1. **Analyze** — user submits a draft; system classifies complexity tier
2. **Clarify** — AI asks 2–5 targeted questions based on tier
3. **Integrate** — answers combined with the best-practices library
4. **Optimize** — appropriate techniques applied automatically
5. **Refine** — user approves or requests changes in an iterative loop

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Promptprompt.git
cd Promptprompt

# 2. (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows

# 3. Install dependencies (core CLI only — enough to use Groq)
pip install -r requirements.txt

# 3b. (Optional) Install the SDK(s) for other optimizer backends you want
#     (Gemini, Claude, GPT) — see "Configuration" below.
pip install -r requirements-providers.txt

# 3c. (Optional) Install extra dependencies to run the evaluation scripts
#     (tests2.py, tests3.py) — these pull in torch/transformers and are not
#     needed to use the CLI itself.
pip install -r requirements-eval.txt
```

---

## Configuration

No manual setup required. On first run, the program detects whether any provider's API key is present and, if not, prompts you interactively:

```
First Time Setup
No API keys detected. Please configure one now.

Which AI provider would you like to use to power PromptPrompt?
  1. Groq (fast & free)
  2. Google Gemini
  3. Anthropic Claude
  4. OpenAI GPT
```

Pick one and paste its key — it's saved to a local `.env` file. **Groq is recommended** (fast and free): get a key at [console.groq.com/keys](https://console.groq.com/keys).

| Provider | .env variable | Needs |
|----------|----------------|-------|
| Groq | `GROQ_API_KEY` | `requirements.txt` (installed by default) |
| Google Gemini | `GEMINI_API_KEY` | `pip install google-generativeai` |
| Anthropic Claude | `ANTHROPIC_API_KEY` | `pip install anthropic` |
| OpenAI GPT | `OPENAI_API_KEY` | `pip install openai` |

You can configure more than one — just add extra `PROVIDER_API_KEY=...` lines to `.env` (or re-run setup by deleting it). If more than one provider is configured, PromptPrompt asks which one should power that session; each optional SDK above is only required for the provider(s) you actually enable (`requirements-providers.txt` installs all three at once).

The `.env` file is listed in `.gitignore` and will never be committed.

---

## Usage

```bash
python main.py
```

The CLI will guide you through the workflow. At the end, the optimized prompt is:
- saved to `prompts/optimized prompts/<timestamp>-session.txt`
- copied to your clipboard
- auto-launched in your browser (default: ChatGPT) or Claude Code

---

## Evaluation Results

Evaluated on 30 prompt cases comparing outputs before and after optimization:

| Metric | Result |
|--------|--------|
| Semantic quality score | **71.41%** |
| Iteration reduction | **66.67%** |
| Token reduction | **65.45%** |
| Average optimization time | **0.8 seconds** |

Key findings:
- Most optimized outputs use fewer tokens than the originals (avg. −65%), with several cases dropping by more than 50% — same meaning, shorter response.
- TF-IDF content coverage stays nearly identical before and after, confirming the optimizer reduces length without losing information.
- Relevance scores improve across almost all 30 cases, with the "after" curve consistently above "before".

### Evaluation Scripts

**`tests2.py`** — pulls prompt pairs from a Google Sheet and computes: token counts (tiktoken), semantic similarity (sentence-transformers), BERT score, ROUGE, TF-IDF content coverage, and readability (textstat).

**`tests3.py`** — plots a before/after relevance score line chart across the 30 cases and saves `relevant_score_comparison.png`.

---

## Supported LLM Targets

The optimizer engine runs on **Groq, Gemini, Claude, or GPT** — whichever provider(s) you configure (see Configuration above). The web launcher can open any of these targets with the final prompt:

- [ChatGPT](https://chatgpt.com) *(default)*
- [Claude](https://claude.ai)
- [Gemini](https://gemini.google.com)
- Claude Code *(terminal, if path is configured)*

---

## Data Sources

- User-generated prompts (direct CLI input)
- Groq API model outputs: `openai/gpt-oss-20b`, `llama-3.3-70b-versatile`
- Evaluation references:
  - https://jilltxt.net/llms-fail-at-70-of-simple-office-tasks/
  - https://fortune.com/2025/07/20/ai-hampers-productivity-software-developers-productivity-study/

---

## AI Assistance Credits

- **Seongsu** — used Claude AI for guidance on the `rich` library, method ordering, and general debugging.
- **Jennifer** — used ChatGPT to refine token counting and ROI-related token metrics (`tests2.py`).
- **Guy Adou** — used Claude Code for debugging and setting up prompt templates.
