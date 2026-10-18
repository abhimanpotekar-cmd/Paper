from settings import MODEL_NAME,MAX_MODEL_ENTRIES
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()
# MAX_MODEL_ENTRIES is used / interpretted for now as MAX_MODEL_RETRIES
llm=ChatGoogleGenerativeAI(model=MODEL_NAME,max_retries=MAX_MODEL_ENTRIES)