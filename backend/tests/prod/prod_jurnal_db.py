# -*- coding: utf-8 -*-
"""Production bazasi (faqat o'qish): yangi jadvallar bormi, jurnalga yozuv tushyaptimi. Maxfiy ma'lumot chiqarilmaydi."""
import json

import psycopg2
import psycopg2.extras

cfg = json.load(open(r'C:\Users\ADMIN\Desktop\BilimSari-zaxira\supabase-baza.json', encoding='utf-8'))
conn = psycopg2.connect(cfg['database_url'], connect_timeout=15)
conn.set_session(readonly=True)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
for t in ('chaqmoq_log', 'marathons', 'marathon_participants', 'game_chances', 'game_chance_state'):
    cur.execute(f'SELECT COUNT(*) AS n FROM {t}')
    print(t, cur.fetchone()['n'])
cur.execute('SELECT source, COUNT(*) AS n, MAX(created_ms) AS last FROM chaqmoq_log GROUP BY source')
print('jurnal manbalari:', [(r['source'], r['n']) for r in cur.fetchall()])
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'broadcasts' AND column_name IN ('html', 'everyone', 'button_text')")
print('broadcasts yangi ustunlar:', sorted(r['column_name'] for r in cur.fetchall()))
conn.close()
