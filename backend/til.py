# -*- coding: utf-8 -*-
"""
Kontent tili: o'quvchi interfeysni ruscha qilgan bo'lsa — darslar, testlar, uy vazifasi,
kun savoli va o'yin savollari ham ruscha.

Ruscha matnlar curriculum/ru/<fan>.json'da (mavzu slug'i bo'yicha) va bazada topics.title_ru,
topics.summary_ru, topics.ru (dars, test, uy vazifasi — JSON) ustunlarida saqlanadi.

Tuzilma va to'g'ri javoblar DOIM o'zbekcha (asl) nusxadan olinadi — ruscha nusxa faqat matnni
almashtiradi. Tarjimadagi savol tuzilmasi aslinikiga mos kelmasa (masalan, admin keyinroq
o'zbekcha testni o'zgartirgan bo'lsa) — o'sha savol o'zbekcha ko'rsatiladi. Uy vazifasidagi
matnli javob ikkala tilda ham qabul qilinadi.

Til so'rovdan olinadi: frontend har so'rovga X-Lang (uz | ru) sarlavhasini qo'shadi.
"""

import copy
import json

LANGS = ('uz', 'ru')


def req_lang() -> str:
    """Joriy so'rov tili. So'rovdan tashqarida (rejalashtiruvchi, testlar) — 'uz'."""
    try:
        from flask import has_request_context, request
    except ImportError:  # pragma: no cover
        return 'uz'
    if not has_request_context():
        return 'uz'
    h = (request.headers.get('X-Lang') or '').strip().lower()
    if h in LANGS:
        return h
    user = getattr(request, 'user', None) or {}
    return 'ru' if user.get('lang') == 'ru' else 'uz'


def _load(value, default):
    if value is None or value == '':
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def merge_quiz(quiz, ru_quiz) -> list:
    """Asl test + ruscha matn. Javob va tur — asldan; tuzilma mos kelmasa — o'sha savol asl holicha."""
    out = []
    ru_quiz = ru_quiz if isinstance(ru_quiz, list) else []
    for i, q in enumerate(quiz or []):
        r = ru_quiz[i] if i < len(ru_quiz) and isinstance(ru_quiz[i], dict) else None
        item = dict(q)
        qtype = q.get('type', 'mc')
        if r and r.get('q') and r.get('type', 'mc') == qtype and (
                qtype != 'mc' or len(r.get('options') or []) == len(q.get('options') or [])):
            item['q'] = r['q']
            if qtype == 'mc':
                item['options'] = list(r['options'])
            if r.get('explain'):
                item['explain'] = r['explain']
            if qtype not in ('mc', 'tf') and r.get('answer') not in (None, ''):
                # Matnli javob: ruscha ko'rsatiladi, ikkala til ham qabul qilinadi
                item['answer'] = r['answer']
                item['accept'] = list(r.get('accept') or []) + [q.get('answer')] + list(q.get('accept') or [])
        out.append(item)
    return out


def merge_homework(hw, ru_hw) -> dict:
    hw = copy.deepcopy(hw or {})
    if not isinstance(ru_hw, dict):
        return hw
    if ru_hw.get('intro'):
        hw['intro'] = ru_hw['intro']
    ru_tasks = {t.get('id'): t for t in ru_hw.get('tasks') or [] if isinstance(t, dict)}
    for t in hw.get('tasks') or []:
        r = ru_tasks.get(t.get('id'))
        if not r:
            continue
        if r.get('prompt'):
            t['prompt'] = r['prompt']
        if r.get('hint'):
            t['hint'] = r['hint']
        if t.get('answer') not in (None, '') and r.get('answer') not in (None, ''):
            uz_answer, uz_accept = t['answer'], list(t.get('accept') or [])
            t['answer'] = r['answer']
            t['accept'] = [a for a in list(r.get('accept') or []) + [uz_answer] + uz_accept if a not in (None, '')]
    return hw


def ru_of(row) -> dict:
    """topics.ru — {'lesson', 'quiz', 'homework'} yoki {}."""
    data = _load((row or {}).get('ru'), {})
    return data if isinstance(data, dict) else {}


def topic(row, lang=None) -> dict:
    """Mavzu qatori (dict nusxa) — tilga qarab nom, tavsif, dars, test va uy vazifasi."""
    lang = lang or req_lang()
    t = dict(row)
    t['quiz'] = _load(row.get('quiz'), [])
    t['lesson'] = _load(row.get('lesson'), [])
    t['homework'] = _load(row.get('homework'), {})
    if lang != 'ru':
        return t
    if row.get('title_ru'):
        t['title'] = row['title_ru']
    if row.get('summary_ru'):
        t['summary'] = row['summary_ru']
    ru = ru_of(row)
    if ru.get('lesson'):
        t['lesson'] = ru['lesson']
    if ru.get('quiz'):
        t['quiz'] = merge_quiz(t['quiz'], ru['quiz'])
    if ru.get('homework'):
        t['homework'] = merge_homework(t['homework'], ru['homework'])
    return t


def titles(rows, lang=None):
    """Ro'yxatlar uchun (title_ru, summary_ru ustunlari tanlangan qatorlar): joyida almashtiradi."""
    lang = lang or req_lang()
    if lang != 'ru':
        return rows
    for r in rows:
        if r.get('title_ru'):
            r['title'] = r['title_ru']
        if r.get('summary_ru'):
            r['summary'] = r['summary_ru']
    return rows


def quiz_pair(row) -> tuple:
    """(asl test, ruscha test yoki None) — o'yin va kun savoli ikkala tilni birga saqlaydi."""
    quiz = _load(row.get('quiz'), [])
    ru = ru_of(row)
    return quiz, (merge_quiz(quiz, ru['quiz']) if ru.get('quiz') else None)


TF_OPTIONS = {'uz': ["To'g'ri", "Noto'g'ri"], 'ru': ['Верно', 'Неверно']}


def tf_options(lang=None):
    return TF_OPTIONS['ru' if (lang or req_lang()) == 'ru' else 'uz']
