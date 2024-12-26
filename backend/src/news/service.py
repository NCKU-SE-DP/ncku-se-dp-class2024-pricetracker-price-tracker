from .prompt import Prompt
from .utils import generate_ai_response

def extract_search_keywords(content):
    return generate_ai_response(content, Prompt.EXTRACT_KEYWORDS_PROMPT)

def generate_summary(content):
    return generate_ai_response(content, Prompt.GENERATE_SUMMARY_PROMPT)