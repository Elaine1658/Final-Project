from pathlib import Path
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from .agents import build_plan

ROOT = Path(__file__).resolve().parents[1]
# The course runner may place its shared .env beside the cloned repository.
# This repo keeps the app under AI FINAL, so cover the app folder, the clone
# root, and the folder above the clone. Earlier locations win.
for env_file in (ROOT / '.env', ROOT.parent / '.env', ROOT.parent.parent / '.env'):
    load_dotenv(env_file, override=False)
API_KEY_CONFIGURED = bool(os.getenv('PORTKEY_API_KEY') or os.getenv('OPENAI_API_KEY'))
app = FastAPI(title='Campus Dining Demand & Waste Control Tower')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
LAST = None
APPROVAL = None

class PlanRequest(BaseModel):
    weather: str | None = None
    attendance: int | None = Field(default=None, ge=0, le=10000)

class ApprovalRequest(BaseModel):
    approved_by: str = 'Dining manager'

@app.get('/')
def home():
    return FileResponse(ROOT / 'frontend' / 'index.html')

@app.get('/api/health')
def health():
    return {'ok': True, 'mode': 'offline deterministic demo', 'api_key_configured': API_KEY_CONFIGURED}

@app.post('/api/plan')
def plan(req: PlanRequest | None = None):
    global LAST, APPROVAL
    APPROVAL = None
    LAST = build_plan(req.weather if req else None, req.attendance if req else None)
    return LAST

@app.post('/api/approve-plan')
def approve_plan(req: ApprovalRequest):
    global APPROVAL
    if not LAST:
        return {'ok': False, 'message': 'Create a plan before approving it.'}
    APPROVAL = {'ok': True, 'approved_by': req.approved_by, 'status': 'approved'}
    return APPROVAL

@app.get('/api/plan')
def get_plan():
    return {**(LAST or {'status': 'not_run', 'events': [], 'rows': [], 'metrics': {}}), 'approval': APPROVAL}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8010)
