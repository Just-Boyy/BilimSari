import WebApp from "@twa-dev/sdk";

/** Telegram WebApp'ni ishga tayyorlaydi va themeParams/colorScheme'ga qarab
 * <html>'ga 'dark' klassini qo'yadi (brend yashili har doim aksent bo'lib qoladi —
 * bu CSS token darajasida qattiq belgilangan, temaga bog'liq emas). */
export function initTelegramTheme(): void {
  try {
    WebApp.ready();
    WebApp.expand();
    applyColorScheme();
    WebApp.onEvent("themeChanged", applyColorScheme);
  } catch {
    // Brauzerda (Telegram tashqarisida) ishga tushirilganda WebApp API mavjud bo'lmasligi mumkin.
  }
}

function applyColorScheme(): void {
  const isDark = WebApp.colorScheme === "dark";
  document.documentElement.classList.toggle("dark", isDark);
}

export function getInitData(): string {
  return WebApp.initData ?? "";
}

export function getTelegramLanguageCode(): string | undefined {
  return WebApp.initDataUnsafe?.user?.language_code;
}

/** Telegram Desktop'da "platform" maydoni ham (initData kabi) kechikib to'ladi — shu sababli
 * unga asoslanish noto'g'ri xato beradi. window.Telegram.WebApp esa rasmiy telegram-web-app.js
 * skripti orqali sahifa yuklanishi bilanoq sinxron o'rnatiladi (index.html <head>'da), shuning
 * uchun "Telegram ichidamizmi" tekshiruvi shu obyektning mavjudligiga asoslanadi. */
export function isRunningInsideTelegram(): boolean {
  const telegram = (window as unknown as { Telegram?: { WebApp?: unknown } }).Telegram;
  return Boolean(telegram?.WebApp);
}

/** initData Telegram Desktop'da kechikib kelishi mumkin (WebApp brauzer bridge orqali
 * asinxron beriladi) — shu sababli darhol bo'sh bo'lsa ham, qisqa vaqt kutib, qayta
 * tekshiramiz. Mobil klientlarda odatda birinchi urinishdayoq to'ladi. */
export async function waitForInitData(timeoutMs = 3000, intervalMs = 100): Promise<string> {
  const start = Date.now();
  while (true) {
    const data = WebApp.initData;
    if (data) return data;
    if (Date.now() - start >= timeoutMs) return "";
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}

/** Vaqtinchalik diagnostika uchun — Telegram Desktop'da nima uzatilayotganini ekranda
 * ko'rish imkonini beradi (DevTools ochish qiyin bo'lgan muhitlarda). */
export function getDebugInfo(): string {
  const w = WebApp as unknown as { platform?: string; version?: string };
  return `platform=${w.platform ?? "?"} version=${w.version ?? "?"} initDataLen=${WebApp.initData?.length ?? 0} hasTelegramObj=${Boolean(
    (window as unknown as { Telegram?: unknown }).Telegram,
  )} ua=${navigator.userAgent.slice(0, 60)}`;
}

export default WebApp;
