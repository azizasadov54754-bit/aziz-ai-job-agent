import re
from datetime import datetime,timezone,timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from ..config import settings
from ..db import SessionLocal
from ..models import Job,Application,Message,AuditEvent
from ..services.sources import collect_all
from ..services.ai import cover,reply
from ..services.apply import make,send_application
from ..profile import PROFILE
from ..services.gmail import inbox,get,hdr,body,email,send
scheduler=AsyncIOScheduler(timezone=settings.timezone)
async def discover():
 async with SessionLocal() as db:
  items=await collect_all();added=0
  for x in items[:settings.daily_discovery_limit]:
   if await db.scalar(select(Job).where(Job.external_id==x['external_id'])):continue
   j=Job(**x); emails=re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',x['description']);
   if emails:j.recruiter_email=emails[0].lower()
   # source-provided company-domain evidence is required; generic email domains are never auto-verified
   from .apply import verified_email
   j.recruiter_verified=verified_email(j.recruiter_email,j);db.add(j);await db.flush();added+=1
  jobs=(await db.scalars(select(Job).where(Job.published_at>=datetime.now(timezone.utc)-timedelta(hours=26)).order_by(Job.score.desc()).limit(settings.daily_discovery_limit))).all();sent=0
  for j in jobs:
   if j.score<50 or await db.scalar(select(Application).where(Application.job_id==j.id)):continue
   letter=await cover({'title':j.title,'company':j.company,'description':j.description});cv=f"{PROFILE['name']}\n{PROFILE['headline']}\nSkills: {', '.join(PROFILE['skills'])}\nPortfolio: {PROFILE['portfolio']}"
   mode='auto' if settings.auto_apply_enabled and sent<settings.auto_apply_daily_limit else 'approval';a=await make(db,j,cv,letter,mode)
   if mode=='auto':
    try:await send_application(db,j,a);sent+=1
    except Exception as e:a.status='queued';db.add(AuditEvent(event='auto_apply_blocked',details=str(e)))
  db.add(AuditEvent(event='daily_discovery',details=f'added={added};auto_sent={sent}'));await db.commit()
async def poll_mail():
 if not (settings.google_refresh_token and settings.google_gmail_address):return
 async with SessionLocal() as db:
  for item in inbox():
   mid=item['id']
   if await db.scalar(select(Message).where(Message.gmail_message_id==mid)):continue
   m=get(mid);frm=hdr(m,'From');sub=hdr(m,'Subject');txt=body(m)[:20000]
   if settings.google_gmail_address.lower() in frm.lower():continue
   r=await reply(txt,sub);db.add(Message(gmail_message_id=mid,thread_id=m.get('threadId',''),direction='inbound',sender=frm,subject=sub,language=r['language'],body=txt,approval_required=r['approval_required']))
   if not r['approval_required'] and settings.auto_apply_enabled:
    to=email(frm)
    if to:send(to,'Re: '+sub,r['text'],m.get('threadId',''));db.add(AuditEvent(event='auto_reply_sent',details=f'to={to};thread={m.get("threadId","")}'))
  await db.commit()
scheduler.add_job(discover,CronTrigger(hour=settings.discovery_hour,minute=settings.discovery_minute,timezone=settings.timezone),id='daily-discovery',replace_existing=True)
scheduler.add_job(poll_mail,'interval',minutes=settings.reply_poll_minutes,id='gmail-poll',replace_existing=True)
