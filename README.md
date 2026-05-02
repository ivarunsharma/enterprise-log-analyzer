# Enterprise Log Analyzer

![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![LangChain](https://img.shields.io/badge/LangChain-0.3-orange)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A web app that takes a production log file, runs it through LangChain + Azure OpenAI, and gives you a structured breakdown of what went wrong, why, and how to fix it. Useful for post-mortems and incident triage when you don't want to grep through thousands of lines manually.

---

## What it does

1. You upload a log file (`.log`, `.txt`, `.out`)
2. The app parses it, groups entries into time windows, and filters down to chunks that actually have errors or warnings
3. Each error chunk is sent to GPT via LangChain to extract **error patterns**
4. Patterns are fed into a second chain to identify **root causes**
5. Root causes feed into a third chain to generate **fix recommendations**
6. Results are shown on an interactive dashboard with Plotly charts
7. You can download a PDF report

---

## Tech stack

| Layer | Library |
|-------|---------|
| Web server | **FastAPI** + Uvicorn |
| LLM orchestration | **LangChain** (LCEL) + `langchain-openai` |
| LLM backend | **Azure OpenAI** (GPT-4.1-mini by default) |
| Charts | **Plotly** |
| PDF generation | **ReportLab** |
| Data models | **Pydantic v2** |
| Config | **python-dotenv** |
| Templates | **Jinja2** + Tailwind CSS (CDN) |

---

## Prerequisites

- Python 3.11+
- An Azure OpenAI resource with a deployed model (GPT-4 or GPT-4o class works best)
- The deployment name, endpoint URL, and API key

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/ivarunsharma/enterprise-log-analyzer.git
cd enterprise-log-analyzer
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file and fill in your Azure OpenAI credentials:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
```

> **Local runs** — `app/config.py` calls `load_dotenv("../.env")`, so it expects the `.env` file **one level above** this directory by default. Either place `.env` there, or change the path in `app/config.py` to `load_dotenv(".env")` if you prefer it inside the project.
>
> **Docker runs** — `docker-compose.yml` uses `env_file: - .env`, which looks for `.env` **inside** this directory (alongside `docker-compose.yml`). Place your `.env` here when using Docker.

---

## Running locally

From inside the `enterprise-log-analyzer/` directory:

```bash
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Running with Docker

```bash
docker-compose up --build
```

This starts the app on port 8000. Make sure your `.env` file is present inside the `enterprise-log-analyzer/` directory before building — `docker-compose.yml` mounts it via `env_file`.

To stop:

```bash
docker-compose down
```

---

## Usage

1. Go to `http://localhost:8000`
2. Drag and drop (or browse) a log file
3. Choose which severity levels to include in the analysis
4. Click **Analyze Log File** and wait — analysis takes 20–60 seconds depending on log size
5. The dashboard shows:
   - Summary stats (total lines, errors, warnings, patterns found)
   - Timeline chart of log events over time
   - Severity distribution pie chart
   - Top components by error/warn count
   - Detected error patterns with counts and sample messages
   - Root cause analysis with confidence scores
   - Ranked fix recommendations with effort estimates
6. Use the **Download PDF Report** button for a shareable summary

### Supported log formats

The parser handles these formats out of the box:

| Format | Example |
|--------|---------|
| Python logging | `2024-01-15 10:23:45,123 ERROR root — message` |
| Log4j / Java | `2024-01-15 10:23:45.123 [thread] ERROR com.example — message` |
| Generic timestamped | `2024-01-15 10:23:45 ERROR some message` |
| Syslog | `Jan 15 10:23:45 hostname sshd[1234]: message` |

Anything that doesn't match a known format falls back to keyword-based severity inference (looks for words like `error`, `fatal`, `warn`, `timeout`, etc.).

Sample log files for testing are in `tests/sample_logs/`.

---

## Configuration

Settings live in `app/config.py` and are read from environment variables (via `python-dotenv`):

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | required | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | required | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_VERSION` | required | API version (e.g. `2024-12-01-preview`) |
| `AZURE_OPENAI_DEPLOYMENT` | required | Deployment name |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max log file size |
| `CHUNK_WINDOW_MINUTES` | `5` | Time window per log chunk |
| `CHUNK_MAX_LINES` | `50` | Max lines per chunk |
| `MAX_CHUNKS_FOR_LLM` | `200` | Cap on chunks sent to the LLM |

Raising `MAX_CHUNKS_FOR_LLM` gives more thorough analysis but increases cost and latency linearly.

---

## Project structure

```
enterprise-log-analyzer/
├── main.py                  # FastAPI app entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example             # copy to .env and fill in credentials
├── static/
│   ├── css/app.css
│   └── js/app.js            # upload form + polling logic
├── app/
│   ├── config.py            # settings loaded via python-dotenv + os.getenv
│   ├── templates/           # Jinja2 HTML templates
│   ├── api/
│   │   ├── upload.py        # POST /api/upload
│   │   ├── analysis.py      # GET /api/analysis/{job_id}
│   │   └── report.py        # GET /api/report/{job_id} (PDF)
│   ├── analysis/
│   │   ├── analyzer.py      # orchestrates the full pipeline
│   │   ├── chains.py        # LangChain LCEL chain definitions
│   │   ├── llm_client.py    # Azure OpenAI client instances
│   │   └── prompts.py       # system + human prompt templates
│   ├── ingestion/
│   │   ├── parser.py        # regex-based log line parser
│   │   ├── filter.py        # severity filtering + stats
│   │   └── chunker.py       # time-window chunking
│   ├── models/
│   │   ├── log_entry.py     # LogEntry, LogChunk, Severity
│   │   └── analysis.py      # AnalysisResult, ErrorPattern, etc.
│   ├── reporting/
│   │   ├── chart_builder.py # Plotly chart JSON builders
│   │   └── pdf_generator.py # ReportLab PDF generation
│   └── storage/
│       └── job_store.py     # in-memory job/result store
├── tests/
│   └── sample_logs/         # sample log files for testing
└── uploads/                 # temp storage during analysis (gitignored)
```

---

## Upload cleanup

Uploaded log files are stored temporarily in the `uploads/` directory while analysis runs. The app automatically deletes all files in that directory on shutdown (Ctrl+C, `SIGTERM`, `docker-compose down`, etc.) via a FastAPI `@app.on_event("shutdown")` handler in `main.py`. No manual cleanup is needed between runs.

If the process is killed hard (`kill -9`, power loss) the cleanup won't run — in that case just delete the contents of `uploads/` manually.

---

## Limitations

- **In-memory job store** — restarting the server loses all job history. Jobs are not persisted to disk.
- **No auth** — anyone who can reach the server can upload files and see results. Don't expose this publicly without adding authentication.
- **Large files** — very large logs (>10k error lines) hit the `MAX_CHUNKS_FOR_LLM` cap and only the first N windows are analyzed. The dashboard shows a note when this happens.

---

## License

MIT
