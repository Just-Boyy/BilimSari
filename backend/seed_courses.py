"""Fanlar (courses) — PostgreSQL seed"""

COURSES_SEED = [
    {
        "id": "english",
        "icon": "lang",
        "name": "Ingliz tili",
        "desc": "So‘zlar, gaplar va muloqot",
        "color": "#FF4B4B",
        "sort": 1,
        "units": [{
            "id": "en-u1",
            "title": "1-bo‘lim: Asoslar",
            "desc": "Salomlashish va oddiy gaplar",
            "lessons": [
                ("en-l1", "Salomlashish", "star", "lesson"),
                ("en-l2", "Oila", "star", "lesson"),
                ("en-l3", "Mashq", "dumbbell", "practice"),
                ("en-l4", "Raqamlar", "star", "lesson"),
                ("en-l5", "Ranglar", "star", "lesson"),
                ("en-l6", "Test", "trophy", "review"),
            ],
        }],
    },
    {
        "id": "uzbek",
        "icon": "book",
        "name": "Ona tili",
        "desc": "Imlo, so‘z va gap tuzilishi",
        "color": "#58A700",
        "sort": 2,
        "units": [{
            "id": "uz-u1",
            "title": "1-bo‘lim: Asoslar",
            "desc": "To‘g‘ri yozuv va ifoda",
            "lessons": [
                ("uz-l1", "Unli va undosh", "star", "lesson"),
                ("uz-l2", "So‘z turkumlari", "star", "lesson"),
                ("uz-l3", "Mashq", "dumbbell", "practice"),
                ("uz-l4", "Gap bo‘laklari", "star", "lesson"),
                ("uz-l5", "Test", "trophy", "review"),
            ],
        }],
    },
    {
        "id": "russian",
        "icon": "lang",
        "name": "Rus tili",
        "desc": "Lug‘at va oddiy muloqot",
        "color": "#1CB0F6",
        "sort": 3,
        "units": [{
            "id": "ru-u1",
            "title": "1-bo‘lim: Asoslar",
            "desc": "Salom va tanishuv",
            "lessons": [
                ("ru-l1", "Приветствие", "star", "lesson"),
                ("ru-l2", "Семья", "star", "lesson"),
                ("ru-l3", "Mashq", "dumbbell", "practice"),
                ("ru-l4", "Числа", "star", "lesson"),
                ("ru-l5", "Test", "trophy", "review"),
            ],
        }],
    },
    {
        "id": "geography",
        "icon": "globe",
        "name": "Geografiya",
        "desc": "Dunyo va O‘zbekiston",
        "color": "#0EA5E9",
        "sort": 4,
        "units": [{
            "id": "geo-u1",
            "title": "1-bo‘lim: Asoslar",
            "desc": "Xarita va qit’alar",
            "lessons": [
                ("geo-l1", "Qit’alar", "star", "lesson"),
                ("geo-l2", "Okeanlar", "star", "lesson"),
                ("geo-l3", "Mashq", "dumbbell", "practice"),
                ("geo-l4", "O‘zbekiston", "star", "lesson"),
                ("geo-l5", "Test", "trophy", "review"),
            ],
        }],
    },
    {
        "id": "math",
        "icon": "calc",
        "name": "Matematika",
        "desc": "Arifmetika va mantiq",
        "color": "#7C3AED",
        "sort": 5,
        "units": [{
            "id": "math-u1",
            "title": "1-bo‘lim: Sonlar",
            "desc": "Qo‘shish, ayirish, ko‘paytirish",
            "lessons": [
                ("m-l1", "Qo‘shish", "star", "lesson"),
                ("m-l2", "Ayirish", "star", "lesson"),
                ("m-l3", "Mashq", "dumbbell", "practice"),
                ("m-l4", "Ko‘paytirish", "star", "lesson"),
                ("m-l5", "Bo‘lish", "star", "lesson"),
                ("m-l6", "Test", "trophy", "review"),
            ],
        }],
    },
    {
        "id": "geometry",
        "icon": "shapes",
        "name": "Geometriya",
        "desc": "Shakllar va o‘lchovlar",
        "color": "#F59E0B",
        "sort": 6,
        "units": [{
            "id": "geom-u1",
            "title": "1-bo‘lim: Shakllar",
            "desc": "Nuqta, chiziq, burchak",
            "lessons": [
                ("ge-l1", "Nuqta va chiziq", "star", "lesson"),
                ("ge-l2", "Burchaklar", "star", "lesson"),
                ("ge-l3", "Mashq", "dumbbell", "practice"),
                ("ge-l4", "Uchburchak", "star", "lesson"),
                ("ge-l5", "Test", "trophy", "review"),
            ],
        }],
    },
    {
        "id": "law",
        "icon": "scale",
        "name": "Huquq",
        "desc": "Huquq asoslari va burchlar",
        "color": "#64748B",
        "sort": 7,
        "units": [{
            "id": "law-u1",
            "title": "1-bo‘lim: Asoslar",
            "desc": "Konstitutsiya va huquq",
            "lessons": [
                ("law-l1", "Huquq nima?", "star", "lesson"),
                ("law-l2", "Huquq va burch", "star", "lesson"),
                ("law-l3", "Mashq", "dumbbell", "practice"),
                ("law-l4", "Bolalar huquqlari", "star", "lesson"),
                ("law-l5", "Test", "trophy", "review"),
            ],
        }],
    },
    {
        "id": "biology",
        "icon": "leaf",
        "name": "Biologiya",
        "desc": "Tirik tabiat asoslari",
        "color": "#22C55E",
        "sort": 8,
        "units": [{
            "id": "bio-u1",
            "title": "1-bo‘lim: Asoslar",
            "desc": "Hujayra va organizmlar",
            "lessons": [
                ("bio-l1", "Tirik mavjudotlar", "star", "lesson"),
                ("bio-l2", "Hujayra", "star", "lesson"),
                ("bio-l3", "Mashq", "dumbbell", "practice"),
                ("bio-l4", "O‘simliklar", "star", "lesson"),
                ("bio-l5", "Test", "trophy", "review"),
            ],
        }],
    },
    {
        "id": "literature",
        "icon": "book",
        "name": "Adabiyot",
        "desc": "Asarlar va yozuvchilar",
        "color": "#EC4899",
        "sort": 9,
        "units": [{
            "id": "lit-u1",
            "title": "1-bo‘lim: Asoslar",
            "desc": "Janrlar va she’r",
            "lessons": [
                ("lit-l1", "Adabiyot nima?", "star", "lesson"),
                ("lit-l2", "She’r va nasr", "star", "lesson"),
                ("lit-l3", "Mashq", "dumbbell", "practice"),
                ("lit-l4", "O‘zbek adiblari", "star", "lesson"),
                ("lit-l5", "Test", "trophy", "review"),
            ],
        }],
    },
]


def ensure_course_tables(cur, conn):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            icon TEXT,
            name TEXT NOT NULL,
            description TEXT,
            color TEXT,
            sort_order INTEGER DEFAULT 0
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            sort_order INTEGER DEFAULT 0
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id TEXT PRIMARY KEY,
            unit_id TEXT NOT NULL REFERENCES units(id) ON DELETE CASCADE,
            course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            icon TEXT,
            lesson_type TEXT DEFAULT 'lesson',
            sort_order INTEGER DEFAULT 0
        )
    ''')
    conn.commit()


def seed_courses(cur, conn):
    ensure_course_tables(cur, conn)
    cur.execute('SELECT COUNT(*) AS c FROM courses')
    row = cur.fetchone()
    count = row['c'] if row else 0
    if count and count >= 9:
        return

    # To‘liq qayta yuklash
    cur.execute('DELETE FROM lessons')
    cur.execute('DELETE FROM units')
    cur.execute('DELETE FROM courses')

    for c in COURSES_SEED:
        cur.execute(
            'INSERT INTO courses (id, icon, name, description, color, sort_order) VALUES (%s,%s,%s,%s,%s,%s)',
            (c['id'], c['icon'], c['name'], c['desc'], c['color'], c['sort'])
        )
        for ui, u in enumerate(c['units']):
            cur.execute(
                'INSERT INTO units (id, course_id, title, description, sort_order) VALUES (%s,%s,%s,%s,%s)',
                (u['id'], c['id'], u['title'], u['desc'], ui)
            )
            for li, les in enumerate(u['lessons']):
                lid, title, icon, ltype = les
                cur.execute(
                    'INSERT INTO lessons (id, unit_id, course_id, title, icon, lesson_type, sort_order) '
                    'VALUES (%s,%s,%s,%s,%s,%s,%s)',
                    (lid, u['id'], c['id'], title, icon, ltype, li)
                )
    conn.commit()


def fetch_courses_tree(cur):
    cur.execute('SELECT id, icon, name, description, color, sort_order FROM courses ORDER BY sort_order, name')
    courses = cur.fetchall()
    result = []
    for c in courses:
        cur.execute(
            'SELECT id, title, description, sort_order FROM units WHERE course_id = %s ORDER BY sort_order',
            (c['id'],)
        )
        units_rows = cur.fetchall()
        units = []
        for u in units_rows:
            cur.execute(
                'SELECT id, title, icon, lesson_type, sort_order FROM lessons '
                'WHERE unit_id = %s ORDER BY sort_order',
                (u['id'],)
            )
            lessons = [
                {
                    'id': L['id'],
                    'title': L['title'],
                    'icon': L['icon'] or 'star',
                    'type': L['lesson_type'] or 'lesson',
                }
                for L in cur.fetchall()
            ]
            units.append({
                'id': u['id'],
                'title': u['title'],
                'desc': u['description'] or '',
                'lessons': lessons,
            })
        result.append({
            'id': c['id'],
            'icon': c['icon'] or 'book',
            'name': c['name'],
            'desc': c['description'] or '',
            'color': c['color'] or '#58A700',
            'units': units,
        })
    return result
