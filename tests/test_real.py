from app.scoring import score_job

def test_worldwide_remote_match():
    s,*_=score_job("AI Automation Engineer","Python FastAPI Telegram API automation","Worldwide Remote")
    assert s >= 70

def test_non_remote_is_rejected():
    s,*_=score_job("Python Developer","Python FastAPI","Berlin on-site")
    assert s == 0
