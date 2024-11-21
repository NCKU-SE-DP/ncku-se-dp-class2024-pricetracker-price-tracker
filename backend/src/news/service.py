from .prompt import EXTRACT_KEYWORDS_PROMPT, GENERATE_SUMMARY_PROMPT
from .utils import generate_ai_response

def extract_search_keywords(content):
    return generate_ai_response(content, EXTRACT_KEYWORDS_PROMPT)

def generate_summary(content):
    return generate_ai_response(content, GENERATE_SUMMARY_PROMPT)