# RSS to Audio

This script fetches articles from any RSS feed, generates comprehensive extracts using an Ollama LLM, and optionally creates an English audio narration using MLX Audio.

**Enjoy your automated, narrated RSS digests!**

## Requirements

- Python 3.10+
- `requests`, `beautifulsoup4`, `mlx-audio` (for audio)
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
| `--content-selector` | string  | `None`                                | CSS selector for main article content (optional)                   |
| `--max-articles`     | int     | `10`                                  | Number of articles to process                                      |
| `--audio-model`      | string  | `prince-canuma/Kokoro-82M`            | MLX Audio TTS model path                                           |
| `--audio-voice`      | string  | `bf_emma`                             | MLX Audio TTS voice                                                |
| `--audio-speed`      | float   | `1.0`                                 | Reading speed for audio (1.0 = normal)                             |
| `--audio-lang-code`  | string  | `b`                                   | Language code for TTS (e.g., `b` for British English)              |
| `--output-dir`       | string  | `./outputs`                           | Directory for output files                                         |

### Outputs

- A text file with comprehensive extracts:  
  `outputs/[site-name]_extracts_YYYY-MM-DD.txt`
- An audio file with narration (if MLX Audio is available):  
  `outputs/[site-name]_extracts_YYYY-MM-DD.wav`

### Notes

- You must have an Ollama server running and the specified model available.
- The script estimates audio duration based on a typical narration speed (150 words per minute).

## Blog posts

Don't hesitate to read the following blog posts to find out more AI-generated audio from RSS feeds:

* [Transform RSS feeds into podcasts using AI](https://blog.filador.ch/en/posts/transform-rss-feeds-into-podcasts-using-ai) - English version
* [Transformer des flux RSS en Podcast grâce à l'IA](https://blog.filador.ch/posts/transformer-des-flux-rss-en-podcast-grace-a-l-ia) - French version

