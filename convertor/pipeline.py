
from convertor.schemas import SourcePaper,PaperInterpretation,TemplateInterpretation
from settings import INITIAL_PAPER_PATH , TEMPLATE_RULES_PATH,TEMPLATE_PATH

from convertor.documetns import read_paper

from typing import Tuple

from convertor.llm import llm ,interpret_paper ,  interpret_template , serializing_json

def interpretation(input_path:str)->Tuple[PaperInterpretation,SourcePaper]:
    paper:SourcePaper =read_paper(
        input_path,
    )
    result:PaperInterpretation=interpret_paper(paper)

    return (result,paper)
def template_interpreter(template_path:str,template_rules_path:str)->TemplateInterpretation:
    interpreted = interpret_template(template_path)
    serializing_json(interpreted,template_rules_path)
    print("Template rules generated and saved")
    return interpreted

if __name__ == "__main__":
    print("Initializing paper interpretation...")
    papers=interpretation(INITIAL_PAPER_PATH)
    template_rule = template_interpreter(TEMPLATE_PATH,TEMPLATE_RULES_PATH)


    # print(papers[-1],"\n\n\n\n",papers[0])




