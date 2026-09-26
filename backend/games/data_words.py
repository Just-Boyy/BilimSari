# -*- coding: utf-8 -*-
"""
Word Battle so'z banki.

Daraja: 0 — oson, 1 — o'rta, 2 — qiyin.
Sinonim/antonim juftliklarida "guruh" bor: bir guruhdagi so'zlar bir-biriga
chalg'ituvchi variant sifatida TUSHMAYDI (masalan, "katta" savolida "past"
variant bo'lib chiqmaydi — ikkalasi o'lcham guruhida), shunda bitta savolda
ikkita to'g'ri javob bo'lib qolmaydi.
"""

# (english, uzbek, daraja)
EN_TRANSLATIONS = (
    ('apple', 'olma', 0), ('book', 'kitob', 0), ('water', 'suv', 0),
    ('sun', 'quyosh', 0), ('moon', 'oy', 0), ('house', 'uy', 0),
    ('school', 'maktab', 0), ('friend', "do'st", 0), ('family', 'oila', 0),
    ('mother', 'ona', 0), ('father', 'ota', 0), ('dog', 'it', 0),
    ('cat', 'mushuk', 0), ('bird', 'qush', 0), ('tree', 'daraxt', 0),
    ('flower', 'gul', 0), ('bread', 'non', 0), ('milk', 'sut', 0),
    ('city', 'shahar', 0), ('road', "yo'l", 0), ('window', 'deraza', 0),
    ('door', 'eshik', 0), ('table', 'stol', 0), ('red', 'qizil', 0),

    ('to read', "o'qimoq", 1), ('to write', 'yozmoq', 1), ('to run', 'yugurmoq', 1),
    ('to swim', 'suzmoq', 1), ('to learn', "o'rganmoq", 1), ('to sing', 'kuylamoq', 1),
    ('to build', 'qurmoq', 1), ('to forget', 'unutmoq', 1), ('beautiful', 'chiroyli', 1),
    ('strong', 'kuchli', 1), ('difficult', 'qiyin', 1), ('easy', 'oson', 1),
    ('clean', 'toza', 1), ('hungry', 'och', 1), ('tired', 'charchagan', 1),
    ('brave', 'jasur', 1), ('honest', 'halol', 1), ('busy', 'band', 1),

    ('knowledge', 'bilim', 2), ('experience', 'tajriba', 2), ('environment', 'atrof-muhit', 2),
    ('opportunity', 'imkoniyat', 2), ('responsibility', "mas'uliyat", 2), ('government', 'hukumat', 2),
    ('society', 'jamiyat', 2), ('independence', 'mustaqillik', 2), ('development', 'rivojlanish', 2),
    ('research', 'tadqiqot', 2), ('patience', 'sabr', 2), ('justice', 'adolat', 2),
    ('health', "sog'liq", 2), ('education', "ta'lim", 2), ('success', 'muvaffaqiyat', 2),
)

# (so'z, sinonim, o'zbekcha ma'nosi, guruh, daraja)
EN_SYNONYMS = (
    ('big', 'large', 'katta', 'size', 0),
    ('small', 'little', 'kichik', 'size', 0),
    ('happy', 'glad', 'xursand', 'feeling', 0),
    ('begin', 'start', 'boshlamoq', 'start', 0),
    ('fast', 'quick', 'tez', 'speed', 0),
    ('smart', 'clever', 'aqlli', 'mind', 0),
    ('shut', 'close', 'yopmoq', 'door', 0),
    ('gift', 'present', "sovg'a", 'gift', 0),
    ('finish', 'end', 'tugatmoq', 'start', 1),
    ('hard', 'difficult', 'qiyin', 'difficulty', 1),
    ('easy', 'simple', 'oson', 'difficulty', 1),
    ('answer', 'reply', 'javob bermoq', 'talk', 1),
    ('choose', 'select', 'tanlamoq', 'choose', 1),
    ('sick', 'ill', 'kasal', 'health', 1),
    ('quiet', 'silent', 'jim', 'sound', 1),
    ('mistake', 'error', 'xato', 'mistake', 1),
    ('rich', 'wealthy', 'boy', 'money', 2),
    ('buy', 'purchase', 'sotib olmoq', 'money', 2),
    ('help', 'assist', 'yordam bermoq', 'help', 2),
    ('brave', 'courageous', 'jasur', 'character', 2),
    ('huge', 'enormous', 'ulkan', 'size', 2),
    ('repair', 'fix', 'tuzatmoq', 'repair', 2),
    ('journey', 'trip', 'sayohat', 'travel', 2),
    ('idea', 'thought', 'fikr', 'mind', 2),
)

# (so'z, antonim, o'zbekcha ma'nosi, guruh, daraja)
EN_ANTONYMS = (
    ('hot', 'cold', 'issiq — sovuq', 'temp', 0),
    ('big', 'small', 'katta — kichik', 'size', 0),
    ('happy', 'sad', 'xursand — xafa', 'feeling', 0),
    ('day', 'night', 'kun — tun', 'time', 0),
    ('open', 'close', 'ochmoq — yopmoq', 'door', 0),
    ('up', 'down', 'yuqori — past', 'direction', 0),
    ('old', 'new', 'eski — yangi', 'age', 0),
    ('fast', 'slow', 'tez — sekin', 'speed', 1),
    ('early', 'late', 'erta — kech', 'time', 1),
    ('strong', 'weak', 'kuchli — kuchsiz', 'strength', 1),
    ('full', 'empty', "to'la — bo'sh", 'amount', 1),
    ('win', 'lose', 'yutmoq — yutqazmoq', 'result', 1),
    ('clean', 'dirty', 'toza — iflos', 'clean', 1),
    ('light', 'dark', "yorug' — qorong'i", 'light', 1),
    ('rich', 'poor', "boy — kambag'al", 'money', 2),
    ('buy', 'sell', 'sotib olmoq — sotmoq', 'money', 2),
    ('cheap', 'expensive', 'arzon — qimmat', 'money', 2),
    ('always', 'never', 'doim — hech qachon', 'frequency', 2),
    ('remember', 'forget', 'eslamoq — unutmoq', 'mind', 2),
    ('push', 'pull', 'itarmoq — tortmoq', 'force', 2),
    ('arrive', 'leave', 'kelmoq — ketmoq', 'move', 2),
)

# (to'g'ri yozilishi, (3 ta xato variant), o'zbekcha ma'nosi, daraja)
EN_SPELLING = (
    ('because', ('becuase', 'becouse', 'beacause'), 'chunki', 0),
    ('friend', ('freind', 'frend', 'friiend'), "do'st", 0),
    ('beautiful', ('beatiful', 'beautifull', 'beutiful'), 'chiroyli', 0),
    ('tomorrow', ('tommorow', 'tomorow', 'tommorrow'), 'ertaga', 0),
    ('different', ('diffrent', 'differant', 'diferent'), 'boshqacha', 0),
    ('believe', ('beleive', 'belive', 'beleave'), 'ishonmoq', 1),
    ('receive', ('recieve', 'receeve', 'resieve'), 'qabul qilmoq', 1),
    ('library', ('libary', 'librery', 'liberary'), 'kutubxona', 1),
    ('February', ('Febuary', 'Februray', 'Febrary'), 'fevral', 1),
    ('Wednesday', ('Wensday', 'Wednsday', 'Wendesday'), 'chorshanba', 1),
    ('business', ('buisness', 'bussiness', 'busness'), 'biznes', 1),
    ('science', ('sience', 'scince', 'sciense'), 'fan', 1),
    ('calendar', ('calender', 'calandar', 'kalendar'), 'taqvim', 1),
    ('necessary', ('neccessary', 'necesary', 'nessesary'), 'zarur', 2),
    ('separate', ('seperate', 'separete', 'seprate'), 'alohida', 2),
    ('definitely', ('definately', 'definitly', 'defenitely'), 'albatta', 2),
    ('government', ('goverment', 'governmant', 'govermint'), 'hukumat', 2),
    ('environment', ('enviroment', 'environmant', 'enviornment'), 'atrof-muhit', 2),
    ('knowledge', ('knowlege', 'knowledg', 'nowledge'), 'bilim', 2),
    ('height', ('hieght', 'heigth', 'hight'), 'balandlik', 2),
)

# (so'z, sinonim, guruh, daraja)
UZ_SYNONYMS = (
    ('chiroyli', "go'zal", 'gozallik', 0),
    ('katta', 'ulkan', 'olcham', 0),
    ('aqlli', 'dono', 'aql', 0),
    ("do'st", "o'rtoq", 'dostlik', 0),
    ('odam', 'kishi', 'odam', 0),
    ('quvonch', 'shodlik', 'his', 0),
    ("qayg'u", "g'am", 'his', 1),
    ('vatan', 'yurt', 'vatan', 1),
    ('kuchli', 'baquvvat', 'kuch', 1),
    ('jasur', 'botir', 'xarakter', 1),
    ('boy', 'badavlat', 'boylik', 1),
    ('sokin', 'jim', 'tovush', 1),
    ('toza', 'ozoda', 'tozalik', 1),
    ('xato', 'yanglish', 'xato', 1),
    ('ilm', 'bilim', 'bilim', 1),
    ('yordam', "ko'mak", 'yordam', 1),
    ('qadimgi', "ko'hna", 'vaqt', 2),
    ('fikr', "o'y", 'aql', 2),
    ('mashhur', 'taniqli', 'shuhrat', 2),
    ('qiyin', 'mushkul', 'qiyinlik', 2),
    ('oson', 'yengil', 'qiyinlik', 2),
    ('yuz', 'chehra', 'tana', 2),
    ('baxt', 'saodat', 'his', 2),
)

# (so'z, antonim, guruh, daraja)
UZ_ANTONYMS = (
    ('katta', 'kichik', 'olcham', 0),
    ('issiq', 'sovuq', 'harorat', 0),
    ('oq', 'qora', 'rang', 0),
    ('kun', 'tun', 'vaqt', 0),
    ('yaxshi', 'yomon', 'baho', 0),
    ("do'st", 'dushman', 'munosabat', 0),
    ('ochmoq', 'yopmoq', 'harakat', 0),
    ('baland', 'past', 'olcham', 1),
    ('keng', 'tor', 'olcham', 1),
    ('uzun', 'qisqa', 'olcham', 1),
    ('kirmoq', 'chiqmoq', 'harakat', 1),
    ('kulmoq', "yig'lamoq", 'his', 1),
    ('tez', 'sekin', 'tezlik', 1),
    ('yaqin', 'uzoq', 'masofa', 1),
    ('yangi', 'eski', 'davr', 1),
    ('achchiq', 'shirin', 'maza', 1),
    ('boy', "kambag'al", 'boylik', 2),
    ('oson', 'qiyin', 'qiyinlik', 2),
    ("ko'p", 'oz', 'miqdor', 2),
    ('ichkari', 'tashqari', 'joy', 2),
    ('yoz', 'qish', 'fasl', 2),
    ("ho'l", 'quruq', 'namlik', 2),
    ("to'la", "bo'sh", 'miqdor', 2),
    ('tong', 'shom', 'vaqt', 2),
    ('semiz', "ozg'in", 'tana', 2),
)
