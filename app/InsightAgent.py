from typing import List
from app.data_types import DataProfileState, SheetState
from app.llm_client import client

def generate_insights(state: DataProfileState) -> DataProfileState:

    # Prepare prompt content
    updated_sheets:List[SheetState] = []
    for sheet in state["sheets"]:
        
        sheet_name = sheet["sheet_name"]
        summary = sheet["summary"]
        profile = sheet["profile"]


        system_prompt = {
            "role": "system",
            "content": """
            You are a business insights agent. Your role is to generate clear, actionable, and relevant textual insights based on structured data.

            You have been provided with two key inputs:

            A basic summary of an Excel file, including row/column counts, data types, missing values, unique values, and sample entries.
            A data profile description, which includes detailed statistical and structural metadata about the Excel file.

            Your task is to analyze this information and generate at most 9 applicable business insights that can be inferred from the data.
            These insights should reflect patterns, anomalies, opportunities, risks, or strategic observations that would be useful to a business decision-maker.

            Each insight must be having strictly this format for every Insight everytime:
            Insight 1:
            Insight: 
            Takeaway:    
            Visualization Suggestion:
            ---
            Insight 2:
            Insight: 
            Takeaway:    
            Visualization Suggestion:

            Also keep in mind that: 
            Insight should Grounded in the data, Clearly stated and context-aware
            Takeaway must be Framed as a meaningful takeaway
            Visualization Suggestion means that each insight should be expressed in a way that allows a graph, chart, or dashboard element to be created from it later (e.g., trends, comparisons, distributions, correlations, rankings, outliers).

            Avoid generic statements. Focus on clarity, relevance, and impact.
            """
        }

        user_prompt = {
            "role": "user",
            "content": f"Sheet:{sheet_name}\n Summary:{summary}\n Profile:{profile}"
        }

        response = client.chat.completions.create(
            messages=[system_prompt, user_prompt],
            max_tokens=4096,
            temperature=1.0,
            top_p=1.0,
            model="gpt-4o"
        )

        sheet['insights'] = response.choices[0].message.content
        updated_sheets.append(sheet)
    
    state["sheets"] = updated_sheets
    print("InsightAgent is done")    
    return state