import asyncio
import os
from utils.text_to_speech import detect_language, sanitize_filename, synthesize_chunk, VOICE_MAP
from config import AUDIO_FOLDER
import requests
import json
from collections import defaultdict
from bs4 import BeautifulSoup

def download_image(url, save_path, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Image saved to: {save_path}")
        return True
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        return False

def extract_text_from_dict(content_dict):
    """Recursively extract text from a JSON content dictionary."""
    if isinstance(content_dict, dict):
        if content_dict.get("type") == "text":
            return content_dict.get("text", "")
        elif "content" in content_dict:
            return "\n".join(extract_text_from_dict(item) for item in content_dict["content"] if extract_text_from_dict(item))
    elif isinstance(content_dict, list):
        return "\n".join(extract_text_from_dict(item) for item in content_dict if extract_text_from_dict(item))
    return ""

def fetch_chapters_list(manga_id):
    url = f"https://api.cdnlibs.org/api/manga/{manga_id}/chapters"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"Error fetching chapters: {str(e)}")
        return []

def parse_manga_chapter(manga_id, chapter_number, volume=None, rate="+0%"):
    base_url = f"https://api.cdnlibs.org/api/manga/{manga_id}/chapter"
    params = {"number": chapter_number}
    if volume:
        params["volume"] = volume

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        chapter_data = response.json()["data"]

        # Get content and handle different types
        content = chapter_data.get("content", "")
        if not content:  # Handle empty content
            print(f"Empty content for chapter {chapter_number}")
            return None

        if isinstance(content, dict):
            # Extract text from JSON dictionary
            chapter_text = extract_text_from_dict(content)
        else:
            # Parse HTML string
            soup = BeautifulSoup(content, 'html.parser')
            paragraphs = soup.find_all('p')
            chapter_text = "\n\n".join(p.get_text(separator="\n", strip=True) for p in paragraphs)

        audio_dir = os.path.join(AUDIO_FOLDER, manga_id)
        os.makedirs(audio_dir, exist_ok=True)

        filename_base = f"{chapter_data.get('volume', '')}.{chapter_data['number']}_{sanitize_filename(chapter_data['name'])}"

        # Always process attachments regardless of text presence
        attachments = chapter_data.get("attachments", [])
        image_paths = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "ru,en;q=0.9,ko;q=0.8",
        }
        for i, attachment in enumerate(attachments):
            image_url = "https://ranobelib.me" + attachment["url"]
            image_extension = attachment["extension"]
            image_filename = f"{filename_base}_photo_{i + 1}.{image_extension}"
            image_path = os.path.join(audio_dir, image_filename)
            if not os.path.exists(image_path):
                if download_image(image_url, image_path, headers):
                    image_paths.append(image_path)
                else:
                    print(f"Failed to download image {i + 1} for chapter {chapter_data['number']}")
            else:
                print(f"Image already exists: {image_path}")
                image_paths.append(image_path)

        # Добавляем информацию о количестве иллюстраций в конце текста, если есть вложения
        if attachments and chapter_text.strip():
            chapter_text = chapter_text.strip() + f"\n\nВ главе {len(attachments)} илюстраций"

        # Handle text and audio if text is present
        if chapter_text.strip():

            mp3_path = os.path.join(audio_dir, f"{filename_base}.mp3")
            if not os.path.exists(mp3_path):
                lang = detect_language(chapter_text)
                voice = VOICE_MAP.get(lang, "ru-RU-DmitryNeural")
                asyncio.run(synthesize_chunk(
                    text=chapter_text,
                    mp3_path=mp3_path,
                    voice=voice,
                    rate=rate
                ))
                print(f"Audio created: {mp3_path}")
            else:
                print(f"Audio already exists: {mp3_path}")
            return {
                "title": chapter_data["name"],
                "content": chapter_text,
                "chapter_number": chapter_data["number"],
                "volume": chapter_data.get("volume"),
                "audio_path": mp3_path,
                "image_paths": image_paths if image_paths else None
            }
        else:
            if image_paths:
                return {
                    "title": chapter_data["name"],
                    "content": None,
                    "chapter_number": chapter_data["number"],
                    "volume": chapter_data.get("volume"),
                    "image_paths": image_paths
                }
            else:
                print(f"No text or images found for chapter {chapter_data['number']}")
                return None

    except Exception as e:
        print(f"Error processing chapter {chapter_number}: {str(e)}")
        return None

def display_chapters_by_volume(chapters):
    volumes = defaultdict(list)
    for ch in chapters:
        vol = ch.get("volume", "0")  # Исправление сортировки томов
        volumes[vol].append(ch)

    sorted_volumes = sorted(volumes.keys(), key=lambda x: float(x) if x.replace('.', '', 1).isdigit() else 0)
    chapters_list = []

    for vol in sorted_volumes:
        ch_list = sorted(volumes[vol], key=lambda x:
        tuple(map(int, x["number"].split('.'))) if x["number"].replace('.', '', 1).isdigit() else (0,))
        chapters_list.extend(ch_list)

    print("\nAvailable chapters:")
    for idx, ch in enumerate(chapters_list, 1):
        print(f"{idx:3}) Vol. {ch.get('volume', '?')} Ch. {ch['number']}: {ch['name']}")

    return chapters_list

def parse_range_input(input_str, max_index):
    selected = []
    for part in input_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            try:
                start = int(start)
                end = int(end)
                selected.extend(range(start, end + 1))
            except ValueError:
                print(f"Invalid range: {part}")
                return []
        else:
            if part.isdigit():
                selected.append(int(part))
            else:
                print(f"Invalid number: {part}")
                return []

    # Фильтрация и преобразование
    valid = [x for x in selected if 1 <= x <= max_index]
    return list(set(valid))  # Убираем дубликаты

def main():
    rate = "+50%"

    # manga_id = "19241--wang-guo-xue-mai"
    manga_id = "6709--youkoso-jitsuryoku-shijou-shugi-no-kyoushitsu-e-novel"
    chapters = fetch_chapters_list(manga_id)

    if not chapters:
        print("No chapters found")
        return

    sorted_chapters = display_chapters_by_volume(chapters)
    if not sorted_chapters:
        print("No valid chapters to process")
        return

    selection = input("\nEnter chapter numbers/ranges (e.g., 1-5,7): ").strip()
    selected_indices = parse_range_input(selection, len(sorted_chapters))

    if not selected_indices:
        print("Invalid selection. Exiting.")
        return

    selected = [sorted_chapters[i - 1] for i in selected_indices]

    for ch in selected:
        print(f"\nProcessing: Vol. {ch.get('volume')} Ch. {ch['number']} - {ch['name']} with speed {rate}")
        chapter_data = parse_manga_chapter(
            manga_id,
            ch['number'],
            ch.get('volume'),
            rate
        )

        if chapter_data:
            if 'audio_path' in chapter_data:
                print(f"✅ Audio saved to: {chapter_data['audio_path']}")
            if 'image_paths' in chapter_data and chapter_data['image_paths']:
                for img_path in chapter_data['image_paths']:
                    print(f"✅ Image saved to: {img_path}")
            else:
                print("Chapter processed, but no audio or images saved.")

if __name__ == "__main__":
    main()