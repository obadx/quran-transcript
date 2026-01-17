import re
import Levenshtein as lv
from typing import List, Tuple, Optional, Union, Callable


# Example usage and demonstration
if __name__ == "__main__":
    exp_text = "قاالوو"
    out_text = "كالوو"
    out_text2 = "كااالوو"

    # Compute differences between input and output
    diffs = lv.opcodes(exp_text, out_text2)
    print(diffs)
