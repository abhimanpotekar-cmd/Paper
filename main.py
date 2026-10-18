
import json
from pathlib import Path
from convertor.pipeline import interpretation
from settings import INITIAL_PAPER_PATH , OUTPUT_DIRECTORY_PATH
# This is a sample Python script.

# Press Ctrl+F5 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

def main(initial_source:str,output_source:str)->None:
    resultant_tuple =interpretation(initial_source)

    json_result = {
        "Paper Interpretation":resultant_tuple[0].model_dump(mode="json"),
        "Source Paper":resultant_tuple[-1].model_dump(mode="json"),
    }
    output_dir_path = Path(f"{output_source}/json_result")
    file_path = output_dir_path/"resultant.json"
    # Create the directory if it doesn't already exist
    output_dir_path.mkdir(parents=True, exist_ok=True)
    with open(file_path,"w",encoding="utf-8") as f:
        json.dump(json_result,f,indent=4)
    print(f"Success file stored in {file_path}")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # print_hi('PyCharm')
    main(INITIAL_PAPER_PATH,OUTPUT_DIRECTORY_PATH)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
