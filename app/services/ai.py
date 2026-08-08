import re
from ..config import settings
from ..profile import PROFILE
def language(t):
 t=t.lower()
 if re.search('[а-яё]',t):return 'ru'
 if any(x in t for x in ['salom','rahmat','siz','men','ishlayman','loyiha']):return 'uz'
 return 'en'
def approval_required(t):return any(x in t.lower() for x in ['salary','compensation','payment','contract','legal','passport','bank','tax','test task','assessment','interview time','maosh','shartnoma','tolov','to‘lov','pasport','bank','intervyu','sinov'])
async def gemini(prompt):
 if not settings.gemini_api_key:return ''
 try:
  from google import genai;c=genai.Client(api_key=settings.gemini_api_key);r=c.models.generate_content(model=settings.gemini_model,contents=prompt);return (r.text or '').strip()
 except:return ''
async def cover(job):
 p=f"Write a concise professional application for {job['title']} at {job['company']}. Use ONLY these verified facts: {PROFILE}. Portfolio: {PROFILE['portfolio']}. Never invent years, salary, degree or certification. Job description: {job['description'][:12000]}"
 return await gemini(p) or f"Hello {job['company']} team,\n\nI’m interested in the {job['title']} role. My verified background includes Python/FastAPI, API integrations, Telegram bots, automation, web platforms, AI media production and prompt engineering. Portfolio: {PROFILE['portfolio']}\n\nBest regards,\nAziz Asadov"
async def reply(text,context=''):
 lang=language(text); req=approval_required(text);p=f"Reply naturally and professionally in {lang}. Use only verified facts from this profile: {PROFILE}. Do not invent anything. Incoming: {text}. Context: {context}. If sensitive decision is needed, say owner confirmation is required."
 out=await gemini(p)
 if not out:out={'uz':f"Salom, xabaringiz uchun rahmat. Loyiha tafsilotlarini ko‘rib chiqishga tayyorman. Portfolio: {PROFILE['portfolio']}",'ru':f"Здравствуйте, спасибо за сообщение. Готов обсудить проект и задачи. Портфолио: {PROFILE['portfolio']}",'en':f"Hello, thank you for reaching out. I’d be happy to discuss the project and requirements. Portfolio: {PROFILE['portfolio']}"}[lang]
 return {'language':lang,'text':out,'approval_required':req}
