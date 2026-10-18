
from convertor.schemas import SourcePaper,PaperInterpretation
from settings import INITIAL_PAPER_PATH
from dotenv import load_dotenv
from convertor.documetns import read_paper
from typing import Tuple

from convertor.llm import llm ,interpret_paper

def interpretation(input_path:str)->Tuple[PaperInterpretation,SourcePaper]:
    paper:SourcePaper =read_paper(
        input_path,
    )
    result:PaperInterpretation=interpret_paper(paper)

    return (result,paper)

if __name__ == "__main__":
    print("Initializing paper interpretation...")
    papers=interpretation(INITIAL_PAPER_PATH)

    print(papers[-1],"\n\n\n\n",papers[0])

