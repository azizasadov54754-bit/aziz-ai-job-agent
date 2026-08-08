import base64,re
from email.message import EmailMessage
from ..config import settings
SCOPES=['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.modify','https://www.googleapis.com/auth/gmail.send']
def svc():
 from google.oauth2.credentials import Credentials
 from googleapiclient.discovery import build
 c=Credentials(None,refresh_token=settings.google_refresh_token,token_uri='https://oauth2.googleapis.com/token',client_id=settings.google_client_id,client_secret=settings.google_client_secret,scopes=SCOPES)
 return build('gmail','v1',credentials=c,cache_discovery=False)
def send(to,subject,body,thread_id=''):
 m=EmailMessage();m['To']=to;m['From']=settings.google_gmail_address;m['Subject']=subject;m.set_content(body);raw=base64.urlsafe_b64encode(m.as_bytes()).decode();p={'raw':raw}
 if thread_id:p['threadId']=thread_id
 return svc().users().messages().send(userId='me',body=p).execute()
def inbox():return svc().users().messages().list(userId='me',q='in:inbox newer_than:2d',maxResults=50).execute().get('messages',[])
def get(mid):return svc().users().messages().get(userId='me',id=mid,format='full').execute()
def hdr(m,n):return next((h['value'] for h in m.get('payload',{}).get('headers',[]) if h.get('name','').lower()==n.lower()),'')
def body(m):
 def walk(p):
  d=p.get('body',{}).get('data')
  if d:
   try:return base64.urlsafe_b64decode(d+'===').decode('utf8','ignore')
   except:pass
  return '\n'.join(walk(x) for x in p.get('parts',[]))
 return walk(m.get('payload',{}))
def email(text):
 m=re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',text or '');return m.group(0).lower() if m else ''
