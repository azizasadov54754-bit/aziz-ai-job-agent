import hashlib,json,asyncio,re
from datetime import datetime,timezone
from urllib.parse import urlparse
import httpx,feedparser
from bs4 import BeautifulSoup
from ..config import settings
from ..scoring import score_job
async def get(url,params=None):
 async with httpx.AsyncClient(timeout=settings.http_timeout_seconds,follow_redirects=True,headers={'User-Agent':'AzizAIJobAgent/2.0'}) as c:
  r=await c.get(url,params=params); r.raise_for_status(); return r

def norm(x,source):
 url=x.get('url') or x.get('apply_url') or ''; title=x.get('title') or x.get('position') or x.get('jobTitle') or ''
 if not url or not title:return None
 desc=x.get('description') or x.get('jobDescription') or x.get('jobExcerpt') or ''
 if '<' in desc:desc=BeautifulSoup(desc,'html.parser').get_text(' ',strip=True)
 loc=str(x.get('location') or x.get('jobGeo') or x.get('candidate_required_location') or 'Worldwide')
 score,strengths,gaps,risk=score_job(title,desc,loc,str(x.get('salary') or ''))
 return dict(external_id=str(x.get('id') or hashlib.sha256((source+url).encode()).hexdigest()),title=title[:400],company=str(x.get('company') or x.get('companyName') or x.get('company_name') or 'Unknown')[:300],location=loc[:500],salary=str(x.get('salary') or x.get('salaryRange') or 'Not specified')[:300],source=source,url=url[:1200],apply_url=str(x.get('apply_url') or url)[:1200],published_at=datetime.now(timezone.utc),description=desc[:30000],score=score,strengths=strengths,gaps=gaps,risk=risk,raw_json=json.dumps(x,ensure_ascii=False)[:50000])
async def remoteok():
 d=(await get('https://remoteok.com/api')).json(); out=[]
 for x in d if isinstance(d,list) else []:
  j=norm({'id':x.get('id'),'title':x.get('position'),'company':x.get('company'),'location':x.get('location') or 'Worldwide Remote','description':x.get('description'),'salary':x.get('salary'),'url':x.get('url'),'apply_url':x.get('apply_url')},'Remote OK')
  if j and j['score']>0:out.append(j)
 return out
async def remotive():
 d=(await get('https://remotive.com/api/remote-jobs',{'limit':100})).json();out=[]
 for x in d.get('jobs',[]):
  j=norm(x,'Remotive')
  if j and j['score']>0:out.append(j)
 return out
async def arbeitnow():
 out=[]
 for p in range(1,4):
  d=(await get('https://www.arbeitnow.com/api/job-board-api',{'page':p})).json()
  for x in d.get('data',[]):
   j=norm(x,'Arbeitnow')
   if j and j['score']>0:out.append(j)
 return out
async def jobicy():
 d=(await get('https://jobicy.com/api/v2/remote-jobs',{'count':100})).json();out=[]
 for x in d.get('jobs',[]):
  j=norm(x,'Jobicy')
  if j and j['score']>0:out.append(j)
 return out
async def himalayas():
 out=[]
 for off in range(0,100,20):
  d=(await get('https://himalayas.app/jobs/api',{'offset':off,'limit':20})).json();jobs=d.get('jobs',d if isinstance(d,list) else [])
  for x in jobs:
   j=norm(x,'Himalayas')
   if j and j['score']>0:out.append(j)
  if len(jobs)<20:break
 return out
async def wwr():
 r=await get('https://weworkremotely.com/remote-jobs.rss');f=feedparser.parse(r.content);out=[]
 for e in f.entries:
  j=norm({'id':getattr(e,'id',''),'title':getattr(e,'title',''),'company':getattr(e,'author','Unknown'),'location':'Worldwide Remote','description':getattr(e,'summary',''),'url':getattr(e,'link','')},'We Work Remotely')
  if j and j['score']>0:out.append(j)
 return out
async def collect_all():
 fns=[remoteok,remotive,arbeitnow,jobicy,himalayas,wwr]
 res=await asyncio.gather(*(f() for f in fns),return_exceptions=True); all=[]
 for x in res:
  if isinstance(x,list):all+=x
 seen=set();out=[]
 for j in sorted(all,key=lambda x:x['score'],reverse=True):
  k=j['url'].split('?')[0].rstrip('/')
  if k not in seen:seen.add(k);out.append(j)
 return out
