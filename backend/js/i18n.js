/* BilimSari — interfeys tili (o'zbekcha / ruscha).

   Ilova o'zbek tilida yozilgan. Rus tili tanlansa, sahifadagi interfeys
   matnlari (tugmalar, sarlavhalar, xabarlar, xatolar) shu lug'at orqali
   ruschaga almashtiriladi: sahifa yuklanganda va keyin JS qo'shgan har bir
   yangi matnda (MutationObserver — ekranga chizilishidan oldin ishlaydi).
   Dars mazmuni (mavzu matni, test savollari) o'zbekcha qoladi; translate="no"
   belgisi bor joylarga tegilmaydi.

   Til localStorage'da (bilimsari_lang) va serverda (users.lang) saqlanadi.
   I18N.t(matn) — JS ichidan tarjima; I18N.til — 'uz' yoki 'ru'.

   Admin panelda o'zgartirilgan matnlar (o'zbekcha va ruscha), ranglar va yashirilgan bloklar ham shu yerda
   qo'llanadi: /api/site/config dan olinadi va localStorage'da saqlanadi — keyingi ochilishda sahifa
   chizilishidan oldin ishlaydi. */
(function () {
  var KALIT = 'bilimsari_lang';
  var til = 'uz';
  try { til = localStorage.getItem(KALIT) === 'ru' ? 'ru' : 'uz'; } catch (e) { /* xotira yopiq */ }

  function ko(n, bir, ikki, kop) {
    n = Math.abs(parseInt(String(n).replace(/\s/g, ''), 10)) % 100;
    var n1 = n % 10;
    if (n > 10 && n < 20) return kop;
    if (n1 > 1 && n1 < 5) return ikki;
    if (n1 === 1) return bir;
    return kop;
  }

  // ───────────────────────── Lug'at ─────────────────────────
  var RU = {
    // Fanlar
    'Matematika': 'Математика', 'Geometriya': 'Геометрия', 'Ona tili': 'Родной язык', 'Adabiyot': 'Литература',
    'Ingliz tili': 'Английский язык', 'Rus tili': 'Русский язык', 'Tarix': 'История', 'Geografiya': 'География',
    'Kimyo': 'Химия', 'Biologiya': 'Биология', 'Huquq': 'Право', 'Informatika': 'Информатика',

    // Navigatsiya va umumiy
    'BilimSari': 'BilimSari', 'Bosh sahifa': 'Главная', 'Bosh sahifaga': 'На главную', "Do'kon": 'Магазин',
    "O'yinlar": 'Игры', 'Profil': 'Профиль', 'Sozlamalar': 'Настройки', 'Reyting': 'Рейтинг', 'Orqaga': 'Назад',
    'Yopish': 'Закрыть', 'Saqlash': 'Сохранить', 'Saqlanmoqda...': 'Сохранение...', 'Yuklanmoqda...': 'Загрузка...',
    'Bekor qilish': 'Отмена', 'Davom etish': 'Продолжить', 'Boshlash': 'Начать', 'Tayyor': 'Готово',
    'Qo\'shish': 'Добавить', 'Qo\'llash': 'Применить', 'Nusxalash': 'Копировать', 'Nusxalandi': 'Скопировано',
    "Nusxalab bo'lmadi — qo'lda belgilang": 'Не удалось скопировать — выделите вручную', 'Yuborildi': 'Отправлено',
    'Yuborilmoqda...': 'Отправка...', 'Tekshirilmoqda...': 'Проверка...', 'Tekshirilmoqda': 'Проверяется',
    'Hisoblanmoqda...': 'Подсчёт...', 'Xatolik yuz berdi': 'Произошла ошибка', 'Hammasi': 'Все', 'Jami': 'Всего',
    'Boshqa': 'Другое', 'Siz': 'Вы', 'Bugun': 'Сегодня', 'Hafta': 'Неделя', 'Oy': 'Месяц', 'Umumiy': 'Общий',
    'Global': 'Общий', 'Davr': 'Период', 'Vaqt': 'Время', 'Ball': 'Очки', 'ball': 'очков', 'Fan': 'Предмет',
    'Mavzu': 'Тема', 'Mavzular': 'Темы', 'Savol': 'Вопрос', 'Savollar': 'Вопросы', 'Javob': 'Ответ', 'Maslahat': 'Подсказка',
    'Javoblar': 'Ответы', 'Natijalar': 'Результаты', 'Raund': 'Раунд', 'Quiz': 'Тест', 'Mashq': 'Практика',
    'Takrorlash': 'Повторение', 'Chaqmoq': 'Молнии', 'Yutuqlar': 'Достижения', 'Darajasi': 'Уровень',
    'Daraja': 'Уровень', "O'quvchi": 'Ученик', "o'quvchi": 'учеников', 'Kutilmoqda': 'Ожидается',
    'Kutishda': 'Ожидание', 'Tugallandi': 'Завершено', 'Qulflangan': 'Закрыто', 'Boshlanmagan': 'Не начато',
    'Hali boshlanmagan': 'Ещё не начато', "To'g'ri": 'Верно', "Noto'g'ri": 'Неверно', "To'g'ri!": 'Верно!',
    'Zo\'r!': 'Отлично!', 'Tabriklaymiz!': 'Поздравляем!', 'Salom!': 'Привет!', 'Boshladik!': 'Поехали!',
    'GO!': 'GO!', 'Room': 'Комната', 'Host': 'Хост', 'onlayn': 'онлайн', 'faol room': 'активных комнат',
    'Tezkor o\'tish': 'Быстрый переход', 'Asosiy menyu': 'Главное меню', 'Admin panel': 'Админ-панель',
    'Foydalanuvchilar, to\'lovlar va statistika': 'Пользователи, платежи и статистика',
    'Taxminan': 'Примерно', 'Hozir:': 'Сейчас:', 'Keyingi:': 'Далее:', 'Nishon:': 'Значок:',
    'Tugashiga:': 'До конца:', 'Qolgan vaqt': 'Осталось времени', 'Reytingda': 'В рейтинге', 'erkin javob': 'свободный ответ',
    'Javob variantlari': 'Варианты ответа', 'Mavzu bosqichlari': 'Этапы темы', 'Natijalar jadvali': 'Таблица результатов',
    'Reyting doirasi': 'Область рейтинга', 'Game Hub bo\'limlari': 'Разделы игр', 'Ma\'lumot yuklanmadi': 'Данные не загрузились',
    'Sahifani ko\'rsatib bo\'lmadi.': 'Не удалось показать страницу.', 'Qayta urinib ko\'ring.': 'Попробуйте ещё раз.',
    'Qayta urinish': 'Повторить', 'Internet aloqasi yo\'q. Ulanishni tekshiring.': 'Нет подключения к интернету. Проверьте соединение.',
    'Internet aloqasi uzildi. Qayta ulanmoqda...': 'Связь с интернетом потеряна. Переподключение...',
    'Server bilan aloqa muammosi. Qayta urinilmoqda...': 'Проблема связи с сервером. Повторяем попытку...',
    'Sessiya tugadi': 'Сеанс завершён', 'Tez orada qo\'shiladi.': 'Скоро будет добавлено.',
    'Hozircha mavjud emas': 'Пока недоступно',

    // Sarlavhalar (title)
    'Bilim Sari': 'Bilim Sari', 'BilimSari — bilim sari birinchi qadam': 'BilimSari — первый шаг к знаниям',
    'Bosh sahifa — BilimSari': 'Главная — BilimSari', 'Boshlash — BilimSari': 'Начало — BilimSari',
    'Faqat Telegram orqali — BilimSari': 'Только через Telegram — BilimSari', 'Mening fanlarim — BilimSari': 'Мои предметы — BilimSari',
    'Mavzular — BilimSari': 'Темы — BilimSari', 'Mavzu — BilimSari': 'Тема — BilimSari', 'Profil — BilimSari': 'Профиль — BilimSari',
    'Reyting — BilimSari': 'Рейтинг — BilimSari', 'Yakka mashq — BilimSari': 'Одиночная тренировка — BilimSari',
    'O\'yinlar — BilimSari': 'Игры — BilimSari', 'Kun savoli — BilimSari': 'Вопрос дня — BilimSari',
    'Sozlamalar — BilimSari': 'Настройки — BilimSari', 'Fan sotib olish — BilimSari': 'Покупка предмета — BilimSari',
    'Room yaratish — BilimSari': 'Создание комнаты — BilimSari', 'Room — BilimSari': 'Комната — BilimSari',

    // Kirish sahifalari
    'BilimSari — Telegram Mini App. Undan foydalanish uchun botni Telegram orqali oching.':
      'BilimSari — это Telegram Mini App. Чтобы пользоваться им, откройте бота в Telegram.',
    'Telegram Mini App emas': 'Это не Telegram Mini App', 'Faqat Telegram orqali ishlaydi': 'Работает только через Telegram',
    'Botni ochish': 'Открыть бота', 'Telegram orqali kirib bo\'lmadi': 'Не удалось войти через Telegram',
    'BilimSari — o\'zbek maktab o\'quvchilari uchun': 'BilimSari — для школьников Узбекистана',
    'Bilim + raqobat + zavq': 'Знания + соревнование + удовольствие',

    // Onboarding
    'Ismingiz nima?': 'Как вас зовут?', 'Sizga shu ism bilan murojaat qilamiz.': 'Мы будем обращаться к вам по этому имени.',
    'Ismingiz': 'Ваше имя', 'Ism': 'Имя', 'Masalan: Dilnoza': 'Например: Дилноза', 'O\'zim kiritaman': 'Введу сам', 'Qaysi fandan boshlaymiz?': 'С какого предмета начнём?',
    'Bu fan bepul bo\'ladi. Boshqa fanlarni keyinroq sotib olishingiz mumkin.':
      'Этот предмет будет бесплатным. Остальные предметы можно купить позже.',
    'Ismingizni to\'liq yozing.': 'Напишите имя полностью.', 'Fanlar yuklanmoqda...': 'Загрузка предметов...',
    'Fanlar tayyorlanmoqda': 'Предметы готовятся', 'Hozircha fanlar mavjud emas': 'Пока нет доступных предметов',
    'Hozircha fanlar tayyorlanmoqda. Tez orada qo\'shiladi.': 'Предметы пока готовятся. Скоро будут добавлены.',

    // Bosh sahifa (dashboard)
    'Xayrli tong': 'Доброе утро', 'Xayrli kun': 'Добрый день', 'Xayrli kech': 'Добрый вечер', 'Xayrli tun': 'Доброй ночи',
    'Bugungi reja': 'План на сегодня', 'Bugungi reja:': 'План на сегодня:', 'Bugungi mavzu': 'Тема на сегодня',
    'Kun savoliga javob berish': 'Ответить на вопрос дня', '1 ta mavzuni tugatish': 'Пройти 1 тему', '1 ta o\'yin o\'ynash': 'Сыграть 1 игру',
    'Barakalla! Bugungi reja bajarildi.': 'Молодец! План на сегодня выполнен.',
    'Barakalla! Bugungi reja to\'liq bajarildi': 'Молодец! План на сегодня полностью выполнен',
    'Chaqmoq haqida': 'О молниях', 'Har bir tugallangan mavzu +20': 'Каждая пройденная тема +20',
    'O\'yinda har 10 ball +1': 'В играх каждые 10 очков +1', 'To\'g\'ri javob +5': 'Правильный ответ +5',
    'Chaqmoq to\'plab reytingga chiqing!': 'Собирайте молнии и поднимайтесь в рейтинге!',
    'Birinchi mavzuni tugatgan o\'quvchi reytingda birinchi bo\'ladi!': 'Кто первым пройдёт тему, окажется первым в рейтинге!',
    'Reytingni ochish': 'Открыть рейтинг', 'Darsni ochish': 'Открыть урок', 'Mavzuni o\'rganish': 'Изучить тему',
    'Fanlarimga o\'tish': 'К моим предметам', 'O\'yinlarga o\'tish': 'К играм', 'Darslarga o\'tish': 'К урокам',
    'Keyingi mavzu ochildi!': 'Следующая тема открыта!', 'Mavzu ochildi!': 'Тема открыта!',
    'Keyingi mavzu qulflangan': 'Следующая тема закрыта', 'Keyingi mavzu:': 'Следующая тема:',
    'Hamma mavzu tugallandi': 'Все темы пройдены', 'Bu fanda bugungi mavzuni yakunladingiz': 'Вы завершили сегодняшнюю тему по этому предмету',
    'Bu fanda bir kunda bitta mavzu o\'rganiladi. Bu orada boshqa fanlarni o\'qishingiz mumkin.':
      'По этому предмету изучается одна тема в день. А пока можно заниматься другими предметами.',
    'Keyingi mavzu quyidagi vaqtdan so\'ng ochiladi. Bu orada boshqa fanlarni o\'qishingiz mumkin.':
      'Следующая тема откроется через указанное время. А пока можно заниматься другими предметами.',
    'Kuniga bitta mavzu — shunda bilim mustahkam o\'rnashadi': 'Одна тема в день — так знания закрепляются прочнее',
    'Boshqa fanlar': 'Другие предметы', 'Fan sotib olish': 'Купить предмет', 'Qulflangan fan': 'Закрытый предмет',
    'Ushbu fanni ochish uchun sotib oling.': 'Купите этот предмет, чтобы открыть его.',

    // Kun savoli
    'Kun savoli': 'Вопрос дня', 'Hamma uchun bitta savol': 'Один вопрос для всех', 'Bugungi savol tayyor!': 'Вопрос дня готов!',
    'Savolni ochish': 'Открыть вопрос', 'Bugungi reyting': 'Рейтинг дня', 'Bugun adashdingiz': 'Сегодня вы ошиблись',
    'To\'g\'ri javob!': 'Правильный ответ!', 'Keyingi savol:': 'Следующий вопрос:', 'Birinchi to\'g\'ri javob:': 'Первый правильный ответ:',
    'Bugun hali hech kim to\'g\'ri javob bermadi.': 'Сегодня пока никто не ответил правильно.',
    'Hech kim to\'g\'ri javob bermadi': 'Никто не ответил правильно', 'Shu haftadagi kun savollari': 'Вопросы дня на этой неделе',
    'To\'g\'ri va tez javob bering — +5 chaqmoq va kunlik reyting.': 'Отвечайте правильно и быстро — +5 молний и место в рейтинге дня.',
    'Javob yuborilmadi. Qayta urinib ko\'ring.': 'Ответ не отправлен. Попробуйте ещё раз.',
    'Vaqt tugadi — javob qabul qilinmadi.': 'Время вышло — ответ не принят.', 'Do\'stlarga ulashish': 'Поделиться с друзьями',
    'Bugungi savol hali tayyor emas.': 'Вопрос дня ещё не готов.', 'Bugungi savol topilmadi.': 'Вопрос дня не найден.',
    'Javob noto\'g\'ri formatda.': 'Неверный формат ответа.', 'Bunday variant yo\'q.': 'Такого варианта нет.',
    'Avval savolni oching.': 'Сначала откройте вопрос.', 'Bugungi savolga javob bergansiz. Ertaga yangi savol!':
      'Вы уже ответили на сегодняшний вопрос. Завтра — новый!',
    'Du': 'Пн', 'Se': 'Вт', 'Ch': 'Ср', 'Pa': 'Чт', 'Ju': 'Пт', 'Sh': 'Сб', 'Ya': 'Вс',

    // Fanlar va mavzular
    'Mening fanlarim': 'Мои предметы', 'Fanlarim': 'Мои предметы', 'Mavzular ro\'yxati': 'Список тем',
    'Mavzular tayyorlanmoqda': 'Темы готовятся', 'Darslar hali qo\'shilmagan.': 'Уроки ещё не добавлены.',
    'Darslar tayyorlanmoqda.': 'Уроки готовятся.', 'Bu fan bo\'yicha darslar hali qo\'shilmagan.': 'Уроки по этому предмету ещё не добавлены.',
    'Fanlarga qaytish': 'Вернуться к предметам', 'Qo\'shimcha, dastur tashqarisidagi darslar': 'Дополнительные уроки вне программы',
    'Bu mavzu hozircha qulflangan': 'Эта тема пока закрыта', 'Avval oldingi mavzuni yakunlang.': 'Сначала завершите предыдущую тему.',
    'Bu mavzu uchun dars matni tayyorlanmoqda.': 'Текст урока для этой темы готовится.',
    'Darsni o\'qib bo\'ldim': 'Я прочитал урок', 'Quizga o\'tish': 'Перейти к тесту', 'Uyga vazifaga o\'tish': 'К домашнему заданию',
    'Uyga vazifa': 'Домашнее задание', 'Uyga vazifa yo\'q': 'Домашнего задания нет', 'Vazifani topshirish': 'Сдать задание',
    'Bu mavzuda qo\'shimcha vazifa berilmagan.': 'В этой теме нет дополнительного задания.',
    'To\'g\'ridan-to\'g\'ri uy vazifasiga o\'tishingiz mumkin.': 'Можно сразу перейти к домашнему заданию.',
    'Bu mavzuda test yo\'q': 'В этой теме нет теста', 'Testni yakunlash': 'Завершить тест', 'Keyingi savol': 'Следующий вопрос',
    'Javobingizni yozing': 'Напишите ваш ответ', 'Bu savolga javob yozing.': 'Напишите ответ на этот вопрос.',
    'Javob juda qisqa — fikringizni bir-ikki gap bilan yozing.': 'Ответ слишком короткий — изложите мысль в одном-двух предложениях.',
    'Javoblar tekshirilmoqda...': 'Ответы проверяются...', 'Javoblaringiz': 'Ваши ответы', 'Javob berilmagan': 'Нет ответа',
    'Javob berilmadi': 'Нет ответа', 'Sizning javobingiz:': 'Ваш ответ:', 'To\'g\'ri javob:': 'Правильный ответ:',
    'Hammasi to\'g\'ri!': 'Всё верно!', 'Ajoyib natija!': 'Отличный результат!', 'Ko\'proq mashq qilish kerak': 'Нужно больше практики',
    'Mavzuni qayta o\'qish': 'Прочитать тему ещё раз', 'Quizni qayta ishlash': 'Пройти тест ещё раз',
    'Keyingi mavzu': 'Следующая тема', 'Bu mavzuni allaqachon yakunlagansiz.': 'Вы уже завершили эту тему.',
    'Mavzular': 'Темы', 'Yakunlash': 'Завершить', 'Tekshirish': 'Проверить',
    'AI yordamida tushuntirish': 'Объяснение с помощью ИИ', 'AI o\'ylayapti...': 'ИИ думает...',
    'Misol ber': 'Приведи пример', 'To\'liqroq tushuntir': 'Объясни подробнее',
    'Bu AI faqat Bilim Premium olgan foydalanuvchilar uchun': 'Этот ИИ доступен только пользователям Bilim Premium',
    'Premium olish': 'Получить Premium', 'Bilim Premium tez orada ishga tushadi': 'Bilim Premium скоро появится',
    'Bu — qo\'shimcha yordam. Rasmiy dars yuqorida turibdi.': 'Это дополнительная помощь. Официальный урок — выше.',
    'Birozdan keyin qayta urinib ko\'ring yoki savolingizni botga yozing.': 'Попробуйте чуть позже или напишите вопрос боту.',
    'Mavzu topilmadi': 'Тема не найдена', 'Mavzu topilmadi.': 'Тема не найдена.', 'Savol topilmadi': 'Вопрос не найден',
    'Bu fan qulflangan. Ochish uchun sotib oling.': 'Этот предмет закрыт. Купите его, чтобы открыть.',
    'Bu mavzu hozircha qulflangan. Avval oldingi mavzuni yakunlang.': 'Эта тема пока закрыта. Сначала завершите предыдущую.',
    'Bu fan topilmadi yoki mavzular hali tayyorlanmagan.': 'Предмет не найден или темы ещё не готовы.',
    'Mavzu ma\'lumoti yetarli emas (grade)': 'Недостаточно данных о теме',
    'Javoblar formati noto\'g\'ri': 'Неверный формат ответов', 'Bu mavzuda uyga vazifa yo\'q': 'В этой теме нет домашнего задания',
    'Ajoyib! Testdan o\'tdingiz.': 'Отлично! Вы прошли тест.',
    'Yana bir bor mavzuni o\'rganib, quizni qayta ishlashingiz mumkin.': 'Можно ещё раз изучить тему и пройти тест снова.',
    'Uyga vazifa qabul qilindi!': 'Домашнее задание принято!',
    'Tabriklaymiz! Mavzuni muvaffaqiyatli yakunladingiz.': 'Поздравляем! Вы успешно завершили тему.',
    'Fan to\'lovdan keyin ochiladi: «Sotib olish» tugmasini bosing.': 'Предмет откроется после оплаты: нажмите «Купить».',
    'Bunday fan mavjud emas': 'Такого предмета нет', 'Fan allaqachon tanlangan, uni o\'zgartirib bo\'lmaydi': 'Предмет уже выбран, изменить его нельзя',
    'Sinf 1 dan 11 gacha bo\'lishi kerak': 'Класс должен быть от 1 до 11',

    // Yakka mashq
    'Yakka mashq': 'Одиночная тренировка', 'O\'qigan darslaringizdan savollar': 'Вопросы из пройденных уроков',
    'Aralash mashq': 'Смешанная тренировка', 'Zaif mavzularingiz bo\'yicha': 'По вашим слабым темам',
    'Javob berish': 'Ответить', 'Qayta o\'ynash': 'Играть снова', 'Savollar tayyorlanmoqda...': 'Вопросы готовятся...',
    'Hali mashq qilinadigan mavzu yo\'q': 'Пока нет тем для практики',
    'Avval kamida bitta darsni o\'qing, keyin shu yerda o\'sha mavzulardan savollar bilan mashq qilasiz.':
      'Сначала прочитайте хотя бы один урок — затем здесь можно будет тренироваться на вопросах по этим темам.',
    'Hozircha zaif mavzu yo\'q': 'Пока нет слабых тем', 'Takrorlanadigan mavzular': 'Темы для повторения',
    'O\'yinlarda qatnashing va dars testlarini ishlang — natijangiz past bo\'lgan mavzular shu yerda takrorlash uchun paydo bo\'ladi.':
      'Участвуйте в играх и проходите тесты — темы с низким результатом появятся здесь для повторения.',
    'Ajoyib mashq bo\'ldi! Yana bir bor sinab ko\'rasizmi?': 'Отличная тренировка! Попробуете ещё раз?',
    'Zaif mavzularni takrorlash': 'Повторить слабые темы', 'Mashq turi': 'Вид тренировки',
    "O'yin": 'Игры', "O'zi yangilanadi": 'Обновляется автоматически',

    // Profil va yutuqlar
    'Yangi nishon': 'Новый значок', 'Yangi nishonlar': 'Новые значки', 'Barcha nishonlar': 'Все значки',
    'hali olinmagan': 'ещё не получен', 'olingan': 'получен', 'Turnir medallari:': 'Медали турниров:',
    'Oltin': 'Золото', 'Kumush': 'Серебро', 'Bronza': 'Бронза', 'Brilyant': 'Бриллиант',
    "Bilim Premium a'zolari uchun maxsus nishon": 'Особый значок для участников Bilim Premium', 'Sevimli fanlar:': 'Любимые предметы:',
    'Sinf ko\'rsatilmagan': 'Класс не указан', 'Hali natija yo\'q': 'Пока нет результатов',
    'Kuchli mavzularingiz': 'Ваши сильные темы', 'Hali yetarli emas': 'Пока недостаточно',
    'Hali nishon yo\'q. Dars o\'qing, o\'yin o\'ynang va': 'Пока нет значков. Читайте уроки, играйте и',
    'kun savoliga javob bering — olingan nishonlar shu yerda paydo bo\'ladi.': 'отвечайте на вопрос дня — полученные значки появятся здесь.',
    'Birinchi qadam': 'Первый шаг', 'Birinchi mavzuni tugatdingiz': 'Вы прошли первую тему', 'Bilim izlovchi': 'Искатель знаний',
    '10 ta mavzu tugatildi': 'Пройдено 10 тем', '50 ta mavzu': '50 тем', '50 ta mavzu tugatildi': 'Пройдено 50 тем',
    'Bilimdon': 'Знаток', '100 ta mavzu tugatildi': 'Пройдено 100 тем', '3 kunlik streak': 'Серия 3 дня',
    '3 kun ketma-ket dars': '3 дня подряд с уроками', '7 kunlik streak': 'Серия 7 дней', '7 kun ketma-ket dars': '7 дней подряд с уроками',
    '30 kunlik streak': 'Серия 30 дней', '30 kun ketma-ket dars': '30 дней подряд с уроками', 'Birinchi o\'yin': 'Первая игра',
    'Birinchi o\'yinni o\'ynadingiz': 'Вы сыграли первую игру', 'Birinchi g\'alaba': 'Первая победа',
    'O\'yinda 1-o\'rinni oldingiz': 'Вы заняли 1-е место в игре', '10 ta g\'alaba': '10 побед',
    'O\'yinlarda 10 marta g\'olib bo\'ldingiz': 'Вы победили в играх 10 раз', 'Kompyuter ustasi': 'Мастер против компьютера',
    'Qiyin darajadagi kompyuterni yutdingiz': 'Вы победили компьютер на сложном уровне', 'Turnir sovrindori': 'Призёр турнира',
    'Haftalik turnirda top-3 ga kirdingiz': 'Вы вошли в топ-3 недельного турнира', 'Turnir g\'olibi': 'Победитель турнира',
    'Haftalik turnirda 1-o\'rin': '1-е место в недельном турнире', 'Birinchi kun savoliga javob berdingiz': 'Вы ответили на первый вопрос дня',
    'Har kuni savol': 'Вопрос каждый день', '7 kun ketma-ket kun savoliga javob': '7 дней подряд отвечали на вопрос дня',
    '500 chaqmoq': '500 молний', 'Jami 500 chaqmoq to\'pladingiz': 'Вы собрали 500 молний',
    'Hammasini ko\'rish': 'Показать все', 'Yig\'ish': 'Свернуть',
    'Nishonlar ro\'yxati noto\'g\'ri.': 'Неверный список значков.', 'Faqat olingan nishonlarni tanlash mumkin.': 'Можно выбрать только полученные значки.',

    // Sozlamalar
    'Profil va ilova sozlamalari': 'Профиль и настройки приложения', 'Rasmni o\'zgartirish': 'Изменить фото',
    'Rasmni o\'chirish': 'Удалить фото', 'Rasm saqlandi': 'Фото сохранено', 'Rasm o\'chirildi': 'Фото удалено',
    'Rasmingiz o\'chirilsinmi?': 'Удалить ваше фото?', 'Rasm faylini tanlang': 'Выберите файл изображения',
    'Bu rasmni ochib bo\'lmadi. Boshqa rasm tanlang.': 'Не удалось открыть это изображение. Выберите другое.',
    'Rasm formati noto\'g\'ri (JPG, PNG yoki WebP bo\'lishi kerak).': 'Неверный формат (нужен JPG, PNG или WebP).',
    'Rasm formati noto\'g\'ri.': 'Неверный формат изображения.', 'Rasm juda katta.': 'Изображение слишком большое.',
    'Ism saqlandi': 'Имя сохранено', 'Reyting, o\'yinlar va kun savolida shu ism ko\'rinadi.': 'Это имя видно в рейтинге, играх и вопросе дня.',
    'Avatar nishonlari': 'Значки у аватара', 'Avatar nishonlari saqlandi': 'Значки у аватара сохранены',
    'Profilda avatar atrofida qaysi nishonlar tursin? 6 tagacha tanlang. Tanlanmasa — eng so\'nggi olinganlari ko\'rinadi.':
      'Какие значки показывать вокруг аватара в профиле? Выберите до 6. Если не выбрать — будут видны последние полученные.',
    'Avtomatik': 'Автоматически', 'Avtomatik tanlashga qaytarish': 'Вернуть автоматический выбор',
    'Avtomatik tanlash yoqildi': 'Автоматический выбор включён', 'Bildirishnomalar': 'Уведомления',
    'Telegram eslatmalari': 'Напоминания в Telegram',
    'Kun savoli, kunlik eslatma, yangi mavzu ochilishi, o\'yin takliflari': 'Вопрос дня, ежедневное напоминание, открытие новой темы, приглашения в игры',
    'Eslatma vaqti': 'Время напоминания', 'Kunlik dars eslatmasi shu vaqtda keladi': 'Ежедневное напоминание об уроке придёт в это время',
    'Eslatmalar faqat BilimSari\'ga Telegram orqali kirganlarga yuboriladi.': 'Напоминания приходят только тем, кто вошёл в BilimSari через Telegram.',
    'Eslatmalar yoqildi': 'Напоминания включены', 'Eslatmalar o\'chirildi': 'Напоминания выключены', 'Sozlamalar saqlandi': 'Настройки сохранены',
    'To\'lovlarim': 'Мои платежи', 'Do\'stlarni taklif qilish': 'Пригласить друзей',
    'BilimSari havolasini do\'stlaringizga yuboring': 'Отправьте друзьям ссылку на BilimSari',
    'Til': 'Язык',
    "BilimSari'da maktab fanlarini o'rganyapman: darslar, o'yinlar va kun savoli. Sen ham qo'shil!":
      'Я изучаю школьные предметы в BilimSari: уроки, игры и вопрос дня. Присоединяйся!',
    'BilimSari kun savoli — bugun men adashdim. Sen yecha olasanmi?': 'Вопрос дня BilimSari — сегодня я ошибся. А ты решишь?', 'Interfeys tili': 'Язык интерфейса', 'Darslar o\'zbek tilida qoladi': 'Уроки остаются на узбекском языке',
    'Soat 07:00 dan 22:00 gacha bo\'lishi kerak.': 'Время должно быть с 07:00 до 22:00.',
    'Ismingizni yozing (kamida 2 ta harf)': 'Напишите имя (минимум 2 буквы)',
    "Til noto'g'ri tanlangan.": 'Неверно выбран язык.',

    // Do'kon va to'lov
    'Fan sotib olish ›': 'Купить предмет ›', 'Sotib olish': 'Купить', 'Sotib olmoqchi bo\'lgan fanlarni tanlang.': 'Выберите предметы, которые хотите купить.',
    'Hammasini tanlash': 'Выбрать все', 'Karta orqali to\'lov': 'Оплата картой',
    'Kartaga o\'tkazasiz, chek rasmini botga yuborasiz — admin tasdiqlagach fan ochiladi.':
      'Переводите на карту, отправляете фото чека боту — после подтверждения админом предмет откроется.',
    'Karta orqali to\'lash': 'Оплатить картой',
    'qo\'llandi': 'применён', 'Promo-kod qo\'llandi': 'Промокод применён',
    'Havola orqali kelgan promo-kod avtomatik qo\'llandi.': 'Промокод из ссылки применён автоматически.',
    'Promo-kod': 'Промокод', 'Promo-kod (ixtiyoriy)': 'Промокод', 'Paketlar arzonroq:': 'Пакеты дешевле:',
    'Botga karta raqami keladi': 'Бот пришлёт номер карты', 'To\'lab, chekni botga yuboring': 'Оплатите и отправьте чек боту',
    'Admin tasdiqlaydi': 'Админ подтверждает', 'Qanday ishlaydi': 'Как это работает',
    'Buyurtma': 'Заказ', 'Buyurtma yaratildi': 'Заказ создан', 'Buyurtma bekor qilindi': 'Заказ отменён',
    'Buyurtma bekor qilinsinmi?': 'Отменить заказ?', 'Chek kutilmoqda': 'Ожидается чек', 'Chekingiz tekshirilmoqda ⏳': 'Ваш чек проверяется ⏳',
    'Tasdiqlangan': 'Подтверждён', 'Rad etilgan': 'Отклонён', 'Muddati tugagan': 'Срок истёк', 'To\'lov rad etildi': 'Платёж отклонён',
    'To\'lov qabul qilindi!': 'Платёж принят!', 'Fan(lar) ochildi. O\'qishda omad!': 'Предмет(ы) открыт(ы). Удачи в учёбе!',
    'To\'lov amalga oshmadi. Qayta urinib ko\'ring.': 'Платёж не прошёл. Попробуйте ещё раз.',
    'To\'lov vaqtincha ishlamayapti': 'Оплата временно не работает', 'Hozircha to\'lov usuli mavjud emas.': 'Пока нет доступного способа оплаты.',
    'To\'lov Telegram orqali': 'Оплата через Telegram', 'Karta raqami kiritilmagan': 'Номер карты не указан', 'Kartani kiritish': 'Указать карту',
    'Siz adminsiz. O\'quvchilar to\'lov qila olishi uchun karta raqamini kiriting — u botda o\'quvchiga ko\'rsatiladi.':
      'Вы админ. Укажите номер карты, чтобы ученики могли оплачивать — бот покажет его ученику.',
    'Karta raqami botga yuborilgan. To\'lab, chek rasmini botga yuboring.': 'Номер карты отправлен в бот. Оплатите и отправьте фото чека боту.',
    'Botda karta raqami bor: to\'lovni qiling va chek rasmini botga yuboring. Admin tasdiqlagach fan ochiladi.':
      'В боте есть номер карты: оплатите и отправьте фото чека боту. После подтверждения админом предмет откроется.',
    'Bot sizga yoza olmadi. Botni oching va «Start» tugmasini bosing — yo\'riqnoma keladi.': 'Бот не смог вам написать. Откройте бота и нажмите «Start» — придёт инструкция.',
    'Yo\'riqnoma botga yuborildi!': 'Инструкция отправлена в бот!',
    'Odatda 5–30 daqiqa. Tasdiqlangach fan ochiladi va botga xabar keladi.': 'Обычно 5–30 минут. После подтверждения предмет откроется, а бот пришлёт сообщение.',
    'Fan sotib olish uchun BilimSari\'ni Telegram botdan oching — to\'lov bot chatida amalga oshiriladi.':
      'Чтобы купить предмет, откройте BilimSari через Telegram-бота — оплата проходит в чате бота.',
    'Barcha fanlar ochiq!': 'Все предметы открыты!', 'Sizda sotib olinadigan fan qolmadi. O\'qishda omad!': 'Предметов для покупки не осталось. Удачи в учёбе!',
    'Barcha fanlar': 'Все предметы', 'Kamida bitta fan tanlang.': 'Выберите хотя бы один предмет.',
    'Tanlangan fan allaqachon ochiq yoki mavjud emas.': 'Выбранный предмет уже открыт или недоступен.',
    'Bunday promo-kod yo\'q.': 'Такого промокода нет.', 'Promo-kod muddati tugagan.': 'Срок промокода истёк.',
    'Promo-kod limiti tugagan.': 'Лимит промокода исчерпан.', 'Siz bu promo-koddan allaqachon foydalangansiz.': 'Вы уже использовали этот промокод.',
    'Bu buyurtmani bekor qilib bo\'lmaydi.': 'Этот заказ нельзя отменить.', 'Promo-kod topilmadi': 'Промокод не найден',
    "O'zingizning hamkorlik kodingizdan foydalana olmaysiz — uni do'stlaringizga ulashing.":
      'Нельзя использовать собственный партнёрский промокод — поделитесь им с друзьями.',
    'Juda ko\'p urinish. Birozdan keyin qayta urinib ko\'ring.': 'Слишком много попыток. Попробуйте чуть позже.',
    'Juda ko\'p urinish. Birozdan so\'ng qayta urinib ko\'ring.': 'Слишком много попыток. Попробуйте чуть позже.',
    'Avtorizatsiya talab qilinadi': 'Требуется авторизация',

    // O'yinlar
    'O\'yinlar markazi': 'Игровой центр', 'Do\'stlaringiz bilan bilim bellashing': 'Соревнуйтесь в знаниях с друзьями',
    'Faol roomlar': 'Активные комнаты', 'Hozircha faol room yo\'q': 'Пока нет активных комнат',
    'Room yarating — u shu ro\'yxatda hamma uchun darhol ko\'rinadi.': 'Создайте комнату — она сразу появится в этом списке для всех.',
    'Room yaratish': 'Создать комнату', 'Roomga qo\'shilish': 'Войти в комнату', 'Qo\'shilish': 'Войти', 'O\'yin yaratish': 'Создать игру',
    'Room kodi': 'Код комнаты', 'Do\'stingiz yuborgan 6 belgili kodni kiriting.': 'Введите 6-символьный код, который прислал друг.',
    'Kod 6 ta harf va raqamdan iborat bo\'ladi.': 'Код состоит из 6 букв и цифр.', 'Room kodi noto\'g\'ri': 'Неверный код комнаты',
    'Room topilmadi': 'Комната не найдена', 'Room to\'liq': 'Комната заполнена', 'Room yopilgan': 'Комната закрыта',
    'Roomning muddati tugagan': 'Срок комнаты истёк', 'Siz bu roomda emassiz': 'Вы не в этой комнате', 'Siz roomdan chiqarildingiz': 'Вас удалили из комнаты',
    'Room sozlamalari': 'Настройки комнаты', 'Room tayyorlanmoqda...': 'Комната готовится...', 'O\'yin tayyorlanmoqda...': 'Игра готовится...',
    'Room uzoq vaqt harakatsiz qoldi. Yangi room yarating.': 'Комната долго была неактивной. Создайте новую.',
    'Room “Faol roomlar” ro\'yxatida hamma uchun darhol ko\'rinadi. Do\'stingizni room ichidagi “Do\'st taklif qilish” tugmasi orqali chaqirasiz.':
      'Комната сразу появится в списке «Активные комнаты» для всех. Пригласить друга можно кнопкой «Пригласить друга» внутри комнаты.',
    'Fan tanlang': 'Выберите предмет', 'Qiyinlik': 'Сложность', 'Oson': 'Лёгкий', 'O\'rta': 'Средний', 'Qiyin': 'Сложный',
    'Savollar soni': 'Количество вопросов', 'Raundlar soni': 'Количество раундов', 'O\'yinchilar soni': 'Количество игроков',
    'O\'yinchilar': 'Игроки', 'O\'yinchilar (room uchun)': 'Игроки (для комнаты)', 'Barcha mavzular (aralash)': 'Все темы (вперемешку)',
    'Kompyuter raqib': 'Компьютер-соперник', 'Kompyuter qo\'shish': 'Добавить компьютер', 'Kompyuter darajasi': 'Уровень компьютера',
    'Kompyuter raqib hamma bilan birga javob beradi. Uning javoblari va ballari ham server tomonidan hisoblanadi.':
      'Компьютер отвечает вместе со всеми. Его ответы и очки тоже считает сервер.',
    'Do\'st taklif qilish': 'Пригласить друга', 'Do\'stingizni taklif qiling': 'Пригласите друга', 'Havolani nusxalash': 'Скопировать ссылку',
    'Kodni nusxalash': 'Скопировать код', 'Telegram orqali yuborish': 'Отправить через Telegram',
    'Do\'stingiz havolani ochsa, shu roomga kiradi. Yoki O\'yinlar bo\'limida “Roomga qo\'shilish” tugmasini bosib, kodni kiritadi.':
      'Если друг откроет ссылку, он попадёт в эту комнату. Или в разделе «Игры» нажмёт «Войти в комнату» и введёт код.',
    '. Top-3 medal oladi.': '. Топ-3 получат медали.', 'Bu fan qulflangan': 'Этот предмет закрыт',
    'Tayyorman': 'Я готов', 'Tayyorsiz — bekor qilish': 'Вы готовы — отменить', 'Tayyor bo\'lsangiz, tugmani bosing': 'Если готовы, нажмите кнопку',
    'Hamma tayyor — boshlashingiz mumkin!': 'Все готовы — можно начинать!', 'Host o\'yinni boshlashini kuting': 'Дождитесь, пока хост начнёт игру',
    'O\'yinni boshlash': 'Начать игру', 'O\'yin boshlanmoqda': 'Игра начинается', 'Raqib topildi!': 'Соперник найден!',
    'Roomdan chiqasizmi?': 'Выйти из комнаты?', 'O\'yinchini chiqarish': 'Удалить игрока', 'Bo\'sh joy': 'Свободное место',
    'Kamida 2 o\'yinchi kerak — do\'stingizni taklif qiling yoki kompyuter qo\'shing.': 'Нужно минимум 2 игрока — пригласите друга или добавьте компьютер.',
    'O\'yin allaqachon boshlangan': 'Игра уже началась', 'Hamma o\'yinchilar roomdan chiqib ketdi.': 'Все игроки вышли из комнаты.',
    'O\'yinni tark etasizmi? Hozirgi natijangiz saqlanadi, lekin bonuslar berilmaydi.': 'Покинуть игру? Текущий результат сохранится, но бонусы не начислятся.',
    'Raqiblar chiqib ketgani uchun o\'yin muddatidan oldin yakunlandi.': 'Игра завершилась досрочно, потому что соперники вышли.',
    'Siz bu o\'yinda qatnashmadingiz. Host yangi o\'yin boshlashini kuting.': 'Вы не участвовали в этой игре. Дождитесь, пока хост начнёт новую.',
    'Host yangi o\'yin boshlasa, shu yerda qolasiz.': 'Если хост начнёт новую игру, вы останетесь здесь.',
    'O\'yin natijasi': 'Результат игры', 'G\'alaba': 'Победы', 'G\'alaba! Siz 1-o\'rindasiz': 'Победа! Вы на 1-м месте',
    'Nimalarni o\'rgandingiz?': 'Чему вы научились?', 'Savollarni ko\'rib chiqish': 'Просмотреть вопросы',
    'Yana o\'ynash': 'Играть ещё', 'O\'yinlar markaziga qaytish': 'Вернуться в игровой центр', 'Shu savolda ball olganlar': 'Получили очки за этот вопрос',
    'sekinroq bo\'ldi': 'чуть медленнее', 'Aniqlik': 'Точность', 'O\'yin reytingi': 'Игровой рейтинг', 'Haftalik turnir': 'Недельный турнир',
    'O\'tgan hafta:': 'Прошлая неделя:', 'Chaqmoq bo\'yicha eng faol o\'quvchilar': 'Самые активные ученики по молниям',
    'O\'yinlarda hisobga o\'tgan ball bo\'yicha. Har 10 ball — 1 chaqmoq.': 'По засчитанным в играх очкам. Каждые 10 очков — 1 молния.',
    'Chaqmoq kamida 2 o\'yinchi qatnashgan o\'yinlarda beriladi.': 'Молнии даются в играх, где участвовало минимум 2 игрока.',
    'Sinfim bo\'yicha': 'По моему классу', 'Fan bo\'yicha': 'По предмету', 'Reyting hali bo\'sh': 'Рейтинг пока пуст',
    'Bu davrda hali hech kim o\'ynamagan. Birinchi bo\'ling — o\'yin tanlang!': 'В этот период ещё никто не играл. Будьте первым — выберите игру!',
    'Hali o\'yin o\'ynamagansiz. Do\'stlaringiz bilan bilim bellashuvida ball va chaqmoq to\'plang!':
      'Вы ещё не играли. Собирайте очки и молнии в соревнованиях с друзьями!',
    'Avval chapdagi savolni, keyin unga mos javobni bosing. Juftlikni bekor qilish uchun uni qayta bosing.':
      'Сначала нажмите вопрос слева, затем подходящий ответ. Чтобы отменить пару, нажмите её ещё раз.',
    'Har bir savolni to\'g\'ri javobi bilan moslang': 'Сопоставьте каждый вопрос с правильным ответом',
    'O\'yin fayli yuklanmadi.': 'Файл игры не загрузился.', 'O\'yin fayllari yuklanmadi. Internetni tekshiring.': 'Файлы игры не загрузились. Проверьте интернет.',
    'Bilimingni boshqa o\'quvchilar bilan sinab ko\'r.': 'Проверь свои знания вместе с другими учениками.',
    'Hamma bir xil savolga javob beradi. To\'g\'ri javob +10 ball, tez javob yana +5.': 'Все отвечают на один и тот же вопрос. Правильный ответ +10 очков, быстрый — ещё +5.',
    'Kim birinchi to\'g\'ri javob bersa — ball o\'shaniki.': 'Кто первым ответит правильно — тому и очки.',
    'Savolga birinchi bo\'lib to\'g\'ri javob bergan o\'yinchi ballni oladi. Har savolga bitta urinish.':
      'Очки получает игрок, первым ответивший правильно. На каждый вопрос одна попытка.',
    'Sinonim, antonim, tarjima va imlo bellashuvi.': 'Соревнование в синонимах, антонимах, переводе и орфографии.',
    'So\'z boyligingizni sinang: ma\'nodosh va zid so\'zlar, tarjima va to\'g\'ri yozilish.': 'Проверьте словарный запас: синонимы и антонимы, перевод и правописание.',
    'Misollarni imkon qadar tez va to\'g\'ri yeching.': 'Решайте примеры как можно быстрее и правильнее.',
    'Har o\'yinda yangi misollar. Og\'zaki hisoblash tezligingizni oshiring.': 'В каждой игре новые примеры. Развивайте скорость устного счёта.',
    'HTML, CSS, JavaScript, Python va algoritmlar.': 'HTML, CSS, JavaScript, Python и алгоритмы.',
    'Boshlang\'ich dasturlash savollari: kod natijasini toping, to\'g\'ri tegni tanlang.': 'Вопросы по основам программирования: найдите результат кода, выберите правильный тег.',
    'Savol va javoblarni juftlab moslang.': 'Сопоставьте вопросы и ответы попарно.',
    'Har raundda 4 ta savolni to\'g\'ri javobi bilan moslang. Hammasi to\'g\'ri bo\'lsa +10 ball.': 'В каждом раунде сопоставьте 4 вопроса с правильными ответами. Всё верно — +10 очков.',
    'Qo\'shish va ayirish': 'Сложение и вычитание', 'Ko\'paytirish': 'Умножение', 'Bo\'lish': 'Деление', 'Kasrlar': 'Дроби',
    'Foizlar': 'Проценты', 'Darajalar va ildizlar': 'Степени и корни', 'Algoritmlar': 'Алгоритмы', 'Sinonimlar': 'Синонимы',
    'Antonimlar': 'Антонимы', 'Tarjima': 'Перевод', 'Sinonimlar (synonyms)': 'Синонимы (synonyms)', 'Antonimlar (antonyms)': 'Антонимы (antonyms)',
    'To\'g\'ri yozilish (spelling)': 'Правописание (spelling)',
    // O'yin xatolari (server)
    'Juda ko\'p room yaratildi. Birozdan so\'ng urinib ko\'ring.': 'Создано слишком много комнат. Попробуйте чуть позже.',
    'O\'yin yoki fan noto\'g\'ri tanlangan.': 'Неверно выбрана игра или предмет.', 'Juda ko\'p qidiruv. Birozdan so\'ng urinib ko\'ring.': 'Слишком много поисков. Попробуйте чуть позже.',
    'Serverda xatolik yuz berdi. Birozdan so\'ng qayta urinib ko\'ring.': 'На сервере произошла ошибка. Попробуйте чуть позже.',
    'Room yaratib bo\'lmadi. Qayta urinib ko\'ring.': 'Не удалось создать комнату. Попробуйте ещё раз.', 'Bu room yopilgan.': 'Эта комната закрыта.',
    'Room kodi 6 ta harf va raqamdan iborat bo\'ladi.': 'Код комнаты состоит из 6 букв и цифр.',
    'Room topilmadi. Kodni tekshirib, qayta kiriting.': 'Комната не найдена. Проверьте код и введите снова.',
    'Bu roomning muddati tugagan. Yangi room yarating.': 'Срок этой комнаты истёк. Создайте новую.', 'Host sizni bu roomdan chiqargan.': 'Хост удалил вас из этой комнаты.',
    'Bu roomda o\'yin allaqachon boshlangan.': 'В этой комнате игра уже началась.', 'Bu room to\'liq.': 'Эта комната заполнена.',
    'Siz bu roomda emassiz. Kod orqali qayta qo\'shiling.': 'Вы не в этой комнате. Войдите снова по коду.',
    'Buni faqat room egasi (host) qila oladi.': 'Это может сделать только владелец комнаты (хост).',
    'Bu amal faqat o\'yin boshlanishidan oldin mumkin.': 'Это можно сделать только до начала игры.', 'Roomda o\'yinchilar bu limitdan ko\'p.': 'В комнате больше игроков, чем этот лимит.',
    'Kompyuter darajasi noto\'g\'ri.': 'Неверный уровень компьютера.', 'Roomda bo\'sh joy yo\'q. O\'yinchilar sonini sozlamalarda oshiring.': 'В комнате нет мест. Увеличьте число игроков в настройках.',
    'O\'yin davomida o\'yinchini chiqarib bo\'lmaydi.': 'Во время игры нельзя удалить игрока.', 'O\'yinchi topilmadi.': 'Игрок не найден.',
    'O\'zingizni chiqara olmaysiz.': 'Нельзя удалить самого себя.', 'O\'yin hozir davom etmayapti.': 'Игра сейчас не идёт.',
    'Yangi o\'yinni faqat oldingisi tugagach boshlash mumkin.': 'Новую игру можно начать только после окончания предыдущей.',
    'Bu sozlamalar uchun savol topilmadi. Boshqa fan yoki mavzuni tanlang.': 'Для этих настроек нет вопросов. Выберите другой предмет или тему.',
    'Bu savolning vaqti tugadi.': 'Время на этот вопрос вышло.', 'Siz bu savolga javob bergansiz.': 'Вы уже ответили на этот вопрос.',
    'O\'yin savollar boshlanishidan oldin tugadi.': 'Игра закончилась до начала вопросов.', 'Savol raqami noto\'g\'ri.': 'Неверный номер вопроса.',
    'Bunday o\'yin topilmadi.': 'Такая игра не найдена.', 'Bu o\'yin uchun fan noto\'g\'ri tanlangan.': 'Для этой игры неверно выбран предмет.',
    'Qiyinlik darajasi noto\'g\'ri.': 'Неверный уровень сложности.', 'Savollar soni noto\'g\'ri.': 'Неверное количество вопросов.',
    'O\'yinchilar soni 2, 4, 8 yoki 16 bo\'lishi mumkin.': 'Количество игроков может быть 2, 4, 8 или 16.',
    'Sinfingiz ko\'rsatilmagan — bu reyting hozircha bo\'sh.': 'Ваш класс не указан — этот рейтинг пока пуст.',
    'O\'yinchi': 'Игрок', 'Kompyuter': 'Компьютер',
    // Bilim Premium
    'Bilim Premium': 'Bilim Premium', 'Bilim Premium (1 oy)': 'Bilim Premium (1 мес.)', 'Bilim Premium (1 oy) •': 'Bilim Premium (1 мес.) •',
    'AI, shaxsiy darslar, emoji va oltin halqa': 'ИИ, личные уроки, эмодзи и золотое кольцо',
    'AI, shaxsiy darslar, emoji va avatar ramkasi': 'ИИ, личные уроки, эмодзи и рамка аватара',
    'Avatar ramkasi': 'Рамка аватара', 'Oltin chaqmoq': 'Золотая молния', "Ko'k chaqmoq": 'Синяя молния',
    'Yashil chaqmoq': 'Зелёная молния', 'Binafsha chaqmoq': 'Фиолетовая молния', 'Qizil chaqmoq': 'Красная молния',
    'Oq chaqmoq': 'Белая молния', 'Ramka saqlandi': 'Рамка сохранена',
    "Tanlagan ramkangiz profil, reyting va o'yinlarda avataringiz atrofida ko'rinadi.":
      'Выбранная рамка видна вокруг аватара в профиле, рейтинге и играх.',
    "Ramka faqat Bilim Premium bilan ishlaydi.": 'Рамка доступна только с Bilim Premium.',
    "O'qishni yanada qiziqarli va samarali qiladigan imkoniyatlar.": 'Возможности, которые делают учёбу интереснее и эффективнее.',
    'Premium faol —': 'Premium активен — до', 'Premium faol': 'Premium активен',
    'AI tushuntirish': 'Объяснение от ИИ',
    "Har bir darsda AI mavzuni to'liqroq tushuntiradi va yangi misollar bilan qadam-baqadam yechib beradi.":
      'На каждом уроке ИИ подробнее объяснит тему и разберёт новые примеры шаг за шагом.',
    'Shaxsiy darslar': 'Личные уроки', 'Shaxsiy darslarim': 'Мои личные уроки', 'Shaxsiy dars': 'Личный урок', 'Shaxsiy': 'Личные',
    "O'zingizda ochiq fanlardan istalgan mavzuni yozing — AI siz uchun dars, 3 savolli test va uy vazifasini tayyorlaydi. Har 24 soatda bitta yangi dars yaratiladi, o'qish esa cheksiz. Darslar faqat sizga ko'rinadi va Premium tugasa ham o'zingizda qoladi.":
      'Напишите любую тему по вашим открытым предметам — ИИ подготовит для вас урок, тест из 3 вопросов и домашнее задание. Новый урок можно создавать раз в 24 часа, а заниматься — без ограничений. Уроки видите только вы, и они останутся у вас даже после окончания Premium.',
    'Ism yonida emoji': 'Эмодзи рядом с именем', 'Ism yonidagi emoji': 'Эмодзи рядом с именем',
    'Oltin halqa': 'Золотое кольцо',
    "Avataringiz atrofida oltin halqa paydo bo'ladi — hamma sizni Premium o'quvchi ekaningizni ko'radi.":
      'Вокруг аватара появится золотое кольцо — все увидят, что вы ученик с Premium.',
    "Premium fanlarni ochmaydi — fanlar Do'konda alohida sotiladi. Muddat 1 oy; tugagach, qayta olish mumkin.":
      'Premium не открывает предметы — они продаются отдельно в Магазине. Срок — 1 месяц; после окончания можно купить снова.',
    "Odatda 5–30 daqiqa. Tasdiqlangach Premium faollashadi va botga xabar keladi.":
      'Обычно 5–30 минут. После подтверждения Premium активируется, а бот пришлёт сообщение.',
    'Emoji tanlash': 'Выбрать эмодзи',
    "Muddati tugagach, shu yerdan yana 1 oyga olishingiz mumkin.": 'Когда срок закончится, здесь можно купить ещё на 1 месяц.',
    "Premium olish uchun BilimSari'ni Telegram botdan oching — to'lov bot chatida amalga oshiriladi.":
      'Чтобы купить Premium, откройте BilimSari через Telegram-бота — оплата проходит в чате бота.',
    "Kartaga o'tkazasiz, chek rasmini botga yuborasiz — admin tasdiqlagach Premium faollashadi.":
      'Переводите на карту, отправляете фото чека боту — после подтверждения админом Premium активируется.',
    "Fan uchun ochiq buyurtmangiz bor — Premium olsangiz, u bekor qilinadi.": 'У вас есть открытый заказ на предмет — если купите Premium, он отменится.',
    "Botda karta raqami bor: to'lovni qiling va chek rasmini botga yuboring. Admin tasdiqlagach Premium faollashadi.":
      'В боте есть номер карты: оплатите и отправьте фото чека боту. После подтверждения админом Premium активируется.',
    'Bilim Premium faollashmoqda...': 'Bilim Premium активируется...', 'Premium faollashdi! Omad!': 'Premium активирован! Удачи!',

    // Boshqa o'quvchi profili
    "O'quvchi profili": 'Профиль ученика', "Reytingdagi o'rin": 'Место в рейтинге', 'Kunlik streak': 'Серия дней',
    'Tugatilgan mavzular': 'Пройдено тем', "Hali o'yin o'ynamagan.": 'Пока не играл.', 'Hali nishon olmagan.': 'Пока нет значков.',
    "O'quvchi topilmadi": 'Ученик не найден', "Bu o'quvchi ilovadan o'chirilgan bo'lishi mumkin.": 'Возможно, ученик удалён из приложения.',
    "Bunday o'quvchi topilmadi.": 'Такой ученик не найден.', "To'liq profil": 'Полный профиль', "O'rin": 'Место', 'Mavzu': 'Тем',
    'Streak': 'Серия',
    // Pastki "Menyu"
    'Menyu': 'Меню', 'Biz haqimizda': 'О нас', "Kanal havolasi tez orada qo'shiladi.":'Ссылка на канал скоро появится.',
    // Hamkorlik (sahifa)
    'Promo-kodingiz, sotuvlar va daromad': 'Ваш промокод, продажи и доход', 'Kod': 'Код',
    'Siz hali hamkor emassiz': 'Вы пока не партнёр',
    "Hamkorlik dasturi admin tanlagan o'quvchilar uchun: o'z promo-kodingiz orqali qilingan har bir xariddan foiz olasiz. Qiziqsangiz, botga yozing.":
      'Партнёрская программа — для учеников, выбранных админом: вы получаете процент с каждой покупки по вашему промокоду. Если интересно, напишите боту.',
    'Hamkorlik': 'Партнёрство', 'Faol': 'Активен', 'To\'xtatilgan': 'Приостановлен', 'Promo-kodingiz': 'Ваш промокод',
    'Sizga:': 'Вам:', 'Do\'stingizga:': 'Другу:', 'Har bir xariddan': 'С каждой покупки',
    'Kodingiz vaqtincha to\'xtatilgan. Savolingiz bo\'lsa, botga yozing.': 'Ваш код временно приостановлен. Если есть вопросы, напишите боту.',
    'Sotuvlar': 'Продажи', 'Jami ishlangan': 'Всего заработано', 'To\'langan': 'Выплачено', 'To\'lanishi kerak': 'К выплате',
    'Ulashish': 'Поделиться', 'Nusxa olish': 'Копировать', 'Nusxa olindi': 'Скопировано', 'Nusxa olib bo\'lmadi': 'Не удалось скопировать',
    'Oxirgi sotuvlar': 'Последние продажи', 'Sizga to\'langan': 'Выплачено вам',
    'Hali sotuv yo\'q. Kodingizni do\'stlaringiz va tanishlaringizga ulashing!': 'Продаж пока нет. Поделитесь кодом с друзьями и знакомыми!',
    'Komissiya do\'stingiz kodingiz bilan xarid qilib, admin to\'lovni tasdiqlaganda yoziladi. Pulni admin o\'zi o\'tkazib beradi — har bir sotuv va to\'lov haqida botga xabar keladi.':
      'Комиссия начисляется, когда друг покупает с вашим кодом и админ подтверждает оплату. Деньги переводит админ — о каждой продаже и выплате бот пришлёт сообщение.',
    "Premium hali faol — muddati tugagach qayta olish mumkin.": 'Premium ещё активен — купить снова можно после окончания срока.',
    'AI tushuntirish faqat Bilim Premium bilan ishlaydi.': 'Объяснение от ИИ доступно только с Bilim Premium.',
    'Emoji faqat Bilim Premium bilan ishlaydi.': 'Эмодзи доступны только с Bilim Premium.', "Bunday emoji yo'q.": 'Такого эмодзи нет.',
    "Tanlaganingiz ismingiz yonida hamma joyda ko'rinadi.": 'Выбранное эмодзи будет видно рядом с вашим именем везде.',
    "Emoji'ni olib tashlash": 'Убрать эмодзи', 'Emoji saqlandi': 'Эмодзи сохранено',
    // Shaxsiy darslar
    'AI siz uchun tayyorlagan darslar': 'Уроки, которые ИИ подготовил для вас',
    'Shaxsiy darslar — Bilim Premium imkoniyati': 'Личные уроки — возможность Bilim Premium',
    "O'zingizda ochiq fanlardan istalgan mavzuni yozing — AI siz uchun dars, test va uy vazifasini tayyorlaydi.":
      'Напишите любую тему по вашим открытым предметам — ИИ подготовит для вас урок, тест и домашнее задание.',
    "Odatda 1 daqiqagacha. Tayyor bo'lgach ilovada va botda xabar beramiz.": 'Обычно до 1 минуты. Когда будет готово, сообщим в приложении и в боте.',
    'Yangi dars yaratish': 'Создать новый урок',
    'Har 24 soatda bitta shaxsiy dars yaratiladi. Keyingisi:': 'Новый личный урок можно создавать раз в 24 часа. Следующий через:',
    "Ochiq fan yo'q": 'Нет открытых предметов', 'Avval fan tanlang yoki sotib oling.': 'Сначала выберите или купите предмет.',
    "Fanni tanlang va o'rganmoqchi bo'lgan mavzuingiz nomini yozing — AI siz uchun dars tayyorlaydi.":
      'Выберите предмет и напишите тему, которую хотите изучить, — ИИ подготовит для вас урок.',
    '1. Fan': '1. Предмет', '2. Mavzu nomi': '2. Название темы', '3. Qaysi birini nazarda tutdingiz?': '3. Что вы имели в виду?',
    "Masalan: kasrlarni qo'shish": 'Например: сложение дробей', "Yo'q, bularning hech biri emas": 'Нет, ни один не подходит',
    'Mavzu nomini qaytadan, aniqroq yozing.': 'Напишите название темы ещё раз, точнее.',
    "Dars tayyorlanmoqda — tayyor bo'lgach xabar beramiz": 'Урок готовится — сообщим, когда будет готово',
    "Hali shaxsiy dars yo'q. Birinchisini yuqorida yarating!": 'Личных уроков пока нет. Создайте первый выше!',
    'Tayyorlanmoqda...': 'Готовится...', 'Dars tayyorlanmoqda': 'Урок готовится', 'Dars topilmadi': 'Урок не найден',
    'Dars topilmadi.': 'Урок не найден.', "Dars hali tayyorlanmoqda. Tayyor bo'lgach xabar beramiz.": 'Урок ещё готовится. Сообщим, когда будет готово.',
    'Chaqmoq faqat birinchi urinishda beriladi.': 'Молнии даются только за первую попытку.',
    "Javob noto'g'ri — qayta urinib ko'ring.": 'Неверный ответ — попробуйте ещё раз.',
    'Shaxsiy darslar faqat Bilim Premium bilan yaratiladi.': 'Личные уроки можно создавать только с Bilim Premium.',
    "Faqat o'zingizda ochiq fanlar uchun dars yaratish mumkin.": 'Уроки можно создавать только по вашим открытым предметам.',
    "AI hozir javob bermadi. Birozdan keyin qayta urinib ko'ring.": 'ИИ сейчас не ответил. Попробуйте чуть позже.',
    'Mavzu nomini tanlang.': 'Выберите название темы.',
    "Bitta dars allaqachon tayyorlanmoqda. Tayyor bo'lishini kuting.": 'Один урок уже готовится. Дождитесь, пока он будет готов.',
    'Darslar': 'Уроки', "Testda har to'g'ri javob +5 (1-urinish), uy vazifasi +15": 'В тесте +5 за верный ответ (1-я попытка), домашка +15',

    // Do'stlar
    "Do'stlar": 'Друзья', "Do'stlar, so'rovlar va qidiruv": 'Друзья, заявки и поиск', "So'rovlar": 'Заявки',
    "Do'st qo'shish": 'Добавить друга', 'Faollik': 'Активность', "Do'stlar bo'limlari": 'Разделы «Друзья»',
    "Hali do'stingiz yo'q": 'У вас пока нет друзей',
    "Tanishlaringizni ismi, @username yoki ID raqami bilan toping va so'rov yuboring.":
      'Найдите знакомых по имени, @username или ID и отправьте заявку.',
    "Do'stlikdan chiqarish": 'Удалить из друзей', "Do'stlikdan chiqarilsinmi?": 'Удалить из друзей?',
    "Do'stlikdan chiqarildi": 'Удалён из друзей', "Kelgan so'rovlar": 'Входящие заявки', 'Qabul': 'Принять', 'Rad': 'Отклонить',
    "Yangi so'rov yo'q.": 'Новых заявок нет.', 'Siz yuborgan': 'Отправленные', 'javob kutilmoqda': 'ожидает ответа',
    "Javob kutilayotgan so'rov yo'q.": 'Нет заявок, ожидающих ответа.', "Endi do'stsiz!": 'Теперь вы друзья!',
    "So'rov rad etildi": 'Заявка отклонена', "So'rov yuborildi": 'Заявка отправлена', "So'rov bekor qilindi": 'Заявка отменена',
    "Do'stingiz": 'Ваш друг', 'Qabul qilish': 'Принять', 'Rad etish': 'Отклонить',
    'Ism, @username yoki ID': 'Имя, @username или ID', 'Masalan:': 'Например:', 'yoki': 'или',
    "(ID raqami profil havolasida bo'ladi).": '(ID указан в ссылке на профиль).', 'Hech kim topilmadi.': 'Никого не найдено.',
    "Reyting uchun do'st kerak": 'Для рейтинга нужны друзья',
    "Do'st qo'shing — kim ko'proq chaqmoq to'plashini birga kuzatasiz.": 'Добавьте друзей — и следите вместе, кто соберёт больше молний.',
    "Siz va do'stlaringiz — chaqmoq bo'yicha": 'Вы и ваши друзья — по молниям',
    "Hozircha yangilik yo'q": 'Пока новостей нет',
    "Do'stlaringiz mavzu tugatsa, nishon olsa yoki o'yinda g'olib bo'lsa — shu yerda ko'rinadi.":
      'Когда друзья завершат тему, получат значок или победят в игре — это появится здесь.',
    "bilim bellashuvida g'olib bo'ldi": 'победил(а) в игре знаний', "kun savoliga to'g'ri javob berdi": 'верно ответил(а) на вопрос дня',
    "Qo'shilish": 'Присоединиться', 'hozirgina': 'только что', 'kecha': 'вчера',
    'Sizni chaqirishdi': 'Вас зовут в игру', 'Keyinroq': 'Позже',
    "Internet aloqasi yo'q. Ulanishni tekshiring.": 'Нет подключения к интернету. Проверьте соединение.',
    // Admin boshqaruvi: texnik tanaffus, blok, yopiq bo'limlar, bonus
    'Texnik ishlar': 'Технические работы', 'Ilovada texnik ishlar olib borilmoqda.': 'В приложении идут технические работы.',
    'Qayta ishga tushadi:': 'Снова заработает:', 'Tez orada qayta ishga tushadi.': 'Скоро снова заработает.',
    'Akkauntingiz bloklangan.': 'Ваш аккаунт заблокирован.', 'Sabab:': 'Причина:', 'Blok tugaydi:': 'Блокировка до:',
    'Muddat: muddatsiz.': 'Срок: бессрочно.', "Ro'yxatdan o'tish vaqtincha yopiq": 'Регистрация временно закрыта',
    "Hozircha yangi o'quvchilar qabul qilinmayapti. Birozdan keyin qayta urinib ko'ring.":
      'Сейчас новые ученики не принимаются. Попробуйте чуть позже.',
    "Bu bo'lim vaqtincha yopilgan. Birozdan keyin qayta urinib ko'ring.": 'Этот раздел временно закрыт. Попробуйте чуть позже.',
    // Bilim Premium sahifasi va bosh sahifa kartasi
    'AI ustoz, shaxsiy darslar, emoji va ramka': 'ИИ-наставник, личные уроки, эмодзи и рамка', "Ko'rish": 'Смотреть',
    'Ochish': 'Открыть', 'kun qoldi': 'дн. осталось', 'BILIM PREMIUM': 'BILIM PREMIUM',
    "O'qishning eng kuchli": 'Самый сильный уровень', 'darajasi': 'учёбы',
    "Shaxsiy AI ustoz, faqat siz uchun yaratiladigan darslar va hamma ko'radigan Premium belgilari.":
      'Личный ИИ-наставник, уроки, созданные только для вас, и знаки Premium, которые видят все.',
    'AI ustoz': 'ИИ-наставник', 'Maxsus emoji': 'Особые эмодзи', 'Chaqmoqli ramka': 'Рамка с молниями', 'Pastga suring': 'Листайте вниз',
    'Premium bilan nimalar ochiladi': 'Что открывает Premium',
    "Har biri — o'qishingizni tezlashtiradigan yoki sizni boshqalardan ajratib turadigan imkoniyat.":
      'Каждая возможность ускоряет вашу учёбу или выделяет вас среди других.',
    "Har bir darsda tushunmagan joyingizni so'rang — AI mavzuni boshqacha, sodda misollar bilan qadam-baqadam tushuntiradi.":
      'Спросите о непонятном в любом уроке — ИИ объяснит тему по-другому, шаг за шагом и на простых примерах.',
    "Kasrlarni qo'shishni tushunmadim 😕": 'Не понял сложение дробей 😕', 'AI ustoz:': 'ИИ-наставник:',
    "Keling, pitsa misolida ko'ramiz: ½ — yarim pitsa, ¼ — chorak pitsa. Yarimni ikkita chorakka bo'lsak: 2/4 + 1/4 = 3/4 🍕":
      'Давайте на примере пиццы: ½ — половина пиццы, ¼ — четверть. Разделим половину на две четверти: 2/4 + 1/4 = 3/4 🍕',
    "Istalgan mavzuni yozing — AI siz uchun dars, test va uy vazifasini tayyorlaydi. Darslar Premium tugasa ham o'zingizda qoladi.":
      'Напишите любую тему — ИИ подготовит для вас урок, тест и домашнее задание. Уроки останутся у вас даже после окончания Premium.',
    'Dars': 'Урок', 'Test': 'Тест',
    "Reyting, o'yinlar va kun savolida ismingiz yonida yaltiroq emoji turadi — hamma sizni darhol taniydi.":
      'В рейтинге, играх и вопросе дня рядом с вашим именем сияет эмодзи — вас сразу узнают.',
    "Avataringiz atrofida chaqmoqli ramka — Premium o'quvchi ekaningiz hammaga ko'rinadi.":
      'Рамка с молниями вокруг аватара — все видят, что вы ученик Premium.',
    'Oddiy va Premium': 'Обычный и Premium', 'Oddiy': 'Обычный', 'Premium': 'Premium',
    "Darslar, testlar va o'yinlar": 'Уроки, тесты и игры', 'Muddatni tanlang': 'Выберите срок',
    "Qancha uzoq muddat — oyiga shuncha arzon.": 'Чем дольше срок — тем дешевле в месяц.', 'Eng foydali': 'Самый выгодный',
    '1 oy': '1 месяц', '3 oy': '3 месяца', '1 yil': '1 год', "Sinab ko'rish uchun": 'Чтобы попробовать', "so'm": 'сум',
    'Promo-kodingiz bormi?': 'Есть промокод?',
    "To'lov karta orqali: botda karta raqami chiqadi, chek rasmini yuborasiz — admin odatda 5–30 daqiqada faollashtiradi.":
      'Оплата картой: в боте появится номер карты, вы отправите фото чека — админ обычно активирует за 5–30 минут.',
    'Obuna emas — pul avtomatik yechilmaydi.': 'Это не подписка — деньги не списываются автоматически.',
    "Ko'p so'raladigan savollar": 'Частые вопросы', 'Premium fanlarni ochadimi?': 'Открывает ли Premium предметы?',
    "Yo'q — fanlar Do'konda alohida sotiladi. Premium o'qishni qulayroq va qiziqarliroq qiladi.":
      'Нет — предметы продаются отдельно в Магазине. Premium делает учёбу удобнее и интереснее.',
    "Muddat tugasa nima bo'ladi?": 'Что будет, когда срок закончится?',
    "Premium imkoniyatlari yopiladi, lekin shaxsiy darslaringiz o'zingizda qoladi. Xohlasangiz, yana olasiz.":
      'Возможности Premium закроются, но ваши личные уроки останутся. Если захотите — оформите снова.',
    'Qancha vaqtda faollashadi?': 'Как быстро активируется?',
    "Chekni botga yuborganingizdan keyin admin tekshiradi — odatda 5–30 daqiqa. Faollashganda botga xabar keladi.":
      'После того как вы отправите чек в бот, админ его проверит — обычно 5–30 минут. Когда активируется, придёт сообщение в бот.',
    'Tanlangan:': 'Выбрано:', 'Olish': 'Получить', 'Imkoniyatlaringiz': 'Ваши возможности',
    'Emoji va ramka tanlash': 'Выбрать эмодзи и рамку', 'Muddati tugagach, shu yerdan yana olishingiz mumkin.':
      'Когда срок закончится, здесь же можно оформить снова.',
    'Bilim Premium (3 oy)': 'Bilim Premium (3 месяца)', 'Bilim Premium (1 yil)': 'Bilim Premium (1 год)',
    'Bu tarif hozircha sotilmaydi.': 'Этот тариф пока не продаётся.', "Tarif noto'g'ri.": 'Неверный тариф.',
    'Premium muddati': 'Срок Premium',
    'Admin bonusi': 'Бонус от админа', 'Admin tomonidan berilgan': 'Начислено админом',
    "Admin panelni ochib bo'lmadi": 'Не удалось открыть админ-панель',
    "do'stlik so'rovi":'заявка в друзья', "Hali do'stingiz yo'q. Tanishlaringizni toping!": 'У вас пока нет друзей. Найдите знакомых!',
    "Do'stlar reytingi": 'Рейтинг друзей', "Yangi so'rovlar": 'Новые заявки',
    "Sizga do'stlik so'rovi yubordi": 'Отправил(а) вам заявку в друзья', "do'stlikdan chiqarilsinmi?": 'удалить из друзей?',
    'Shikoyat qilish': 'Пожаловаться', "sababni tanlang. Admin ko'rib chiqadi.": 'выберите причину. Администратор рассмотрит жалобу.',
    'Nomaqbul ism': 'Недопустимое имя', 'Nomaqbul rasm': 'Недопустимое фото', 'Haqorat yoki bezorilik': 'Оскорбления или травля',
    'Izoh (ixtiyoriy)': 'Комментарий (необязательно)', 'Yuborish': 'Отправить', 'Sababni tanlang.': 'Выберите причину.',
    'Shikoyatingiz yuborildi. Rahmat!': 'Жалоба отправлена. Спасибо!',
    'Havola yuborish': 'Отправить ссылку', "Do'st qo'shish uchun bosing": 'Нажмите, чтобы позвать друга',
    "Do'stingizni chaqiring — unga xabar boradi va bir bosishda shu roomga kiradi.":
      'Позовите друга — он получит сообщение и зайдёт в эту комнату одним нажатием.',
    "Hali do'stingiz yo'q. Do'st qo'shing yoki havola yuboring.": 'У вас пока нет друзей. Добавьте друзей или отправьте ссылку.',
    "Do'st qidirish": 'Найти друга', 'Chaqirish': 'Позвать', 'Chaqirildi ✓': 'Позван ✓', 'Roomda': 'В комнате',
    'Chaqiruv yuborildi': 'Приглашение отправлено',
    "Chaqiruv yuborildi — do'stingiz ilovani ochganda ko'radi": 'Приглашение отправлено — друг увидит его, когда откроет приложение',
    "Juda ko'p qidiruv. Birozdan keyin urinib ko'ring.": 'Слишком много запросов. Попробуйте чуть позже.',
    "Noma'lum amal": 'Неизвестное действие', "Noma'lum amal.": 'Неизвестное действие.', "Noto'g'ri qiymat.": 'Неверное значение.',
    "Bu do'stingizni hozirgina chaqirdingiz — biroz kuting.": 'Вы только что позвали этого друга — немного подождите.',
    "Bu o'quvchi do'stingiz emas.": 'Этот ученик не ваш друг.',
    "Bu o'quvchi haqida shikoyatingiz allaqachon ko'rib chiqilmoqda.": 'Ваша жалоба на этого ученика уже рассматривается.',
    "Bu o'quvchining do'stlari soni to'lgan.": 'У этого ученика уже максимум друзей.',
    "Bu o'yin allaqachon boshlangan yoki yopilgan.": 'Эта игра уже началась или закрыта.',
    "Bugun juda ko'p shikoyat yubordingiz.": 'Сегодня вы отправили слишком много жалоб.',
    "Bugun juda ko'p so'rov yubordingiz. Ertaga yana urinib ko'ring.": 'Сегодня вы отправили слишком много заявок. Попробуйте завтра.',
    "Do'stingiz allaqachon shu o'yinda.": 'Ваш друг уже в этой игре.',
    "Faqat do'stlaringizni chaqira olasiz.": 'Звать можно только друзей.',
    "Javob kutilayotgan so'rovlaringiz juda ko'p. Avval ular javob bersin.": 'Слишком много заявок ждут ответа. Дождитесь ответов.',
    "O'zingizga shikoyat qila olmaysiz.": 'Нельзя пожаловаться на себя.',
    "O'zingizga so'rov yubora olmaysiz.": 'Нельзя отправить заявку самому себе.',
    "Siz allaqachon do'stsiz.": 'Вы уже друзья.', "Siz bu o'yinda emassiz.": 'Вы не в этой игре.',
    "Sizda do'stlik imkoni vaqtincha yopilgan.": 'Функция друзей для вас временно закрыта.',
    "So'rov allaqachon yuborilgan.": 'Заявка уже отправлена.',
    "So'rov topilmadi yoki allaqachon javob berilgan.": 'Заявка не найдена или на неё уже ответили.',
    "So'rov topilmadi.": 'Заявка не найдена.',

    // Yutuqli marafon
    "Reyting bo'limlari": 'Разделы рейтинга', 'Marafon': 'Марафон', "Hozircha marafon yo'q": 'Пока марафона нет',
    'Yangi yutuqli marafon boshlanganda bot orqali xabar beramiz.': 'Когда начнётся новый призовой марафон, мы сообщим через бота.',
    "Sovrin jamg'armasi": 'Призовой фонд', 'Marafon yakunlandi': 'Марафон завершён', 'Boshlanishiga:': 'До начала:',
    'Tugashiga:': 'До конца:', 'Faqat Premium': 'Только Premium', "G'oliblar": 'Победители',
    "Bu safar g'olib bo'lmadi.": 'В этот раз победителей нет.', "Siz sovrinli o'rindasiz!": 'Вы на призовом месте!',
    'Siz qatnashyapsiz': 'Вы участвуете', 'Siz bu marafondan chiqarilgansiz.': 'Вы исключены из этого марафона.',
    'Sovrinlar': 'Призы', 'Marafon qoidalari': 'Правила марафона',
    "Marafon boshlangandan (yoki siz qo'shilgan paytdan) keyin olingan chaqmoqlar sanaladi: darslar, o'yinlar va kun savoli.":
      'Засчитываются молнии, полученные после начала марафона (или после вашего присоединения): уроки, игры и вопрос дня.',
    "Shaxsiy darslardan 24 soatda faqat 1 ta darsning chaqmoqi sanaladi.": 'Из личных уроков за 24 часа засчитываются молнии только одного урока.',
    "O'yinlarda 24 soatda 3 ta chaqmoqli o'yin: 1-o'rin +30, qolganlar +20. Kompyuter bilan o'yin chaqmoq bermaydi.":
      'В играх за 24 часа 3 игры с молниями: 1-е место +30, остальные +20. Игра с компьютером молний не даёт.',
    "Chaqmoq teng bo'lsa, shu songa birinchi yetgan yuqorida turadi.": 'При равенстве молний выше тот, кто набрал их первым.',
    '"Faqat Premium" marafonda Premium faol bo\'lgan paytda olingan chaqmoqlar sanaladi.':
      'В марафоне «Только Premium» засчитываются молнии, полученные при активном Premium.',
    "Aldash (bir necha akkaunt, nohalol o'yin) aniqlansa — marafondan chiqariladi. Admin qarori yakuniy.":
      'При обмане (несколько аккаунтов, нечестная игра) участник исключается. Решение администратора окончательное.',
    "G'oliblarga bot orqali xabar keladi. Sovrin g'olibning yoki ota-onasining kartasiga o'tkaziladi.":
      'Победители получат сообщение от бота. Приз переводится на карту победителя или его родителей.',
    'Qatnashchilar': 'Участники', "Chaqmoq bo'yicha": 'По молниям', "Sovrinli o'rinlar chegarasi": 'Граница призовых мест',
    "Hali hech kim qo'shilmagan. Birinchi bo'ling!": 'Пока никто не присоединился. Будьте первым!',
    "do'st": 'друг', 'Qatnashish': 'Участвовать', 'Premium olib qatnashing': 'Оформите Premium и участвуйте',
    'Qatnashishdan oldin qoidalar bilan tanishing:': 'Перед участием ознакомьтесь с правилами:',
    'Qoidalarga roziman': 'Согласен с правилами', 'Qatnashaman': 'Участвую',
    "Siz marafonga qo'shildingiz. Omad!": 'Вы присоединились к марафону. Удачи!', "o'rin": 'место',
    'Qatnashyapsiz': 'Участвуете',
    "Hozircha faol marafon yo'q": 'Сейчас активных марафонов нет', 'Marafonlar tarixi': 'История марафонов',
    "Chaqmoq to'plang — sovrin kamida 1 chaqmoq to'plaganlarga beriladi": 'Собирайте молнии — приз получают набравшие хотя бы 1 молнию',
    "Marafonda shaxsiy darslardan 24 soatda faqat 1 ta darsning chaqmoqi sanaladi — bu dars chaqmoqi umumiy hisobingizga qo'shildi, marafonga esa qo'shilmadi.":
      'В марафоне из личных уроков за 24 часа засчитывается только один урок — молнии этого урока добавлены в общий счёт, но не в марафон.',
    'Marafon topilmadi.': 'Марафон не найден.',
    'Qatnashish uchun marafon qoidalariga rozilik bering.': 'Чтобы участвовать, согласитесь с правилами марафона.',
    "Bu marafonga qo'shilib bo'lmaydi.": 'К этому марафону нельзя присоединиться.',
    "Bu marafonda faqat Bilim Premium a'zolari qatnasha oladi.": 'В этом марафоне могут участвовать только участники Bilim Premium.',
    "Juda ko'p urinish. Birozdan keyin urinib ko'ring.": 'Слишком много попыток. Попробуйте чуть позже.',
    'Marafon sovrindori': 'Призёр марафона', "Yutuqli marafonda sovrinli o'ringa kirdingiz": 'Вы заняли призовое место в марафоне',
    "Marafon g'olibi": 'Победитель марафона', "Yutuqli marafonda 1-o'rinni oldingiz": 'Вы заняли 1-е место в марафоне',

    // Chaqmoqli o'yinlar
    "Oxirgi chaqmoqli o'yin tugagach 24 soatlik taymer boshlanadi.": 'После последней игры с молниями запустится 24-часовой таймер.',
    'Yangilanishiga qoldi:': 'До обновления:',
    "O'ynash cheksiz. Kompyuter bilan o'yin chaqmoq bermaydi.": 'Играть можно без ограничений. Игра с компьютером молний не даёт.',
    "O'yinlarda to'plangan ball bo'yicha.": 'По очкам, набранным в играх.',
    "Siz o'yindan chiqdingiz": 'Вы вышли из игры',
    "Chaqmoqli o'yin imkoniyatingiz tugagan — bu o'yin chaqmoq bermaydi.": 'Попытки игр с молниями закончились — эта игра молний не даст.',
    "Chaqmoq uchun kamida 2 kishi o'ynashi kerak. Kompyuter bilan o'yin chaqmoq bermaydi.":
      'Для молний нужно минимум 2 игрока. Игра с компьютером молний не даёт.',
    "Kompyuter bilan o'yin chaqmoq bermaydi.": 'Игра с компьютером молний не даёт.',
    "O'yindan chiqasizmi?": 'Выйти из игры?',
    "Siz hozir o'yindan chiqib ketasiz va chaqmoq olmaysiz. Natijalar jadvalida ham ko'rinmaysiz.":
      'Вы выйдете из игры и не получите молнии. В таблице результатов вас тоже не будет.',
    "Bu chaqmoqli o'yin imkoniyati baribir ishlatilgan hisoblanadi.": 'Попытка игры с молниями всё равно будет засчитана как использованная.',
    "O'yinda qolish": 'Остаться в игре', 'Baribir chiqaman': 'Всё равно выйти',
    "Raqiblar o'yindan chiqib ketgani uchun o'yin tugadi.": 'Игра завершилась, потому что соперники вышли.',
    "Siz bu o'yindan chiqib ketgansiz (chiqish bosilgan yoki aloqa uzilgan). Bu o'yin sizga chaqmoq bermaydi.":
      'Вы вышли из этой игры (нажали «выйти» или пропала связь). Эта игра не даст вам молний.',
  };

  // Raqamli va tarkibli matnlar: [qolip, almashtirish]
  var fanRu = function (s) { return String(s).split(/,\s*/).map(function (x) { return RU[x] || x; }).join(', '); };
  var vaqtRu = function (s) {
    return String(s).replace(/(\d+)\s*kun/g, '$1 д').replace(/(\d+)\s*soat/g, '$1 ч')
      .replace(/(\d+)\s*daqiqa/g, '$1 мин').replace(/(\d+)\s*soniya/g, '$1 с');
  };
  var RE = [
    // Bilim Premium: narxlar va muddatlar
    [/^Oyiga ([\d ]+) so'mdan boshlab$/, 'От $1 сум в месяц'],
    [/^(\d+) o'quvchi allaqachon Premium'da$/, function (m, n) { return n + ' ' + ko(n, 'ученик', 'ученика', 'учеников') + ' уже в Premium'; }],
    [/^Har (\d+) soatda yangi dars$/, function (m, n) { return 'Новый урок каждые ' + n + ' ' + ko(n, 'час', 'часа', 'часов'); }],
    [/^oyiga ([\d ]+) so'm$/, '$1 сум в месяц'],
    [/^−(\d+)% tejaysiz$/, 'экономия $1%'],
    [/^Premium olish — ([\d ]+) so'm$/, 'Получить Premium — $1 сум'],
    [/^(1 oy|3 oy|1 yil) — ([\d ]+) so'm$/, function (m, t, n) { return ({ '1 oy': '1 месяц', '3 oy': '3 месяца', '1 yil': '1 год' })[t] + ' — ' + n + ' сум'; }],
    [/^(\d+) xil ramka$/, function (m, n) { return n + ' ' + ko(n, 'рамка', 'рамки', 'рамок'); }],
    // Yutuqli marafon
    [/^Top-(\d+) sovrin oladi$/, 'Призы получат топ-$1'],
    [/^(\d+) qatnashchi$/, function (m, n) { return n + ' ' + ko(n, 'участник', 'участника', 'участников'); }],
    [/^Boshlanadi: (.+)\. Hozirdan qo'shilib qo'yishingiz mumkin\.$/, 'Начало: $1. Присоединиться можно уже сейчас.'],
    [/^Tabriklaymiz! Siz (\d+)-o'rinni egalladingiz\. Sovrin haqida botga xabar yuborildi\.$/,
      'Поздравляем! Вы заняли $1-е место. Сообщение о призе отправлено в бота.'],
    [/^Keyingi o'ringa: (\d+) chaqmoq$/, 'До следующего места: $1 молний'],
    [/^Top-(\d+) ga: (\d+) chaqmoq$/, 'До топ-$1: $2 молний'],
    [/^Sizning o'rningiz: (\d+)$/, 'Ваше место: $1'],
    [/^Siz bu marafondan chiqarilgansiz\. Sabab: (.+)$/, 'Вы исключены из этого марафона. Причина: $1'],
    [/^([\d ]+) so'm \+ (.+)$/, '$1 сум + $2'],
    [/^Sovrin jamg'armasi: ([\d ]+) so'm$/, 'Призовой фонд: $1 сум'],

    // Chaqmoqli o'yinlar
    [/^Chaqmoqli o'yinlar: (\d+) \/ (\d+)$/, 'Игры с молниями: $1 / $2'],
    [/^Odamlar bilan o'yin: 1-o'rin \+(\d+), qolganlar \+(\d+) chaqmoq\.$/, 'Игра с людьми: 1-е место +$1, остальные +$2 молний.'],
    [/^Bu o'yin chaqmoq beradi: 1-o'rin \+(\d+), qolganlar \+(\d+)\.(?: Qolgan imkoniyat: (\d+) \/ (\d+)\.)?$/,
      function (m, a, b, c, d) { return 'Эта игра даёт молнии: 1-е место +' + a + ', остальные +' + b + '.' + (c ? ' Осталось попыток: ' + c + ' / ' + d + '.' : ''); }],
    [/^Chaqmoqli o'yin imkoniyatingiz tugagan — bu o'yin chaqmoq bermaydi\. Yangilanishiga: (.+)\.$/,
      function (m, t) { return 'Попытки игр с молниями закончились — эта игра молний не даст. До обновления: ' + vaqtRu(t) + '.'; }],
    [/^(.+) aloqasi uzildi\. 30 soniyada qaytmasa, o'yindan chiqib ketgan hisoblanadi\.$/,
      function (m, k) { return (/^\d+ ta o'yinchi$/.test(k) ? 'У ' + k.replace(" ta o'yinchi", ' игроков') : 'У игрока ' + k) + ' пропала связь. Если не вернётся за 30 секунд, считается, что вышел из игры.'; }],
    [/^(.+) o'yindan chiqib ketdi — natijada ko'rinmaydi\.$/, '$1 — вышли из игры, в результатах их нет.'],
    [/^(.+) o'yindan chiqib ketdi$/, '$1 — вышел(а) из игры'],
    [/^O'yin baliga qo'shildi: \+(\d+)(?: \(bonus \+(\d+)\))?( — bugungi ball limiti to'ldi)?\.$/,
      function (m, a, b, c) { return 'Добавлено к игровым очкам: +' + a + (b ? ' (бонус +' + b + ')' : '') + (c ? ' — дневной лимит очков исчерпан' : '') + '.'; }],
    // Do'stlar
    [/^«(.+)» mavzusini tugatdi$/, 'завершил(а) тему «$1»'],
    [/^«(.+)» nishonini oldi$/, function (m, a) { return 'получил(а) значок «' + (RU[a] || a) + '»'; }],
    [/^(.+) sizni «(.+)» o'yiniga chaqirdi$/, function (m, a, b) { return a + ' зовёт вас в игру «' + (RU[b] || b) + '»'; }],
    [/^(\d+) daqiqa oldin$/, '$1 мин назад'], [/^(\d+) soat oldin$/, '$1 ч назад'],
    [/^(\d+) kun oldin$/, function (m, n) { return n + ' ' + ko(n, 'день', 'дня', 'дней') + ' назад'; }],
    [/^(\d+) do'st$/, function (m, n) { return n + ' ' + ko(n, 'друг', 'друга', 'друзей'); }],
    [/^(\d+) \/ (\d+) do'st$/, '$1 / $2 друзей'],
    [/^Sizda (\d+) ta do'st bor — bu eng ko'pi\.$/, 'У вас $1 друзей — это максимум.'],
    [/^Hammasi \((\d+)\)$/, 'Все ($1)'],
    [/^(\d+)-sinf$/, '$1 класс'],
    [/^(\d+)-o'rin reytingda$/, '$1-е место в рейтинге'],
    [/^(\d+) ta mavzu$/, function (m, n) { return n + ' ' + ko(n, 'тема', 'темы', 'тем'); }],
    [/^(\d+) \/ (\d+) mavzu$/, function (m, a, b) { return a + ' / ' + b + ' ' + ko(b, 'темы', 'тем', 'тем'); }],
    [/^(\d+) \/ (\d+) bajarildi$/, '$1 / $2 выполнено'],
    [/^(\d+) \/ (\d+) to'g'ri$/, '$1 / $2 верно'],
    [/^(\d+) \/ (\d+) o'yinchi$/, function (m, a, b) { return a + ' / ' + b + ' ' + ko(b, 'игрока', 'игроков', 'игроков'); }],
    [/^(\d+) kun$/, function (m, n) { return n + ' ' + ko(n, 'день', 'дня', 'дней'); }],
    [/^(\d+) kun (\d+) soat$/, '$1 д $2 ч'],
    [/^(\d+) o'yin$/, function (m, n) { return n + ' ' + ko(n, 'игра', 'игры', 'игр'); }],
    [/^(\d+) g'alaba$/, function (m, n) { return n + ' ' + ko(n, 'победа', 'победы', 'побед'); }],
    [/^(\d+) to'g'ri$/, function (m, n) { return n + ' ' + ko(n, 'верный', 'верных', 'верных'); }],
    [/^(\d+) ta fan$/, function (m, n) { return n + ' ' + ko(n, 'предмет', 'предмета', 'предметов'); }],
    [/^(\d+) ta fan mavjud\.$/, 'Доступно предметов: $1.'],
    [/^Barcha fanlar \((\d+) ta\)$/, 'Все предметы ($1)'],
    [/^(\d+) ta juftlik to'g'ri\.$/, 'Верных пар: $1.'],
    [/^(\d+)\/(\d+) juftlik to'g'ri$/, 'Верных пар: $1/$2'],
    [/^(\d+) ta o'yinchi hali tayyor emas\.$/, 'Ещё не готовы игроков: $1.'],
    [/^(\d+) ta o'yinchi javob berdi$/, 'Ответили игроков: $1'],
    [/^(\d+) ta o'yinchi$/, function (m, n) { return n + ' ' + ko(n, 'игрок', 'игрока', 'игроков'); }],
    [/^(\d+)-o'rin$/, '$1-е место'],
    [/^\((\d+)-o'rin\)$/, '($1-е место)'],
    [/^siz (\d+)-o'rindasiz$/, 'вы на $1-м месте'],
    [/^(\d+)-raund — (\d+)\/(\d+) juftlik to'g'ri$/, 'Раунд $1 — верных пар: $2/$3'],
    [/^(\d+)-savol, jami (\d+) ta$/, 'Вопрос $1 из $2'],
    [/^(\d+)-savol: (.+)\. Hali juftlanmagan$/, 'Вопрос $1: $2. Пока без пары'],
    [/^(\d+)-savol: (.+)\. Juftlandi: (.+)$/, 'Вопрос $1: $2. В паре с: $3'],
    [/^(.+)\. (\d+)-savolga juftlangan$/, '$1. В паре с вопросом $2'],
    [/^(\d+) savol$/, function (m, n) { return n + ' ' + ko(n, 'вопрос', 'вопроса', 'вопросов'); }],
    [/^(\d+) raund$/, function (m, n) { return n + ' ' + ko(n, 'раунд', 'раунда', 'раундов'); }],
    [/^([+−-]?[\d\s]+) so'm$/, '$1 сум'],
    [/^(\d+) chaqmoq$/, function (m, n) { return n + ' ' + ko(n, 'молния', 'молнии', 'молний'); }],
    [/^\+(\d+) chaqmoq$/, function (m, n) { return '+' + n + ' ' + ko(n, 'молния', 'молнии', 'молний'); }],
    [/^(\d+) ball$/, function (m, n) { return n + ' ' + ko(n, 'очко', 'очка', 'очков'); }],
    [/^(\d+) ta mavzu tugatildi$/, 'Пройдено тем: $1'],
    [/^(\d+) ta g'alaba$/, function (m, n) { return n + ' ' + ko(n, 'победа', 'победы', 'побед'); }],
    [/^(\d+) ta javob noto'g'ri yoki bo'sh\. Tekshirib, qayta yuboring\.$/, 'Неверных или пустых ответов: $1. Проверьте и отправьте снова.'],
    [/^([\d.]+ [\d:]+) da ochiladi$/, 'Откроется $1'],
    [/^([\d.]+ [\d:]+) da ochiladi \(Toshkent vaqti\)$/, 'Откроется $1 (по Ташкенту)'],
    [/^(\d+) javob, (\d+) to'g'ri$/, 'Ответов: $1, верных: $2'],
    [/^([\d,.]+) soniyada javob berdingiz$/, 'Вы ответили за $1 с'],
    [/^\((\d+) o'quvchi orasida\)$/, function (m, n) { return '(среди ' + n + ' ' + ko(n, 'ученика', 'учеников', 'учеников') + ')'; }],
    [/^Bugun (\d+) kishi javob berdi(,?)$/, 'Сегодня ответили: $1$2'],
    [/^Bugun — (.+?)\. Faqat bitta urinish\. Vaqt savolni ochganingizda boshlanadi: to'g'ri va tez javob bersangiz, kunlik reytingga chiqasiz \(\+5 chaqmoq\)\.$/,
      function (m, f) { return 'Сегодня — ' + fanRu(f) + '. Только одна попытка. Время пойдёт, когда вы откроете вопрос: ответьте правильно и быстро — и попадёте в рейтинг дня (+5 молний).'; }],
    [/^Bugungi reja: (\d+) \/ (\d+)$/, 'План на сегодня: $1 / $2'],
    [/^Daraja (\d+)$/, 'Уровень $1'],
    [/^Sevimli fanlar: (.+)$/, function (m, f) { return 'Любимые предметы: ' + fanRu(f); }],
    [/^Ketma-ket (\d+) kun$/, function (m, n) { return 'Серия: ' + n + ' ' + ko(n, 'день', 'дня', 'дней'); }],
    [/^Eslatma har kuni soat ([\d:]+) da keladi$/, 'Напоминание приходит каждый день в $1'],
    [/^Ko'pi bilan (\d+) ta nishon tanlash mumkin\.?$/, 'Можно выбрать не больше $1 значков'],
    [/^Ko'pi bilan (\d+) ta kompyuter qo'shish mumkin\.$/, 'Можно добавить не больше $1 компьютеров.'],
    [/^(\d+) ta nishon tanlash mumkin$/, 'можно выбрать $1 значков'],
    [/^Hammasini ko'rish \((\d+)\)$/, 'Показать все ($1)'],
    [/^Hisobga o'tdi: \+(\d+) ball(?: \(bonus \+(\d+)\))?( — bugungi o'yin limiti to'ldi)?\. Har 10 ball = 1 chaqmoq\.$/,
      function (m, a, b, limit) {
        return 'Зачтено: +' + a + ' ' + ko(a, 'очко', 'очка', 'очков') + (b ? ' (бонус +' + b + ')' : '') +
          (limit ? ' — дневной лимит игр исчерпан' : '') + '. Каждые 10 очков = 1 молния.';
      }],
    [/^Hozir: (.+)$/, 'Сейчас: $1'],
    [/^Keyingi: (.+)$/, 'Далее: $1'],
    [/^Keyingi savol (\d+) soniyadan so'ng$/, 'Следующий вопрос через $1 с'],
    [/^Natijalar (\d+) soniyadan so'ng$/, 'Результаты через $1 с'],
    [/^Keyingi savol (.+)dan keyin$/, function (m, v) { return 'Следующий вопрос через ' + vaqtRu(v); }],
    [/^Bu fanda bugungi mavzuni yakunladingiz\. Keyingi mavzu (.+)dan so'ng ochiladi\. Bu orada boshqa fanlarni o'qishingiz mumkin\.$/,
      function (m, v) { return 'Вы завершили сегодняшнюю тему по этому предмету. Следующая откроется через ' + vaqtRu(v) + '. А пока можно заниматься другими предметами.'; }],
    [/^Bu fanda bir kunda faqat bitta mavzu yakunlanadi\. (.+)dan so'ng qayta urinib ko'ring\.$/,
      function (m, v) { return 'По этому предмету можно завершить только одну тему в день. Попробуйте через ' + vaqtRu(v) + '.'; }],
    [/^(\d+) soat (\d+) daqiqa$/, '$1 ч $2 мин'], [/^(\d+) soat$/, '$1 ч'], [/^(\d+) daqiqa$/, '$1 мин'],
    [/^(\d+) soniya$/, '$1 с'],
    [/^Klaviatura: 1–(\d+) yoki A–([A-Z])$/, 'Клавиатура: 1–$1 или A–$2'],
    [/^Kompyuter \((.+)\)$/, function (m, d) { return 'Компьютер (' + t(d) + ')'; }],
    [/^(.+)ni roomdan chiqarish$/, function (m, n) { return 'Удалить из комнаты: ' + t(n); }],
    [/^(.+) \(siz\)$/, '$1 (вы)'],
    [/^(.+): (\d+)% aniqlik$/, function (m, f, n) { return fanRu(f) + ': точность ' + n + '%'; }],
    [/^(.+), (\d+)-mavzu \((\d+) tadan\)$/, function (m, f, a, b) { return fanRu(f) + ', тема ' + a + ' из ' + b; }],
    [/^Room ([A-Z0-9]{6})$/, 'Комната $1'],
    [/^Room kodi: (.+)$/, 'Код комнаты: $1'],
    [/^Raund (\d+), jami (\d+)\.$/, 'Раунд $1 из $2.'],
    [/^Savol (\d+), jami (\d+)\.$/, 'Вопрос $1 из $2.'],
    [/^Siz (\d+) ta savoldan (\d+) tasiga to'g'ri javob berdingiz\.$/, 'Вы правильно ответили на $2 из $1.'],
    [/^Sizning javobingiz: (.+)$/, function (m, x) { return 'Ваш ответ: ' + t(x); }],
    [/^To'g'ri javob: (.+)$/, function (m, x) { return 'Правильный ответ: ' + t(x); }],
    [/^To'g'ri javob! (\d+)-o'rin$/, 'Правильно! $1-е место'],
    [/^Taxminan (\d+) daqiqa$/, 'Примерно $1 мин'],
    [/^~(\d+) daqiqa$/, '~$1 мин'],
    [/^Xayrli (tong|kun|kech|tun), (.+)!$/, function (m, v, n) {
      return { tong: 'Доброе утро', kun: 'Добрый день', kech: 'Добрый вечер', tun: 'Доброй ночи' }[v] + ', ' + n + '!';
    }],
    [/^yana (\d+) ta bo'sh joy$/, function (m, n) { return 'ещё ' + n + ' ' + ko(n, 'свободное место', 'свободных места', 'свободных мест'); }],
    [/^Javobingiz qabul qilindi\. Boshqalar kutilmoqda \((\d+)\/(\d+)\)$/, 'Ваш ответ принят. Ждём остальных ($1/$2)'],
    [/^(.+) ochilmoqda\.\.\.$/, function (m, f) { return fanRu(f) + ' — открываем...'; }],
    [/^(.+) qulflangan$/, function (m, f) { return fanRu(f) + ' — предмет закрыт'; }],
    [/^O'tish uchun kamida (\d+)% kerak\.$/, 'Чтобы пройти, нужно минимум $1%.'],
    [/^Ism (\d+) ta belgidan oshmasin\.$/, 'Имя не должно быть длиннее $1 символов.'],
    [/^Buyurtma (\S+) — chek kutilmoqda$/, 'Заказ $1 — ожидается чек'],
    [/^Promo-kod qo'llandi: −(\d+)%$/, 'Промокод применён: −$1%'],
    [/^«(.+)» mavzusini muvaffaqiyatli yakunladingiz\.$/, 'Вы успешно завершили тему «$1».'],
    [/^host: (.+)$/, 'хост: $1'],
    // Bilim Premium va shaxsiy darslar
    [/^gacha \((\d+) kun qoldi\)$/, function (m, n) { return '(осталось ' + n + ' ' + ko(n, 'день', 'дня', 'дней') + ')'; }],
    [/^1 oyga$/, 'за 1 месяц'],
    [/^Havola orqali kelgan promo-kod avtomatik qo'yildi(?: \(−(\d+)%\))?\.$/,
      function (m, p) { return 'Промокод из ссылки подставлен автоматически' + (p ? ' (−' + p + '%)' : '') + '.'; }],
    // Hamkorlik (profil)
    [/^Promo-kod ([A-Z0-9]+)$/, 'Промокод $1'],
    [/^Promo-kod ([A-Z0-9]+) \(−(\d+)%\)$/, 'Промокод $1 (−$2%)'],
    [/^Yana (\d+) ta sotuv — komissiyangiz (\d+)% bo'ladi\.$/,
      function (m, n, p) { return 'Ещё ' + n + ' ' + ko(n, 'продажа', 'продажи', 'продаж') + ' — и ваша комиссия станет ' + p + '%.'; }],
    [/^(\d+) ta maxsus emoji'dan birini tanlang — u reyting, o'yinlar va kun savolida ismingiz yonida ko'rinadi\.$/,
      'Выберите одно из $1 особых эмодзи — оно будет видно рядом с вашим именем в рейтинге, играх и вопросе дня.'],
    [/^Bilim Premium bilan (\d+) ta maxsus emoji'dan birini tanlaysiz — u reyting, o'yinlar va kun savolida ismingiz yonida ko'rinadi\.$/,
      'С Bilim Premium вы выберете одно из $1 особых эмодзи — оно будет видно рядом с вашим именем в рейтинге, играх и вопросе дня.'],
    [/^Avataringiz atrofida chaqmoqli ramka paydo bo'ladi — (\d+) xil ramkadan birini tanlaysiz\. Hamma sizni Premium o'quvchi ekaningizni ko'radi\.$/,
      'Вокруг аватара появится рамка с молниями — выберите одну из $1. Все увидят, что вы ученик с Premium.'],
    [/^Bilim Premium bilan avataringiz atrofida chaqmoqli ramka paydo bo'ladi — (\d+) xildan birini tanlaysiz\.$/,
      'С Bilim Premium вокруг аватара появится рамка с молниями — выберите одну из $1.'],
    [/^«(.+)» tayyorlanmoqda\.\.\.$/, '«$1» готовится...'],
    [/^«(.+)» shaxsiy darslaringizga qo'shildi$/, '«$1» добавлен в ваши личные уроки'],
    [/^«(.+)» darsini tayyorlab bo'lmadi\. Qayta urinib ko'ring\.$/, 'Не удалось подготовить урок «$1». Попробуйте ещё раз.'],
    [/^Iltimos, (.+) fanidan mavzu nomini kiriting\.$/, function (m, f) { return 'Пожалуйста, введите название темы по предмету «' + fanRu(f) + '».'; }],
    [/^Har 24 soatda bitta shaxsiy dars yaratiladi\. Keyingisi — (.+)dan so'ng\.$/,
      function (m, v) { return 'Новый личный урок можно создавать раз в 24 часа. Следующий — через ' + vaqtRu(v) + '.'; }],
    [/^(\d+) ta dars$/, function (m, n) { return n + ' ' + ko(n, 'урок', 'урока', 'уроков'); }],
    [/^(\d+) \/ (\d+) chaqmoq$/, '$1 / $2 молний'],
    [/^(\d+) \/ 3 bosqich$/, '$1 / 3 этапа'],
    [/^(.+) \+(\d+) chaqmoq$/, function (m, a, n) { return t(a) + ' +' + n + ' ' + ko(n, 'молния', 'молнии', 'молний'); }],
    [/^(.+) aloqasi uzildi — qaytishini kutyapmiz\.\.\.$/, function (m, k) { return t(k) + ': связь потеряна — ждём возвращения...'; }],
    // Do'stlarga ulashiladigan matnlar
    [/^BilimSari kun savoliga ([\d,.]+) soniyada to'g'ri javob berdim(?: \((\d+)-o'rin\))?! Sen qancha vaqtda yecha olasan\?$/,
      function (m, s, o) { return 'Я правильно ответил на вопрос дня BilimSari за ' + s + ' с' + (o ? ' (' + o + '-е место)' : '') + '! А ты за сколько решишь?'; }],
    [/^BilimSari'da (.+) o'yiniga taklif qilaman! Room kodi: (\S+)$/, 'Приглашаю в игру $1 в BilimSari! Код комнаты: $2'],
  ];

  // ───────────────────────── Tarjima ─────────────────────────
  var BELGI_OXIR = /(\s*(?:›|→|…|\.\.\.|[:!?.,]|[←-⇿☀-➿]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|\uD83E[\uDD00-\uDFFF]))$/;
  var BELGI_BOSH = /^((?:←|‹|[←-⇿☀-➿]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|\uD83E[\uDD00-\uDFFF])\s*)/;

  function norm(s) {
    return String(s).replace(/[ʻʼ‘’`´]/g, "'").replace(/\s+/g, ' ').trim();
  }

  function asosiy(k, chuqurlik) {
    if (!k) return null;
    if (Object.prototype.hasOwnProperty.call(RU, k)) return RU[k];
    for (var i = 0; i < RE.length; i++) {
      var q = RE[i];
      if (q[0].test(k)) return k.replace(q[0], q[1]);
    }
    if (chuqurlik > 3) return null;
    // Belgilar: "Darsni ochish ›", "← Orqaga", "Bugungi reja:"
    var m = k.match(BELGI_OXIR);
    if (m && m[1].length < k.length) {
      var ichi = asosiy(k.slice(0, -m[1].length).trim(), chuqurlik + 1);
      if (ichi !== null) return ichi + m[1];
    }
    m = k.match(BELGI_BOSH);
    if (m && m[1].length < k.length) {
      var qolgan = asosiy(k.slice(m[1].length).trim(), chuqurlik + 1);
      if (qolgan !== null) return m[1] + qolgan;
    }
    // Bo'laklar: "A • B", "A — B", "Chap: o'ng"
    var ajratgichlar = [' • ', ' — ', ' – '];
    for (var j = 0; j < ajratgichlar.length; j++) {
      var a = ajratgichlar[j];
      if (k.indexOf(a) > 0) {
        var qismlar = k.split(a);
        var ozgardi = false;
        var yangi = qismlar.map(function (p) {
          var r = asosiy(p.trim(), chuqurlik + 1);
          if (r !== null && r !== p) ozgardi = true;
          return r === null ? p : r;
        });
        if (ozgardi) return yangi.join(a);
      }
    }
    if (k.indexOf(', ') > 0) {                // "Matematika, Tarix" — hammasi tarjima bo'lsa
      var royxat = k.split(', ').map(function (p) { return asosiy(p, chuqurlik + 1); });
      if (royxat.every(function (r) { return r !== null; })) return royxat.join(', ');
    }
    var ik = k.indexOf(': ');
    if (ik > 0) {
      var chap = asosiy(k.slice(0, ik + 1), chuqurlik + 1);
      if (chap !== null) {
        var ong = asosiy(k.slice(ik + 2), chuqurlik + 1);
        return chap + ' ' + (ong === null ? k.slice(ik + 2) : ong);
      }
    }
    return null;
  }

  function t(s) {
    if (s === null || s === undefined) return s;
    if (til !== 'ru') {
      if (!ovrBor) return s;
      var uk = norm(s);
      return Object.prototype.hasOwnProperty.call(OVR.uz, uk) ? OVR.uz[uk] : s;
    }
    var matn = String(s);
    var k = norm(matn);
    if (!k || !/[A-Za-z]/.test(k)) return matn;
    if (Object.prototype.hasOwnProperty.call(OVR.ru, k)) return OVR.ru[k];
    var r = asosiy(k, 0);
    return r === null ? matn : r;
  }

  // ───────────────────────── Admin sozlamalari ─────────────────────────
  var SAYT_KALIT = 'bilimsari_sayt';
  var OVR = { uz: {}, ru: {} };
  var ovrBor = false;            // o'zbekcha almashtirish bormi (yo'q bo'lsa o'zbekcha sahifada kuzatuvchi ishlamaydi)
  var ishlayapti = false;

  function saytQoy(d) {
    OVR = { uz: {}, ru: {} };
    ['uz', 'ru'].forEach(function (l) {
      var x = (d && d.texts && d.texts[l]) || {};
      Object.keys(x).forEach(function (k) { OVR[l][norm(k)] = x[k]; });
    });
    ovrBor = Object.keys(OVR.uz).length > 0;
    // Ranglar va yashirilgan bloklar — server tekshirgan CSS o'zgaruvchilari va selektorlar
    var css = '';
    var th = (d && d.theme) || {};
    var v = Object.keys(th).filter(function (k) { return /^--[a-z-]+$/.test(k) && /^#[0-9a-fA-F]{6}$/.test(th[k]); })
      .map(function (k) { return k + ':' + th[k]; });
    if (v.length) css += ':root{' + v.join(';') + '}';
    var hide = (d && d.hide) || [];
    if (hide.length) css += hide.join(',') + '{display:none!important}';
    var el = document.getElementById('saytUslub');
    if (!el && css) {
      el = document.createElement('style');
      el.id = 'saytUslub';
      (document.head || document.documentElement).appendChild(el);
    }
    if (el) el.textContent = css;
  }

  var sayt = null;
  try { sayt = JSON.parse(localStorage.getItem(SAYT_KALIT) || 'null'); } catch (e) { sayt = null; }
  if (sayt) saytQoy(sayt);

  function saytYangila() {
    if (typeof fetch !== 'function') return Promise.resolve(false);
    return fetch('/api/site/config', { credentials: 'same-origin', cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.ok || (sayt && sayt.v === d.v)) return false;
      sayt = d;
      try { localStorage.setItem(SAYT_KALIT, JSON.stringify(d)); } catch (e) { /* xotira yopiq */ }
      var oldin = ovrBor;
      saytQoy(d);
      // Jonli: ochiq sahifadagi matnlar asl nusxasidan qayta hisoblanadi (yangi almashtirish qo'llanadi,
      // olib tashlangani asliga qaytadi)
      if (til === 'ru' || ovrBor || oldin) {
        if (!ishlayapti) ishgaTushir();
        else { aylan(document.documentElement); sarlavha(); }
      }
      return true;
    }).catch(function () { return false; /* tarmoq yo'q — keshdagisi qoladi */ });
  }

  // ───────────────────────── Sahifa ─────────────────────────
  var ATTR = ['placeholder', 'title', 'aria-label', 'alt'];

  function tashla(el) {
    return !el || (el.closest && el.closest('script,style,noscript,textarea,[translate="no"],.notranslate'));
  }

  // Tugun → {asl matn, biz qo'ygan matn}: sozlamalar o'zgarsa, matn aslidan qayta hisoblanadi
  var ASL = typeof WeakMap === 'function' ? new WeakMap() : null;

  function matnTugun(n) {
    var joriy = n.nodeValue;
    var a = ASL && ASL.get(n);
    if (a && a.qoyilgan !== joriy) { ASL.delete(n); a = null; }      // matnni sahifa kodi o'zgartirgan — yangi asl
    var v = a ? a.asl : joriy;
    if (!v || !/[A-Za-z]/.test(v) || tashla(n.parentElement)) return;
    var yangi = t(v), kerak = v;
    if (yangi !== v) {
      var bosh = v.match(/^\s*/)[0], oxir = v.match(/\s*$/)[0];
      kerak = bosh + yangi + oxir;
    }
    if (kerak === joriy) return;
    if (ASL) { if (kerak !== v) ASL.set(n, { asl: v, qoyilgan: kerak }); else ASL.delete(n); }
    n.nodeValue = kerak;
  }

  function atribut(el, nom, joriy, qoy) {
    var xarita = ASL && ASL.get(el);
    var a = xarita && xarita[nom];
    if (a && a.qoyilgan !== joriy) a = null;
    var v = a ? a.asl : joriy, y = t(v);
    if (y === joriy) return;
    if (ASL) {
      xarita = xarita || {};
      if (y !== v) xarita[nom] = { asl: v, qoyilgan: y }; else delete xarita[nom];
      ASL.set(el, xarita);
    }
    qoy(y);
  }

  function element(el) {
    if (tashla(el)) return;
    if (til === 'ru' && el.hasAttribute('data-ru')) {   // bir xil so'z turli joyda turlicha tarjima qilinsa
      var aniq = el.getAttribute('data-ru');
      if (el.textContent !== aniq) el.textContent = aniq;
      return;
    }
    ATTR.forEach(function (a) {
      if (el.hasAttribute(a)) atribut(el, a, el.getAttribute(a), function (y) { el.setAttribute(a, y); });
    });
    if (el.tagName === 'INPUT' && /^(button|submit)$/i.test(el.type) && el.value) {
      atribut(el, '#value', el.value, function (y) { el.value = y; });
    }
  }

  function aylan(root) {
    if (!root) return;
    if (root.nodeType === 3) { matnTugun(root); return; }
    if (root.nodeType !== 1 || tashla(root)) return;
    element(root);
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        if (n.nodeType === 1 && tashla(n)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    var n;
    while ((n = walker.nextNode())) {
      if (n.nodeType === 3) matnTugun(n); else element(n);
    }
  }

  var sarlavhaAsl = null, sarlavhaQoyilgan = null;
  function sarlavha() {
    if (document.title !== sarlavhaQoyilgan) sarlavhaAsl = document.title;
    var y = t(sarlavhaAsl);
    sarlavhaQoyilgan = y;
    if (y !== document.title) document.title = y;
  }

  function dialoglar() {
    ['alert', 'confirm', 'prompt'].forEach(function (nom) {
      var asl = window[nom];
      if (!asl || asl.__i18n) return;
      var o = function (m) { var a = Array.prototype.slice.call(arguments); a[0] = t(m); return asl.apply(window, a); };
      o.__i18n = true;
      window[nom] = o;
    });
    var tg = window.Telegram && window.Telegram.WebApp;
    if (tg && !tg.__i18n) {
      tg.__i18n = true;
      ['showAlert', 'showConfirm'].forEach(function (nom) {
        var asl = tg[nom];
        if (typeof asl !== 'function') return;
        tg[nom] = function (m) { var a = Array.prototype.slice.call(arguments); a[0] = t(m); return asl.apply(tg, a); };
      });
      if (typeof tg.showPopup === 'function') {
        var aslPopup = tg.showPopup;
        tg.showPopup = function (p) {
          var a = Array.prototype.slice.call(arguments);
          if (p) {
            a[0] = Object.assign({}, p, { title: p.title && t(p.title), message: p.message && t(p.message),
              buttons: (p.buttons || []).map(function (b) { return Object.assign({}, b, { text: b.text && t(b.text) }); }) });
          }
          return aslPopup.apply(tg, a);
        };
      }
    }
  }

  function ishgaTushir() {
    ishlayapti = true;
    document.documentElement.lang = til === 'ru' ? 'ru' : 'uz';
    dialoglar();
    aylan(document.documentElement);
    sarlavha();
    new MutationObserver(function (ozgarishlar) {
      for (var i = 0; i < ozgarishlar.length; i++) {
        var m = ozgarishlar[i];
        if (m.type === 'characterData') matnTugun(m.target);
        else if (m.type === 'attributes') element(m.target);
        else for (var j = 0; j < m.addedNodes.length; j++) aylan(m.addedNodes[j]);
      }
      sarlavha();
    }).observe(document.documentElement, {
      subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTR,
    });
    document.addEventListener('DOMContentLoaded', function () { dialoglar(); aylan(document.body); sarlavha(); });
  }

  function tilOrnat(yangi) {
    yangi = yangi === 'ru' ? 'ru' : 'uz';
    try { localStorage.setItem(KALIT, yangi); } catch (e) { /* */ }
    til = yangi;
  }

  window.I18N = {
    get til() { return til; },
    t: t,
    /** Admin sozlamalarini (matnlar, ranglar, bloklar) serverdan qayta olib, ochiq sahifaga qo'llaydi. */
    saytYangila: saytYangila,
    ornat: tilOrnat,
    ko: ko,
    /** Serverdagi til (users.lang) bilan moslash (boshqa qurilmada tanlangan bo'lsa):
     * farq qilsa — saqlab, sahifani bir marta qayta yuklaydi. */
    moslash: function (serverTil) {
      if ((serverTil !== 'ru' && serverTil !== 'uz') || serverTil === til) return;
      try {
        localStorage.setItem(KALIT, serverTil);
        if (localStorage.getItem(KALIT) !== serverTil) return;   // saqlanmasa — qayta yuklash aylanib qolmasin
      } catch (e) { return; }
      location.reload();
    },
  };

  if (til === 'ru' || ovrBor) ishgaTushir();
  saytYangila();
})();
