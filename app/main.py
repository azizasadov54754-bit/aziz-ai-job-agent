import asyncio,secrets
from contextlib import asynccontextmanager
from datetime import datetime,timezone
from fastapi import FastAPI,Depends,HTTPException,Form
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic,HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select,func,desc
from sqlalchemy.ext.asyncio import AsyncSession
from .config import settings
from .db import init_db,get_db,SessionLocal
from .models import Job,Application,Message,ProfileFact,AuditEvent
from .profile import PROFILE
from .services.scheduler import scheduler,discover
from .services.ai import cover
from .services.apply import make,send_application
security=HTTPBasic()
def auth(c:HTTPBasicCredentials=Depends(security)):
 if not(secrets.compare_digest(c.username,settings.admin_username) and secrets.compare_digest(c.password,settings.admin_password)):raise HTTPException(401,'Unauthorized',headers={'WWW-Authenticate':'Basic'})
async def seed(db):
 if await db.scalar(select(ProfileFact.id).limit(1)):return
 for cat,vals in [('skill',PROFILE['skills']),('experience',PROFILE['experience']),('project',PROFILE['projects']),('claim',PROFILE['verified_claims'])]:
  for v in vals:db.add(ProfileFact(category=cat,fact=v,state='verified'))
 await db.commit()
@asynccontextmanager
async def lifespan(app):
 await init_db()
 async with SessionLocal() as db:await seed(db)
 scheduler.start()
 if settings.telegram_bot_token:asyncio.create_task(__import__('app.bot',fromlist=['run_bot']).run_bot())
 yield
 scheduler.shutdown(wait=False)
app=FastAPI(title='Aziz AI Job Agent',version='3.0',lifespan=lifespan)
app.mount('/static',StaticFiles(directory='app/static'),name='static')
@app.get('/health')
async def health():return {'status':'ok','env':settings.app_env,'scheduler':scheduler.running,'time':datetime.now(timezone.utc).isoformat()}
@app.get('/',response_class=HTMLResponse)
async def index():return open('app/static/index.html',encoding='utf8').read()
@app.get('/api/dashboard',dependencies=[Depends(auth)])
async def dashboard(db:AsyncSession=Depends(get_db)):
 return {'jobs':await db.scalar(func.count(Job.id)) or 0,'applications':await db.scalar(func.count(Application.id)) or 0,'sent':await db.scalar(func.count(Application.id).filter(Application.status=='sent')) or 0,'replies':await db.scalar(func.count(Message.id).filter(Message.direction=='inbound')) or 0,'approval':await db.scalar(func.count(Application.id).filter(Application.status=='queued')) or 0,'scheduler':scheduler.running}
@app.get('/api/jobs',dependencies=[Depends(auth)])
async def jobs(limit:int=50,min_score:int=0,db:AsyncSession=Depends(get_db)):
 rows=(await db.scalars(select(Job).where(Job.score>=min_score).order_by(desc(Job.score),desc(Job.published_at)).limit(min(limit,100)))).all()
 return [{k:getattr(j,k) for k in ['id','title','company','location','salary','source','url','apply_url','score','strengths','gaps','risk','recruiter_email','recruiter_verified','status']} for j in rows]
@app.post('/api/discovery',dependencies=[Depends(auth)])
async def manual_discovery():asyncio.create_task(discover());return {'ok':True,'message':'Live discovery started'}
@app.post('/api/jobs/{job_id}/apply',dependencies=[Depends(auth)])
async def apply(job_id:int,mode:str=Form('draft'),db:AsyncSession=Depends(get_db)):
 job=await db.get(Job,job_id)
 if not job:raise HTTPException(404,'Job not found')
 letter=await cover({'title':job.title,'company':job.company,'description':job.description});cv=f"{PROFILE['name']} — {PROFILE['headline']}\nSkills: {', '.join(PROFILE['skills'])}\nPortfolio: {PROFILE['portfolio']}";a=await make(db,job,cv,letter,mode)
 if mode=='auto' and a.status=='queued' and job.score>=85 and job.recruiter_verified:
  try:await send_application(db,job,a)
  except Exception as e:db.add(AuditEvent(event='apply_error',details=str(e)))
 await db.commit();return {'id':a.id,'status':a.status,'recipient':a.recipient}
@app.get('/api/applications',dependencies=[Depends(auth)])
async def apps(db:AsyncSession=Depends(get_db)):
 rows=(await db.scalars(select(Application).order_by(desc(Application.created_at)).limit(200))).all();return [{k:getattr(x,k) for k in ['id','job_id','mode','status','recipient','subject','sent_at','created_at']} for x in rows]
@app.get('/api/messages',dependencies=[Depends(auth)])
async def messages(db:AsyncSession=Depends(get_db)):
 rows=(await db.scalars(select(Message).order_by(desc(Message.created_at)).limit(200))).all();return [{k:getattr(x,k) for k in ['id','thread_id','direction','sender','subject','language','body','approval_required','created_at']} for x in rows]
@app.get('/api/profile',dependencies=[Depends(auth)])
async def profile(db:AsyncSession=Depends(get_db)):
 rows=(await db.scalars(select(ProfileFact).order_by(ProfileFact.category))).all();return {'name':PROFILE['name'],'portfolio':PROFILE['portfolio'],'facts':[{k:getattr(x,k) for k in ['id','category','fact','state']} for x in rows]}
@app.get('/api/audit',dependencies=[Depends(auth)])
async def audit(db:AsyncSession=Depends(get_db)):
 rows=(await db.scalars(select(AuditEvent).order_by(desc(AuditEvent.created_at)).limit(200))).all();return [{k:getattr(x,k) for k in ['id','event','details','created_at']} for x in rows]
@app.post('/api/pause',dependencies=[Depends(auth)])
async def pause():scheduler.pause();return {'ok':True}
@app.post('/api/resume',dependencies=[Depends(auth)])
async def resume():scheduler.resume();return {'ok':True}
