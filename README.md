# Comprehensive RSS Article Extractor with Ollama & MLX-Audio

This script fetches articles from any RSS feed, generates comprehensive extracts using an Ollama LLM, and optionally creates an English audio narration using MLX Audio.

## Requirements

- Python 3.10+
- `requests`, `beautifulsoup4`, `mlx-lm`, `mlx-audio` (for audio)
- Ollama server running with your chosen model

## Installation

```bash
virtualenv -p 3.10 .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

```bash
python rss_to_audio.py --rss-url <RSS_FEED_URL> --site-name <SITE_NAME> [options]
```

### Arguments

| Argument             | Type    | Default                               | Description                                                        |
|----------------------|---------|---------------------------------------|--------------------------------------------------------------------|
| `--ollama-url`       | string  | `http://localhost:11434/api/generate` | Ollama API endpoint                                                |
| `--model-name`       | string  | `gemma3:12b`                          | Ollama model name                                                  |
| `--rss-url`          | string  | **(required)**                        | RSS feed URL to fetch articles from                                |
| `--site-name`        | string  | **(required)**                        | Site name (used in output files and intro narration)               |
| `--content-selector` | string  | `None`                                | CSS selector for main article content (optional)               |
| `--max-articles`     | int     | `10`                                  | Number of articles to process                                      |
| `--audio-model`      | string  | `prince-canuma/Kokoro-82M`            | MLX Audio TTS model path                                           |
| `--audio-voice`      | string  | `bf_emma`                             | MLX Audio TTS voice                                                |
| `--audio-speed`      | float   | `1.0`                                 | Reading speed for audio (1.0 = normal)                             |
| `--audio-lang-code`  | string  | `b`                                  | Language code for TTS (e.g., `b` for British English)                     |
| `--output-dir`       | string  | `./outputs`                           | Directory for output files                                         |

### Example

```bash
python crawler_v2.py
--rss-url "http://thenewstack.io/blog/feed/"
--site-name "The New Stack"
--content-selector .article
--max-articles 3
--ollama-url "http://localhost:11434/api/generate"
--model-name "gemma3:12b"
--audio-model "prince-canuma/Kokoro-82M"
--audio-voice "bf_emma"
--audio-speed 1.1
--output-dir "./outputs"
```

### Output

- A text file with comprehensive extracts:  
  `outputs/the_new_stack_extracts_YYYY-MM-DD.txt`
- An audio file with narration (if MLX Audio is available):  
  `outputs/the_new_stack_extracts_YYYY-MM-DD.wav`

### Notes

- You must have an Ollama server running and the specified model available.
- For audio, you must have `mlx-audio` installed and the model/voice downloaded.
- The script estimates audio duration based on a typical narration speed (150 words per minute).

---

**Enjoy your automated, narrated RSS digests!**
