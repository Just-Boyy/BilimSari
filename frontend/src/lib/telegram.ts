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

/** Telegram Desktop'da initData ba'zan darhol emas, biroz kechikib keladi (bridge orqali),
 * URL fragmentiga bog'liq mobil versiyalardan farqli. Shuning uchun "Telegram ichidamizmi"
 * degan tekshiruv initData'ga emas, platform maydoniga asoslanadi — u initData'dan oldinroq
 * to'ladi. */
export function isRunningInsideTelegram(): boolean {
  const platform = (WebApp as unknown as { platform?: string }).platform;
  return Boolean(platform && platform !== "unknown");
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

export default WebApp;
