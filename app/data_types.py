from typing import TypedDict, Dict, Any, List, Tuple
import pandas as pd

class SheetState(TypedDict):
    sheet_name: str
    summary: Dict[str, Any]
    profile: Dict[str, Any]
    df: pd.DataFrame
    insights: str
    visuals: Dict[str, Dict[str, Any]]
    pdf_path: str
    images_with_descriptions: List[Tuple[str, str]]


class DataProfileState(TypedDict):
    filepath: str
    sheets: List[SheetState]
