from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
from typing import List
from langgraph.graph import StateGraph, START, END
from app.DataProfileAgent import get_data_profile
from app.InsightAgent import generate_insights
from app.PlotSuggestionAgent import suggest_plots
from app.PDFAgent import make_pdf_report
from app.data_types import DataProfileState

# Define base paths
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
REPORT_DIR = os.path.join(BASE_DIR, "generated_reports")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse(content="Frontend not found", status_code=404)

# LangGraph workflow
graph = StateGraph(DataProfileState)
graph.add_node('get_data_profile', get_data_profile)
graph.add_node('get_textual_insights', generate_insights)
graph.add_node('get_visualization_code', suggest_plots)
graph.add_node('get_pdf_report', make_pdf_report)

graph.add_edge(START, 'get_data_profile')
graph.add_edge('get_data_profile', 'get_textual_insights')
graph.add_edge('get_textual_insights', 'get_visualization_code')
graph.add_edge('get_visualization_code', 'get_pdf_report')
graph.add_edge('get_pdf_report', END)

workflow = graph.compile()

# Upload endpoint
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        return JSONResponse(content={"error": "Invalid file type"}, status_code=400)

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return JSONResponse(content={"error": f"File upload failed: {e}"}, status_code=500)

    try:
        initial_state = {"filepath": file_path}
        final_state = workflow.invoke(initial_state)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": f"Workflow failed: {e}"}, status_code=500)

    pdfs: List[str] = []
    for sheet in final_state.get("sheets", []):
        pdf_name = sheet.get("pdf_path")
        pdf_path = os.path.join(REPORT_DIR, pdf_name) if pdf_name else None
        if pdf_path and os.path.exists(pdf_path):
            pdfs.append(pdf_name)

    return JSONResponse(content={"success": True, "pdfs": pdfs})

# Download endpoint
@app.get("/download/{pdf_name}")
async def download_pdf(pdf_name: str):
    pdf_path = os.path.join(REPORT_DIR, pdf_name)
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_name)
    return JSONResponse(content={"error": "File not found"}, status_code=404)

# Get history endpoint
@app.get("/history")
async def get_pdf_history():
    try:
        files = [
            f for f in os.listdir(REPORT_DIR)
            if f.endswith(".pdf") and os.path.isfile(os.path.join(REPORT_DIR, f))
        ]
        return JSONResponse(content={"pdfs": sorted(files)})
    except Exception as e:
        return JSONResponse(content={"error": f"Failed to retrieve history: {e}"}, status_code=500)
    


