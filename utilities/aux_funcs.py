import os
import pandas as pd
from typing import Optional

def split_pipe_column(x):
    if isinstance(x, str):
        parts = [p.strip() for p in x.split("|")]
        return [p for p in parts if p != ""]
    return []