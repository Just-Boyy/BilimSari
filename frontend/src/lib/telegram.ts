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

/** MUHIM: window.Telegram.WebApp'ning mavjudligi Telegram ichidamizligimizni ISBOTLAMAYDI —
 * @twa-dev/sdk o'zi shu obyektni polyfill sifatida har doim yaratadi (oddiy brauzerda ham).
 * Haqiqiy signal — "platform" yoki "initData"ning to'lishi, ular esa native bridge orqali
 * (ayniqsa Telegram Desktop'da) kechikib keladi. Shuning uchun ikkalasini ham birgalikda,
 * darhol emas, qisqa vaqt kutib tekshiramiz — pastdagi waitForTelegramReady() orqali. */
export async function waitForTelegramReady(
  timeoutMs = 3000,
  intervalMs = 100,
): Promise<{ insideTelegram: boolean; initData: string }> {
  const start = Date.now();
  while (true) {
    const initData = WebApp.initData;
    if (initData) return { insideTelegram: true, initData };

    const platform = (WebApp as unknown as { platform?: string }).platform;
    const insideTelegram = Boolean(platform && platform !== "unknown");

    if (Date.now() - start >= timeoutMs) return { insideTelegram, initData: "" };
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
