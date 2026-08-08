import re
from .profile import PROFILE,TARGET_ROLES

def score_job(title,description,location='',salary=''):
 t=(title+' '+description).lower(); loc=(location or '').lower()
 if not any(x in loc for x in ['remote','worldwide','anywhere','distributed']) and loc: return 0,'','', 'not worldwide remote'
 skills=[s for s in PROFILE['skills'] if s.lower() in t]
 roles=[r for r in TARGET_ROLES if any(w in t for w in r.lower().split() if len(w)>2)]
 score=min(100,35+min(32,len(roles)*8)+min(23,len(skills)*3)+10)
 gaps=[x for x in ['python','fastapi','api','automation','telegram','javascript','frontend','backend','saas','mvp','prompt','ai'] if x in t and x not in [s.lower() for s in skills]]
 return score,', '.join((roles+skills)[:10]),', '.join(gaps[:8]),''
