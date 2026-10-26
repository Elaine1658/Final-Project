from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .agents import build_plan

ROOT = Path(__file__).resolve().parents[1]
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
    return {'ok': True, 'mode': 'offline deterministic demo'}

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
