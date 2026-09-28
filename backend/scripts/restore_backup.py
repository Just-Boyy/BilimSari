# -*- coding: utf-8 -*-
"""
Zaxira nusxadan (bot yuborgan bilimsari-YYYY-MM-DD-HHMM.json.gz) bazani tiklash.

backend/ papkasidan, DATABASE_URL tiklanadigan bazaga qaratilgan holda:

    python scripts/restore_backup.py FAYL.json.gz              # faqat ko'rsatadi, hech narsa yozmaydi
    python scripts/restore_backup.py FAYL.json.gz --apply      # bo'sh (yangi) bazaga yozadi
    python scripts/restore_backup.py FAYL.json.gz --apply --replace
        # DIQQAT: nusxadagi jadvallardagi hozirgi qatorlar o'chiriladi

Jadvallar avval app.init_db() bilan yaratiladi (darslar kod'dan qayta
yoziladi), keyin nusxadagi qatorlar qo'shiladi. Sessiya tokenlari nusxada
yo'q — o'quvchilar Telegram orqali avtomatik qayta kiradi.
"""
import os
import sys

os.environ.setdefault('SCHEDULER_ENABLED', '0')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = {a for a in sys.argv[1:] if a.startswith('--')}
    if len(args) != 1:
        print(__doc__)
        sys.exit(2)

    import backup
    with open(args[0], 'rb') as fh:
        data = backup.unpack(fh.read())
    print(f"Nusxa: {data['created']} ({data['db']}), {len(data['tables'])} jadval")
    for name, table in sorted(data['tables'].items()):
        print(f"  {name:28} {len(table['rows']):>7} qator")

    if '--apply' not in flags:
        print('\nHech narsa yozilmadi. Tiklash uchun: --apply')
        return

    import app  # noqa: F401  (import vaqtida init_db jadvallarni yaratadi)
    from db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT COUNT(*) AS n FROM users')
        if cur.fetchone()['n'] and '--replace' not in flags:
            print("\nBazada allaqachon o'quvchilar bor. Ustidan yozish uchun --replace qo'shing.")
            sys.exit(1)
        written = backup.restore(cur, conn, data, replace='--replace' in flags)
    finally:
        cur.close()
        conn.close()
    print('\nTiklandi:')
    for name, n in sorted(written.items()):
        print(f'  {name:28} {n:>7} qator')


if __name__ == '__main__':
    main()
