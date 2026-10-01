# -*- coding: utf-8 -*-
"""
SUBJECT_CATALOG'ga qo'shilgan, lekin hali curriculum'da yo'q fan(lar) uchun
mavzularni noldan yaratadi (7-sinf darajasidan boshlab, osondan murakkabga).

Mantiq extend_curriculum.py'da — u ham ikki tilli: har bir AI so'rovi
mavzularni o'zbekcha va ruscha birga qaytaradi; o'zbekchasi
curriculum/ai_curriculum.py'ga, ruschasi curriculum/ru/<fan>.json'ga yoziladi.
Uzilib qolsa, qayta ishga tushirilganda tayyor mavzular qayta yaratilmaydi.

Ishga tushirish: GOOGLE_AI_API_KEY (yoki GEMINI_API_KEY) muhit
o'zgaruvchisi o'rnatilgan holda, backend/ papkasidan:
    python scripts/generate_curriculum.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extend_curriculum as ext  # noqa: E402

TOPICS_PER_SUBJECT = 30


def main():
    if not ext.API_KEY:
        print('XATO: GOOGLE_AI_API_KEY muhit o\'zgaruvchisi topilmadi.')
        sys.exit(1)
    done = {s['key'] for s in ext.load_subjects() if s.get('topics')}
    missing = [k for k in ext.SUBJECT_CATALOG if k not in done]
    if not missing:
        print('Barcha fanlar curriculum\'da bor. Mavzu qo\'shish uchun: python scripts/extend_curriculum.py')
        return
    print(f'Yangi fanlar: {missing}', flush=True)
    ext.extend(TOPICS_PER_SUBJECT, set(missing))


if __name__ == '__main__':
    main()
