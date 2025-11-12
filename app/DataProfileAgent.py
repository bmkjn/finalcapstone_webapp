from typing import List
import pandas as pd
from app.profiler import parse_excel, basic_summary, profile_to_json
from app.data_types import DataProfileState, SheetState
import secrets

def get_data_profile(state: DataProfileState) -> DataProfileState:
    filepath = state['filepath']
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath, encoding="utf-8")
        sheet_id = secrets.token_hex(8)  # Generates a shorter ID 
        sheets = {sheet_id: df}
    else:
        sheets = parse_excel(filepath)
    
    sheet_states: List[SheetState] = []
    for sheet_name, df in sheets.items():
        summary = basic_summary(df)
        profile  = profile_to_json(df)
        sheet_states.append({
            "sheet_name": sheet_name,
            "summary": summary,
            "profile": profile,
            "df": df
        })
    state['sheets'] = sheet_states
    print("DataProfileAgent is done")
    return state