# -*- coding: utf-8 -*-
"""Barcha lokal testlarni ishga tushiradi.

Har bir test alohida jarayonda va o'zining vaqtinchalik SQLite bazasida ishlaydi —
testlar bir-biriga va ishchi bazilimsari.db'ga ta'sir qilmaydi. Prod sozlamalari
(DATABASE_URL, BOT_TOKEN, AI kalitlari) olib tashlanadi: test hech qachon prod bazasiga
yoki Telegram/AI'ga murojaat qilmaydi.

    python tests/run_all.py              # hammasi
    python tests/run_all.py til ramka    # nomida shu so'z bor testlar
    python tests/run_all.py -v           # har bir testning to'liq chiqishi

Prod'dagi tekshiruvlar alohida: tests/prod/ (ADMIN_PW kerak, sinov foydalanuvchilari
yaratilib, oxirida o'chiriladi).
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
SECRET_ENV = ('DATABASE_URL', 'BOT_TOKEN', 'TELEGRAM_BOT_TOKEN', 'GOOGLE_AI_API_KEY', 'GEMINI_API_KEY',
              'GOOGLE_API_KEY', 'OPENROUTER_API_KEY', 'DEEPSEEK_API_KEY', 'ADMIN_PASSWORD', 'ADMIN_PW')
# Hamma testlar uchun sinov qiymatlari (haqiqiy emas) va ayrim testlarga qo'shimcha
TEST_ENV = {'ADMIN_PASSWORD': 'sinov-admin-paroli', 'SCHEDULER_ENABLED': '0', 'FLASK_SKIP_DOTENV': '1'}
PER_TEST_ENV = {'test_admin_tg.py': {'BOT_TOKEN': '000000:SINOV-SOXTA-TOKEN'}}


def main(argv):
    try:                      # Windows konsoli (cp1252) — test chiqishidagi o'zbekcha/ruscha belgilar yiqitmasin
        sys.stdout.reconfigure(errors='replace')
    except (AttributeError, ValueError):
        pass
    verbose = '-v' in argv
    words = [a for a in argv if not a.startswith('-')]
    files = sorted(glob.glob(os.path.join(HERE, 'test_*.py')))
    if words:
        files = [f for f in files if any(w in os.path.basename(f) for w in words)]
    if not files:
        print('Test topilmadi.')
        return 1

    failed = []
    t_all = time.time()
    for f in files:
        name = os.path.basename(f)
        tmp = tempfile.mkdtemp(prefix='bilimsari-test-')
        env = {k: v for k, v in os.environ.items() if k not in SECRET_ENV}
        env.update(TEST_ENV)
        env.update(PER_TEST_ENV.get(name, {}))
        env.update({'SQLITE_PATH': os.path.join(tmp, 'test.db'), 'PYTHONIOENCODING': 'utf-8',
                    'PYTHONUTF8': '1'})
        t0 = time.time()
        try:
            p = subprocess.run([sys.executable, f], cwd=BACKEND, env=env, capture_output=True,
                               text=True, encoding='utf-8', errors='replace', timeout=900)
            code, out = p.returncode, (p.stdout or '') + (p.stderr or '')
        except subprocess.TimeoutExpired:
            code, out = -1, 'VAQT TUGADI (15 daqiqa)'
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        # Ko'p testlar FAIL bo'lsa ham 0 kod bilan chiqadi — chiqishdagi FAIL qatori ham yiqilish
        ok = code == 0 and not any(ln.lstrip().startswith('FAIL ') for ln in out.splitlines())
        print(f"{'OK  ' if ok else 'XATO'} {name:28s} {time.time() - t0:5.1f} s")
        if not ok:
            failed.append(name)
        if verbose or not ok:
            lines = [ln for ln in out.splitlines() if verbose or 'FAIL' in ln or 'Error' in ln
                     or 'Traceback' in ln or 'XATO' in ln or ln.startswith('  File')]
            print('\n'.join('     ' + ln for ln in (lines if verbose else lines[-25:])))
    print(f"\n{len(files) - len(failed)}/{len(files)} test o'tdi ({time.time() - t_all:.0f} s)"
          + (f". Yiqilgan: {', '.join(failed)}" if failed else ''))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
