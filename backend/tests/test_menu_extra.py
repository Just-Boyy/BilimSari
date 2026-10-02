# -*- coding: utf-8 -*-
"""Menyu (/api/menu) va "Biz haqimizda" kanal havolasi — test_partners.py muhitida ishlaydi."""
exec(open(__file__.replace('test_menu_extra.py', 'test_partners.py'), encoding='utf-8').read())  # noqa: S102 — o'z test faylimiz

fails.clear()
print('\n=== 11) Menyu va kanal havolasi ===')
r = c.get('/api/menu', headers=ali['h']).get_json()
check("Hamkor uchun menyu: partner=True, kanal hali yo'q", r['ok'] and r['partner'] is True and r['channel_url'] is None, r)
check("Oddiy o'quvchi: partner=False", c.get('/api/menu', headers=s1['h']).get_json()['partner'] is False)
check('Kirmagan — 401', c.get('/api/menu').status_code == 401)
for raw, want in (('@bilimsari_uz', 'https://t.me/bilimsari_uz'), ('t.me/bilimsari_uz', 'https://t.me/bilimsari_uz'),
                  ('https://t.me/bilimsari_uz/', 'https://t.me/bilimsari_uz'),
                  ('https://t.me/+AbCdEf123456', 'https://t.me/+AbCdEf123456')):
    r = c.post('/api/admin/channel', headers=ADM, json={'url': raw}).get_json()
    check(f'Kanal: {raw} → {want}', r.get('channel_url') == want, r)
for bad in ('https://evil.com/x', 'javascript:alert(1)', '@ab', 'https://t.me/bad name'):
    r = c.post('/api/admin/channel', headers=ADM, json={'url': bad})
    check(f"Noto'g'ri havola rad: {bad}", r.status_code == 400, r.get_json())
c.post('/api/admin/channel', headers=ADM, json={'url': '@bilimsari_uz'})
check('Menyuda kanal havolasi', c.get('/api/menu', headers=s1['h']).get_json()['channel_url'] == 'https://t.me/bilimsari_uz')
check("Tizim bo'limida ko'rinadi", c.get('/api/admin/system', headers=ADM).get_json()['channel_url'] == 'https://t.me/bilimsari_uz')
r = c.post('/api/admin/channel', headers=ADM, json={'url': ''}).get_json()
check("Bo'sh — o'chiriladi", r['ok'] and r['channel_url'] == ''
      and c.get('/api/menu', headers=s1['h']).get_json()['channel_url'] is None)
check('Himoyalangan', c.post('/api/admin/channel', json={'url': '@x_kanal'}).status_code == 401)
CALLS.clear()
buy(mk('Oxirgi', 81011), ['history'], 'ALI20')
btn = [p for m, p in CALLS if m == 'sendMessage' and p.get('chat_id') == 81001]
check('Hamkor xabari tugmasi hamkor.html ga olib boradi', btn and 'hamkor.html' in str(btn[-1].get('reply_markup')), btn[-1:])
r = c.get('/hamkor.html')
check('hamkor.html sahifasi beriladi', r.status_code == 200 and b'Hamkorlik' in r.data)

print('\n' + ('MENYU: HAMMASI OK' if not fails else f'MENYU: {len(fails)} ta XATO: {fails}'))
