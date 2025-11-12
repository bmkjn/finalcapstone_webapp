from typing import List
from app.data_types import DataProfileState, SheetState
from app.llm_client import client
import ast

def suggest_plots(state: DataProfileState) -> DataProfileState:

    updated_sheets:List[SheetState] = []
    for sheet in state['sheets']:

        user_prompt = {
            'role': 'user',
            'content': f"Business Insights: {sheet['insights']}"
        }

        df = sheet['df']
        df_columns = list(df.columns)

        system_prompt = {
            'role': 'system',
            'content': f"""
                    You are a data visualization assistant. Based on the business insights provided to you, your task is to generate at most 9 chart or plot suggestions that can help visualize those insights.

                    Your output must strictly be a JSON object structured as follows:

                    {{
                    "chart1": {{
                        "plot": "matplotlib code as a string",
                        "description": "A short explanation of what the chart reveals."
                    }},
                    "chart2": {{
                        "plot": "...",
                        "description": "..."
                    }}
                    }}

                    Requirements:
                    - Each chart must be based on a specific insight.
                    - Use diverse chart types (e.g., bar, line, pie, scatter, histogram, box plot, heatmap, etc.).
                    - The "plot" field must contain valid Python matplotlib code as a string that can be executed to generate the chart.
                    - The "description" field should briefly explain what the chart shows and why it’s useful.
                    - Use the following DataFrame: The name of the dataframe is "df"
                    - Use only the column names of the DataFrame: {df_columns}
                    - Do not invent or assume any other columns.
                    - Do not include placeholder data — assume the data is already loaded in df.
                    - Focus on clarity, variety, and relevance to the insights.
                    - Always assign the figure to a variable using fig = plt.figure() and plot on that figure. Do not rely on implicit figure creation.
                    """
                        }
        response = client.chat.completions.create(
            messages=[system_prompt, user_prompt],
            max_tokens=4096,
            temperature=0,
            top_p=1.0,
            model="gpt-4o"
        )
        raw = response.choices[0].message.content

        # So that markdown blockers are removed
        if raw.startswith("```json"):
            raw = raw[len("```json"):].strip()
        if raw.endswith("```"):
            raw = raw[:-len("```")].strip()

        # this will make this a dict 
        sheet['visuals']= ast.literal_eval(raw)
        updated_sheets.append(sheet)

    state["sheets"] = updated_sheets
    print("PlotSuggestionAgent is done") 
    return state