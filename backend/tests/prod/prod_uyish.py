# -*- coding: utf-8 -*-
"""Production: uyga vazifada xato javob → to'g'ri javob qaytadimi (sinov o'quvchisi yaratilib, o'chiriladi)."""
import json
import os

import psycopg2
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prod  # noqa: E402
from psycopg2.extras import RealDictCursor

B = 'https://backend-production-ec58b.up.railway.app'
DB = json.load(open(r'C:\Users\ADMIN\Desktop\BilimSari-zaxira\supabase-baza.json'))['database_url']

at = requests.post(B + '/api/admin/login', json={'password': os.environ['ADMIN_PW']}, timeout=30).json()['token']
H = {'Authorization': 'Bearer ' + at}
g = requests.post(B + '/api/guest', headers=_prod.admin_headers(), json={'name': 'Uy ishi Sinov'}, timeout=30).json()
tok, uid = g['token'], g['user']['id']
h = {'Authorization': 'Bearer ' + tok}
try:
    requests.post(B + '/api/study/subjects/math/choose', headers=h, timeout=30)
    conn = psycopg2.connect(DB, cursor_factory=RealDictCursor, connect_timeout=15)
    cur = conn.cursor()
    cur.execute("SELECT grade, slug, homework FROM topics WHERE subject_key = 'math' AND homework::text LIKE '%%answer%%' "
                "ORDER BY grade, seq LIMIT 1")
    t = cur.fetchone()
    conn.close()
    hw = t['homework'] if isinstance(t['homework'], dict) else json.loads(t['homework'])
    bad = {x['id']: 'xxxxx' for x in hw.get('tasks', [])}
    r = requests.post(B + '/api/study/homework', headers=h, timeout=30,
                      json={'grade': t['grade'], 'subject_key': 'math', 'slug': t['slug'], 'answers': bad})
    d = r.json()
    checked = [x for x in d.get('results', []) if x.get('checked')]
    print('status', r.status_code, '| tekshiriladigan vazifalar:', len(checked),
          "| hammasida to'g'ri javob qaytdi:", bool(checked) and all(x.get('correct_answer') for x in checked))
    if not checked:
        print('javob:', json.dumps(d, ensure_ascii=False)[:300])
    js = requests.get(B + '/topic.html', timeout=30).text
    print("topic.html: \"To'g'ri javob\" qatori bor:", "To\\'g\\'ri javob: ' + UI.esc(r.correct_answer)" in js)
finally:
    print("sinov o'quvchisi o'chirildi:", requests.delete(B + f'/api/admin/users/{uid}', headers=H, timeout=30).status_code)
