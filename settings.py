from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INITIAL_PAPER_PATH = BASE_DIR / "inputs" / "paper.docx"
TEMPLATE_PATH = BASE_DIR / "templates" / "template.docx"
TEMPLATE_RULES_PATH = BASE_DIR / "templates" / "rules.json"
OUTPUT_DIRECTORY_PATH = BASE_DIR / "outputs"

MODEL_NAME = "gemini-3.5-flash-lite"

LANGUAGE_POLISHING = False
ADDITIONAL_DIAGRAMS = False

MAX_EDITING_PASSES = 5
MAX_MODEL_ENTRIES = 6