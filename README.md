# Vision Agent Demo

Lightweight demo showing a security-style vision agent that detects people using a pose model
and a YOLO detector, then sends alerts via Stream Video. This repo contains a runnable
example (`main.py`) and a small helper (`get_token.py`) for generating Stream tokens.

**Requirements:** Python 3.11+, and access to Stream API credentials and Google Gemini API key.

**Quick start**
- **Initialize the project:**

	```powershell
        uv init
        uv add "vision-agents[getstream, gemini]" vision-agents-plugins-ultralytics ultralytics
	```


- **Environment variables:** create a `.env` or set these in your shell:

	- `STREAM_API_KEY` — Stream API key
	- `STREAM_API_SECRET` — Stream API secret
	- `GEMINI_API_KEY` — Google Gemini API key used by the LLM plugin

	Example `.env` content:

	```text
	STREAM_API_KEY=your_key_here
	STREAM_API_SECRET=your_secret_here
	GEMINI_API_KEY=your_gemini_key_here
	```

**Files of interest**
- [main.py](main.py): Demo agent runner. Loads models, joins a Stream Video call, and sends alerts when people are detected.
- [get_token.py](get_token.py): Simple helper that prints a Stream token for a local user (used for local client demos).
- `yolo11n-pose.pt` and `yolov8n.pt`: Pre-downloaded model files used by the demo .

**Run the demo**

1. Ensure your environment variables are set.
2. Start the agent:

```powershell
uv run --env-file .env main.py
```

The agent will join a Stream Video call with the hard-coded call id `security-demo-working` and begin processing frames.

**Generate a token**

To generate a token for a local client (the script prints the token to stdout):

```powershell
uv run --env-file .env generate_token.py
```
Use the printed token in your Stream Video client to join the same call as the agent.
