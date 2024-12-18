import re
from collections import Counter
import textstat
import nltk
from rake_nltk import Rake

# Download required NLTK data silently if not present
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

# Set of stopwords to be filtered out from the frequency count
STOP_WORDS = set(nltk.corpus.stopwords.words('russian')).union({
    "в", "на", "к", "по", "с", "для", "и", "или", "от", "из", "за", "о", "об",
    "что", "не", "это", "но", "так", "же", "как", "когда", "если", "где", "кто",
    "можно", "только", "будет", "при", "из-за", "потому", "тогда", "во", "бы",
    "там", "сразу", "пока", "ли", "чтобы", "сейчас", "ещё", "между", "даже",
    "может", "после", "перед", "при", "тут", "да"
})

async def analyze_text(text: str) -> str:
    """
    Analyze the given text by:
    - Counting words and characters
    - Estimating reading time
    - Finding top-5 most common words (excluding stopwords)
    - Calculating reading difficulty via Flesch Reading Ease
    - Determining education level required
    - Extracting top key phrases via RAKE

    Returns a formatted summary string.
    """
    word_count = len(text.split())
    char_count = len(text)
    estimated_time_seconds = round(len(text) / 150)
    estimated_time_minutes = estimated_time_seconds // 60
    estimated_time_remainder_seconds = estimated_time_seconds % 60

    estimated_time_str = ""
    if estimated_time_minutes > 0:
        estimated_time_str += f"{estimated_time_minutes} min "
    if estimated_time_remainder_seconds > 0 or estimated_time_minutes == 0:
        estimated_time_str += f"{estimated_time_remainder_seconds} sec"

    # Find top words excluding stopwords
    words = re.findall(r'\b\w+\b', text.lower())
    filtered_words = [word for word in words if word not in STOP_WORDS]
    common_words = Counter(filtered_words).most_common(5)

    # Reading difficulty and grade level
    reading_ease = textstat.flesch_reading_ease(text)
    grade_level = textstat.text_standard(text, float_output=False)

    # Interpret reading ease
    if reading_ease > 80:
        reading_level = "Very easy to read"
    elif reading_ease > 60:
        reading_level = "Easy to read"
    elif reading_ease > 40:
        reading_level = "Moderately difficult"
    elif reading_ease > 20:
        reading_level = "Hard to read"
    else:
        reading_level = "Very hard to read"

    # Key phrases extraction using RAKE
    rake = Rake()
    rake.extract_keywords_from_text(text)
    key_phrases = rake.get_ranked_phrases()[:5]

    # Compile the summary
    summary_of_the_text = (
        f"📝 Your text contains {word_count} words and {char_count} characters.\n"
        f"⏳ Approximate narration time: {estimated_time_str}.\n\n"
        f"📊 <b>Text Analysis</b>:\n\n"
        f"- <b>Top-5 words</b>: {', '.join([f'{w} ({c})' for w, c in common_words])}\n"
        f"- <b>Reading level</b>: {reading_level} (Flesch: {reading_ease:.2f})\n"
        f"- <b>Suggested education level</b>: {grade_level}\n\n"
        f"- <b>Key phrases</b>: {', '.join(key_phrases)}\n"
    )

    return summary_of_the_text
