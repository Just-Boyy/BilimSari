# -*- coding: utf-8 -*-
"""
Saytni kodsiz o'zgartirish (admin panel → «Matnlar» va «Dizayn»):

  * Ilovadagi istalgan yozuv: asl matn → yangi o'zbekcha va/yoki ruscha matn. js/i18n.js har bir sahifada
    qo'llaydi (tugmalar, sarlavhalar, izohlar, xato xabarlari). Qoidalarga bog'liq matnlar
    (qoidalar.auto_texts) ham shu yerda qo'shiladi.
  * Bot matnlari: /start va /help xabarlari, bot tavsifi.
  * Dizayn: asosiy ranglar va menyu / bosh sahifa bloklarini yashirish.

O'quvchi sahifalari bularni ochiq /api/site/config dan oladi va localStorage'da saqlaydi — keyingi ochilishda
sahifa chizilishidan oldin qo'llanadi.
"""

import hashlib
import json
import re
import time

import qoidalar
from games import clock

CACHE_S = 10
MAX_TEXTS = 1000
MAX_TEXT = 2000

# ───────────────────────── Bot matnlari ─────────────────────────
# kalit: (nomi, izoh, cheklov, HTML ruxsat etiladimi)
BOT_TEXTS = {
    'start': ('/start xabari', "{ism} — o'quvchi ismi. Pastida menyu tugmalari chiqadi.", 3500, True),
    'help': ('/help xabari', 'Buyruqlar ro\'yxati va yordam.', 3500, True),
    'description': ('Bot tavsifi', "Botni birinchi ochganda «Start» tugmasidan oldin ko'rinadi (512 belgigacha).", 512, False),
    'short_description': ('Qisqa tavsif', "Bot profilida va ulashilganda ko'rinadi (120 belgigacha).", 120, False),
}
_ALLOWED_TAG = re.compile(r'</?(b|i|u|s|code|pre)>|<a href="https?://[^"<>]+">|</a>', re.I)

# ───────────────────────── Dizayn ─────────────────────────
# kalit: (nomi, CSS o'zgaruvchilari, standart)
THEME = {
    'primary': ('Asosiy rang (tugmalar, faol menyu)', ('--yashil',), '#58A700'),
    'primary_dark': ('Asosiy rangning to\'q tusi (tugma soyasi, sarlavhalar)', ('--yashil-quyuq',), '#3f7d00'),
    'accent': ("Qo'shimcha rang (havolalar, ma'lumot)", ('--kok',), '#1CB0F6'),
    'danger': ('Xato / ogohlantirish rangi', ('--qizil',), '#FF4B4B'),
    'bg': ('Sahifa foni', ('--fon',), '#f3f4f6'),
    'card': ('Kartalar foni', ('--oq',), '#ffffff'),
    'text': ('Asosiy matn rangi', ('--matn', '--matn-quyuq'), '#1f2937'),
}
_HEX = re.compile(r'^#[0-9a-fA-F]{6}$')

# Yashirish mumkin bo'lgan bloklar: kalit → (bo'lim, nomi, CSS selektor)
BLOCKS = {
    'nav.games': ('Pastki menyu', "O'yinlar", '.pastki-nav > a[href="games.html"]'),
    'nav.shaxsiy': ('Pastki menyu', 'Shaxsiy', '.pastki-nav > a[href="shaxsiy.html"]'),
    'nav.leaderboard': ('Pastki menyu', 'Reyting', '.pastki-nav > a[href="leaderboard.html"]'),
    'menu.profile': ('«Menyu» ro\'yxati', 'Profil', '#navMenyu a[href="profile.html"]'),
    'menu.shaxsiy': ('«Menyu» ro\'yxati', 'Shaxsiy darslar', '#navMenyu a[href="shaxsiy.html"]'),
    'menu.shop': ('«Menyu» ro\'yxati', "Do'kon", '#navMenyu a[href="shop.html"]'),
    'menu.kanal': ('«Menyu» ro\'yxati', 'Biz haqimizda (kanal)', '#navMenyu [data-kanal]'),
    'menu.hamkor': ('«Menyu» ro\'yxati', 'Hamkorlik', '#navMenyu a[href="hamkor.html"]'),
    'dash.daily': ('Bosh sahifa', 'Tezkor tugma: Kun savoli', '#tezkor a[href="daily.html"]'),
    'dash.games': ('Bosh sahifa', "Tezkor tugma: O'yin", '#tezkor a[href="games.html"]'),
    'dash.practice': ('Bosh sahifa', 'Tezkor tugma: Mashq', '#tezkor a[href="game.html"]'),
    'dash.leaderboard': ('Bosh sahifa', 'Tezkor tugma: Reyting', '#tezkor a[href="leaderboard.html"]'),
    'dash.kun': ('Bosh sahifa', 'Kun savoli kartasi', '#kunBo-lim'),
    'dash.reja': ('Bosh sahifa', 'Bugungi reja', '#rejaBo-lim'),
    'dash.qulf': ('Bosh sahifa', 'Yopiq fanlar (sotib olish)', '#qulfBo-lim'),
    'dash.marafon': ('Bosh sahifa', 'Marafon banneri', '#marafonBanner'),
    'dash.dost': ('Bosh sahifa', "Do'stlar chaqiruvi", '#dostChaqiruv'),
    'dash.chaqmoq': ('Bosh sahifa', 'Chaqmoq belgisi (tepada)', '#chaqmoqBelgi'),
}


class SiteError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def norm(s) -> str:
    """js/i18n.js dagi norm() bilan bir xil: tutuq belgilari va bo'shliqlar bir xillashtiriladi."""
    return ' '.join(re.sub(r'[ʻʼ‘’`´]', "'", str(s or '')).split())


def _get(cur, key, default):
    cur.execute('SELECT value FROM pay_settings WHERE key = %s', (key,))
    row = cur.fetchone()
    try:
        return json.loads(row['value']) if row and row['value'] else default
    except (TypeError, ValueError):
        return default


def _put(cur, conn, key, value):
    cur.execute('DELETE FROM pay_settings WHERE key = %s', (key,))
    if value:
        cur.execute('INSERT INTO pay_settings (key, value) VALUES (%s, %s)', (key, json.dumps(value, ensure_ascii=False)))
    cur.execute('DELETE FROM pay_settings WHERE key = %s', ('site_v',))
    cur.execute('INSERT INTO pay_settings (key, value) VALUES (%s, %s)', ('site_v', str(clock.now_ms())))
    conn.commit()
    _cache['t'] = 0.0


# ───────────────────────── Ilova matnlari ─────────────────────────

def ui_texts(cur) -> list:
    return [x for x in _get(cur, 'ui_texts', []) if isinstance(x, dict) and x.get('orig')]


def save_ui_text(cur, conn, orig, uz, ru) -> list:
    """Bitta yozuv: asl matn → yangi o'zbekcha (bo'sh — o'zgarmaydi) va ruscha (bo'sh — odatiy tarjima)."""
    orig, uz, ru = norm(orig)[:MAX_TEXT], str(uz or '').strip()[:MAX_TEXT], str(ru or '').strip()[:MAX_TEXT]
    if not orig:
        raise SiteError('Saytdagi asl matnni yozing.')
    if not uz and not ru:
        raise SiteError('Yangi o\'zbekcha yoki ruscha matnni yozing.')
    items = [x for x in ui_texts(cur) if norm(x['orig']) != orig]
    if len(items) >= MAX_TEXTS:
        raise SiteError(f"Ko'pi bilan {MAX_TEXTS} ta matn o'zgartirish mumkin.")
    items.append({'orig': orig, 'uz': uz, 'ru': ru, 'ms': clock.now_ms()})
    _put(cur, conn, 'ui_texts', items)
    return items


def delete_ui_text(cur, conn, orig) -> list:
    orig = norm(orig)
    items = [x for x in ui_texts(cur) if norm(x['orig']) != orig]
    _put(cur, conn, 'ui_texts', items)
    return items


# ───────────────────────── Bot matnlari ─────────────────────────

def _clean_bot_html(text, limit) -> str:
    text = str(text or '').replace('\r', '').strip()[:limit]
    # Faqat Telegram qabul qiladigan oddiy teglar; boshqa < belgisi oddiy matn sifatida
    out, pos = [], 0
    for m in _ALLOWED_TAG.finditer(text):
        out.append(_escape_plain(text[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_escape_plain(text[pos:]))
    html = ''.join(out)
    opened = re.findall(r'<(b|i|u|s|code|pre|a)\b', html, re.I)
    closed = re.findall(r'</(b|i|u|s|code|pre|a)>', html, re.I)
    if sorted(x.lower() for x in opened) != sorted(x.lower() for x in closed):
        raise SiteError('Teglar juftligi buzilgan: har bir <b> uchun </b> bo\'lishi kerak.')
    return html


def _escape_plain(s) -> str:
    s = re.sub(r'&(?!(amp|lt|gt|quot|#\d+);)', '&amp;', s)
    return s.replace('<', '&lt;').replace('>', '&gt;')


def bot_texts(cur) -> dict:
    data = _get(cur, 'bot_texts', {})
    return {k: v for k, v in data.items() if k in BOT_TEXTS and isinstance(v, dict)} if isinstance(data, dict) else {}


def save_bot_text(cur, conn, key, uz, ru) -> dict:
    if key not in BOT_TEXTS:
        raise SiteError("Noma'lum bot matni.")
    _, _, limit, html_ok = BOT_TEXTS[key]
    clean = (lambda t: _clean_bot_html(t, limit)) if html_ok else (lambda t: ' '.join(str(t or '').split())[:limit])
    entry = {'uz': clean(uz), 'ru': clean(ru)}
    data = bot_texts(cur)
    if entry['uz'] or entry['ru']:
        data[key] = entry
    else:
        data.pop(key, None)
    _put(cur, conn, 'bot_texts', data)
    return data


_bot_cache = {'t': 0.0, 'v': {}}


def bot_text(key, lang='uz'):
    """Admin yozgan bot matni (tilida; ruschasi bo'lmasa o'zbekchasi) yoki None — koddagi standart ishlatiladi."""
    now = time.monotonic()
    if now - _bot_cache['t'] >= CACHE_S:
        try:
            from db import get_connection   # noqa: PLC0415
            conn = get_connection()
            cur = conn.cursor()
            try:
                _bot_cache['v'] = bot_texts(cur)
            finally:
                cur.close()
                conn.close()
            _bot_cache['t'] = now
        except Exception:  # noqa: BLE001
            pass
    e = _bot_cache['v'].get(key) or {}
    return e.get(lang) or e.get('uz') or None


# ───────────────────────── Dizayn ─────────────────────────

def theme(cur) -> dict:
    data = _get(cur, 'theme', {})
    return {k: v for k, v in data.items() if k in THEME and isinstance(v, str) and _HEX.match(v)} if isinstance(data, dict) else {}


def save_theme(cur, conn, colors) -> dict:
    data = {}
    for key, value in (colors or {}).items():
        if key not in THEME:
            raise SiteError(f"Noma'lum rang: {key}")
        value = str(value or '').strip()
        if not value or value.lower() == THEME[key][2].lower():
            continue
        if not _HEX.match(value):
            raise SiteError(f"«{THEME[key][0]}» — rang #RRGGBB ko'rinishida bo'lsin.")
        data[key] = value
    _put(cur, conn, 'theme', data)
    return data


def hidden_blocks(cur) -> list:
    data = _get(cur, 'layout', {})
    return [k for k in (data.get('hide') or []) if k in BLOCKS] if isinstance(data, dict) else []


def save_hidden(cur, conn, keys) -> list:
    keys = [k for k in dict.fromkeys(keys or []) if k in BLOCKS]
    _put(cur, conn, 'layout', {'hide': keys} if keys else None)
    return keys


# ───────────────────────── O'quvchi sahifalari uchun ─────────────────────────

_cache = {'t': 0.0, 'v': None}


def config(cur) -> dict:
    """Ochiq /api/site/config javobi (CACHE_S keshlanadi)."""
    now = time.monotonic()
    rules_key = json.dumps(qoidalar.values(), sort_keys=True)     # qoida o'zgarsa — kesh darhol eskiradi
    if _cache['v'] is not None and now - _cache['t'] < CACHE_S and _cache.get('rules') == rules_key:
        return _cache['v']
    texts = qoidalar.auto_texts()
    for x in ui_texts(cur):                          # admin yozganlari qoidalardan ustun
        k = norm(x['orig'])
        if x.get('uz'):
            texts['uz'][k] = x['uz']
        if x.get('ru'):
            texts['ru'][k] = x['ru']
    th = theme(cur)
    css_vars = {}
    for key, value in th.items():
        for var in THEME[key][1]:
            css_vars[var] = value
    v = str(_get(cur, 'site_v', 0)) + ':' + json.dumps(qoidalar.values(), sort_keys=True)
    out = {'ok': True, 'v': hashlib.md5(v.encode()).hexdigest()[:12], 'texts': texts, 'theme': css_vars,
           'hide': [BLOCKS[k][2] for k in hidden_blocks(cur)]}
    _cache.update(t=now, v=out, rules=rules_key)
    return out


# ───────────────────────── Matnlar katalogi (admin qidiruvi uchun) ─────────────────────────

_catalog = {'items': None}
_PAIR = re.compile(r"""(['"])((?:\\.|(?!\1)[^\\\n])*)\1\s*:\s*\n?\s*(['"])((?:\\.|(?!\3)[^\\\n])*)\3""")


def _unescape(s) -> str:
    return s.replace("\\'", "'").replace('\\"', '"').replace('\\\\', '\\')


def catalog() -> list:
    """js/i18n.js lug'atidagi barcha o'zbekcha matnlar va ruschasi — admin saytdagi yozuvni topishi uchun."""
    if _catalog['items'] is None:
        import os   # noqa: PLC0415
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'js', 'i18n.js')
        try:
            src = open(path, encoding='utf-8').read()
        except OSError:
            src = ''
        start, end = src.find('var RU = {'), src.find('var RE = [')
        body = src[start:end] if start >= 0 and end > start else ''
        seen, items = set(), []
        for m in _PAIR.finditer(body):
            uz, ru = _unescape(m.group(2)), _unescape(m.group(4))
            if uz not in seen and re.search(r'[A-Za-z]', uz):
                seen.add(uz)
                items.append({'uz': uz, 'ru': ru})
        _catalog['items'] = items
    return _catalog['items']


def search_catalog(q, limit=40) -> list:
    q = norm(q).lower()
    if len(q) < 2:
        return []
    return [x for x in catalog() if q in x['uz'].lower() or q in x['ru'].lower()][:limit]
