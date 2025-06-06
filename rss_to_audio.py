#!/usr/bin/env python3
import argparse
import requests
import json
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import time
import sys
import re
import os
from datetime import datetime

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Try to import MLX modules for audio generation, set flag if unavailable
try:
    import mlx_lm
    import mlx_audio
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    print("⚠️  mlx-audio not found. Audio generation will be skipped.")
    print("Install with: pip install mlx-lm mlx-audio")

def parse_args():
    """
    Parse command-line arguments for script configuration.
    """
    parser = argparse.ArgumentParser(description="Comprehensive RSS Article Extractor with Ollama & Audio")
    parser.add_argument('--ollama-url', default="http://localhost:11434/api/generate", help="Ollama API endpoint")
    parser.add_argument('--model-name', default="gemma3:12b", help="Ollama model name")
    parser.add_argument('--rss-url', required=True, help="RSS feed URL")
    parser.add_argument('--content-selector', default=None, help="CSS selector for main article content (optional)")
    parser.add_argument('--site-name', required=True, help="Site name (for output files and intro)")
    parser.add_argument('--max-articles', type=int, default=10, help="Number of articles to process")
    parser.add_argument('--audio-model', default="prince-canuma/Kokoro-82M", help="MLX Audio TTS model path")
    parser.add_argument('--audio-voice', default="bf_emma", help="MLX Audio TTS voice")
    parser.add_argument('--audio-speed', type=float, default=0.8, help="Audio reading speed")
    parser.add_argument('--audio-lang-code', default="b", help="Audio language code (e.g., 'b' for British English)")
    parser.add_argument('--output-dir', default="./outputs", help="Directory for output files")
    return parser.parse_args()

def check_ollama_status(ollama_url):
    """
    Check if the Ollama API is accessible.
    """
    try:
        base_url = ollama_url.split('/api/')[0]
        response = requests.get(f"{base_url}/api/tags")
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_site_name(rss_url, override=None):
    """
    Extract site name from URL or use provided override.
    """
    if override:
        return override
    domain = urlparse(rss_url).netloc
    return domain.replace('www.', '').split('.')[0].capitalize()

def get_latest_articles_from_rss(rss_url, max_articles=5):
    """
    Parse RSS feed and return a list of articles (title, url, description, pub_date).
    """
    try:
        print(f"🔍 Fetching RSS feed from {rss_url}")
        response = requests.get(rss_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        articles = []
        items = root.findall('.//item')
        print(f"✅ Found {len(items)} items in RSS feed")
        for item in items[:max_articles]:
            title = item.findtext('title', default="No title").strip()
            url = item.findtext('link', default="").strip()
            description = item.findtext('description', default="")
            description = re.sub(r'<[^>]+>', '', description).strip()
            pub_date = item.findtext('pubDate', default="").strip()
            if url and title:
                articles.append({
                    'title': title,
                    'url': url,
                    'description': description,
                    'pub_date': pub_date
                })
        return articles
    except ET.ParseError:
        # Fallback: try parsing with BeautifulSoup if XML fails
        return get_latest_articles_from_rss_alternative(rss_url, max_articles)
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return []

def get_latest_articles_from_rss_alternative(rss_url, max_articles=5):
    """
    Alternative RSS parsing using BeautifulSoup (for malformed feeds).
    """
    try:
        response = requests.get(rss_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        articles = []
        items = soup.find_all('item')
        for item in items[:max_articles]:
            title = item.find('title').get_text(strip=True)
            url = item.find('link').get_text(strip=True)
            description = item.find('description').get_text(strip=True)
            description = re.sub(r'<[^>]+>', '', description).strip()
            articles.append({
                'title': title,
                'url': url,
                'description': description,
                'pub_date': ''
            })
        return articles
    except Exception as e:
        print(f"Alternative RSS parsing failed: {e}")
        return []

def extract_article_content(url, content_selector=None):
    """
    Extract main content from an article URL using a custom selector if provided,
    otherwise fallback to heuristics and common selectors.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        content = ""
        if content_selector:
            content_div = soup.select_one(content_selector)
            if content_div:
                paragraphs = content_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # Fallback: try article tag
        if not content or len(content) < 500:
            article_tag = soup.find('article')
            if article_tag:
                paragraphs = article_tag.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # Fallback: use all paragraphs
        if not content or len(content) < 500:
            paragraphs = soup.find_all('p')
            all_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            sentences = all_text.split('.')
            filtered_sentences = [
                sentence.strip() for sentence in sentences
                if len(sentence.strip()) > 20 and not any(skip in sentence.lower() for skip in [
                    'subscribe', 'newsletter', 'follow us', 'share this', 'copyright', 'privacy policy'
                ])
            ]
            content = '. '.join(filtered_sentences[:50])
        
        # Clean up whitespace and limit length
        content = content.replace('\n', ' ').replace('\r', ' ')
        content = ' '.join(content.split())
        return content
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return ""

def create_comprehensive_extract(text, title, ollama_url, model_name):
    """
    Use Ollama LLM to generate a comprehensive extract for narration.
    """
    prompt = f"""Create a comprehensive and detailed extract of this article in English. This extract will be read aloud, so make it engaging and complete.

Title: {title}

Content: {text}

Instructions:
- Create a detailed extract of 30 sentences maximum
- Include all key points, important details, and context
- Maintain the technical depth and nuance of the original
- Use clear, professional English suitable for audio narration
- Structure it as a flowing narrative that's pleasant to listen to
- Include specific examples, data points, or quotes if mentioned
- Don't mention that this is an extract, summary or a text made for audio
- Make it comprehensive enough to understand the full article content

Extract:"""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 500
        }
    }
    try:
        response = requests.post(ollama_url, json=payload, timeout=90)
        response.raise_for_status()
        result = response.json()
        return result.get('response', '').strip()
    except Exception as e:
        print(f"Ollama error: {e}")
        return "Error generating comprehensive extract."

def save_extracts_to_file(extracts_data, output_filename):
    """
    Save all extracts to a text file for later reference or narration.
    """
    with open(output_filename, 'w', encoding='utf-8') as f:
        for extract in extracts_data:
            f.write(f"Title: {extract['title']}\n")
            f.write(f"URL: {extract['url']}\n")
            if extract['pub_date']:
                f.write(f"Published: {extract['pub_date']}\n")
            f.write(f"Extract:\n{extract['extract']}\n")
            f.write("=" * 80 + "\n\n")
    return output_filename

def generate_audio_from_text(text, audio_model, audio_voice, audio_speed, audio_lang_code, output_prefix):
    """
    Generate an audio narration from the full text using MLX Audio TTS.
    """
    try:
        if not MLX_AVAILABLE:
            print("❌ mlx-audio not installed - audio generation skipped")
            return False
        from mlx_audio.tts.generate import generate_audio
        print("🔊 Initializing English TTS...")
        generate_audio(
            text=text,
            model_path=audio_model,
            voice=audio_voice,
            speed=audio_speed,
            lang_code=audio_lang_code,
            file_prefix=output_prefix,
            audio_format="wav",
            sample_rate=24000,
            join_audio=True,
            verbose=False
        )
        print(f"✅ Audio generated: {output_prefix}.wav")
        return True
    except Exception as e:
        print(f"❌ Audio generation error: {e}")
        return False

def main():
    """
    Main workflow: fetch articles, extract content, generate extracts, save to file, and optionally generate audio.
    """
    args = parse_args()
    site_name = get_site_name(args.rss_url, args.site_name)
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_prefix = os.path.join(args.output_dir, f"{site_name.lower()}_extracts_{date_str}")
    text_file = output_prefix + ".txt"
    audio_file = output_prefix + ".wav"

    print(f"=== {site_name} Comprehensive Extract Generator with Audio ===\n")
    if not check_ollama_status(args.ollama_url):
        print(f"❌ Ollama is not accessible at {args.ollama_url}")
        sys.exit(1)
    print("✅ Ollama is accessible")

    print(f"🔍 Fetching the latest {args.max_articles} articles from RSS feed...")
    articles = get_latest_articles_from_rss(args.rss_url, args.max_articles)
    if not articles:
        print("❌ No articles found")
        sys.exit(1)
    print(f"✅ {len(articles)} articles found\n")

    all_extracts = []
    extracts_data = []
    for i, article in enumerate(articles, 1):
        print(f"📖 Article {i}/{len(articles)}: {article['title']}")
        print(f"🔗 URL: {article['url']}")
        if article.get('pub_date'):
            print(f"📅 Published: {article['pub_date']}")
        if article.get('description'):
            print(f"💬 Excerpt: {article['description'][:100]}...")
        
        # Extract main content from the article
        content = extract_article_content(article['url'], args.content_selector)
        if not content:
            print("❌ Unable to extract content\n")
            continue
        print(f"✅ Content extracted ({len(content)} characters)")
        print("🤖 Generating comprehensive extract...")
        
        # Generate extract using Ollama LLM
        extract = create_comprehensive_extract(content, article['title'], args.ollama_url, args.model_name)
        print("📋 Comprehensive Extract:")
        print(f"   {extract}")
        print("-" * 80)
        extract_data = {
            'title': article['title'],
            'url': article['url'],
            'pub_date': article.get('pub_date', ''),
            'extract': extract
        }
        extracts_data.append(extract_data)
        intro = f"Article {i}: {article['title']}. "
        all_extracts.append(intro + extract)
        if i < len(articles):
            time.sleep(3)  # Brief pause between articles to avoid rate limits

    print(f"\n✨ Generated {len(extracts_data)} comprehensive extracts!")
    save_extracts_to_file(extracts_data, text_file)

    if all_extracts:
        print("\n🎵 Preparing audio generation...")
        intro_text = f"Welcome to {site_name} comprehensive extracts. Here are {len(all_extracts)} recent articles from {site_name}, generated on {date_str}. "
        full_text = intro_text + " ".join(all_extracts)
        
        # Estimate audio duration based on word count and average narration speed
        word_count = len(full_text.split())
        duration_minutes = word_count / 150  # 150 words per minute is a typical narration speed
        print(f"📝 Total text length: {len(full_text)} characters ({word_count} words)")
        print(f"🕐 Estimated audio duration: ~{duration_minutes:.1f} minutes")

        # Generate audio file
        audio_success = generate_audio_from_text(
            full_text,
            args.audio_model,
            args.audio_voice,
            args.audio_speed,
            args.audio_lang_code,
            output_prefix
        )
        if audio_success:
            print(f"✅ Audio generation completed! ({audio_file})")
        else:
            print("⚠️  Audio generation failed, but text file is available")
    print(f"\n📁 Files generated:")
    print(f"   - Text extracts: {text_file}")
    print(f"   - Audio: {audio_file}")
    print("\n🎉 Processing completed!")

if __name__ == "__main__":
    main()
