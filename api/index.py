import sys
import os

# 프로젝트 루트를 모듈 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app

# Vercel 서버리스 핸들러
app.template_folder = os.path.join(os.path.dirname(__file__), "..", "templates")
app.static_folder = os.path.join(os.path.dirname(__file__), "..", "static")
