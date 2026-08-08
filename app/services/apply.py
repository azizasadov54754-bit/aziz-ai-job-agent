from datetime import datetime,timezone
from urllib.parse import urlparse
from sqlalchemy import select
from ..models import Application,AuditEvent
from ..services.gmail import send
def verified_email(email,job):
 if not email or '@' not in email:return False
 d=email.split('@')[1].lower();blocked={'gmail.com','outlook.com','hotmail.com','yahoo.com','proton.me'}
 if d in blocked:return False
 host=urlparse(job.apply_url or job.url).netloc.lower().replace('www.','')
 return host==d or host.endswith('.'+d) or d.endswith('.'+host)
async def make(db,job,cv,letter,mode):
 a=await db.scalar(select(Application).where(Application.job_id==job.id))
 if a:return a
 recipient=job.recruiter_email if verified_email(job.recruiter_email,job) else ''
 safe=mode=='auto' and job.score>=85 and job.recruiter_verified and bool(recipient)
 if mode=='auto' and not safe:mode='approval'
 a=Application(job_id=job.id,mode=mode,status='queued' if mode!='draft' else 'draft',recipient=recipient,subject=f'Application — {job.title}',cv_text=cv,cover_letter=letter);db.add(a);await db.flush();return a
async def send_application(db,job,a):
 if not a.recipient or not job.recruiter_verified or job.score<85:raise ValueError('auto-apply gate failed')
 r=send(a.recipient,a.subject,a.cover_letter);a.status='sent';a.sent_at=datetime.now(timezone.utc);a.gmail_message_id=r.get('id','');a.gmail_thread_id=r.get('threadId','');db.add(AuditEvent(event='application_sent',details=f'job={job.id};to={a.recipient}'));return r
