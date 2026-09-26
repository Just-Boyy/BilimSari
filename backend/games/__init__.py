# -*- coding: utf-8 -*-
"""
BilimSari Game Hub — ta'limga yo'naltirilgan multiplayer o'yinlar.

Modullar:
    catalog      — o'yin turlari va sozlamalar (yangi o'yin shu yerga qo'shiladi)
    questions    — savol generatorlari (curriculum, matematika, so'zlar, kod, moslash)
    rooms        — room kodi, o'yinchilar, host huquqlari, muddat va tozalash
    engine       — server tomonidagi o'yin holati, javob tekshiruvi, ball
    matchmaking  — random raqib qidirish navbati
    stats        — reyting, profil statistikasi, chaqmoq
    api          — /api/games/* Flask blueprint

Real-time: hozircha mijoz holatni qisqa polling bilan oladi (mavjud Flask +
gunicorn stack'iga yangi infratuzilma qo'shmasdan). Holat to'liq serverda
bo'lgani uchun keyinchalik WebSocket/SSE transportiga o'tishda faqat
yetkazib berish qatlami o'zgaradi, o'yin mantig'i emas.
"""
