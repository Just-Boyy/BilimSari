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

/** Vaqtinchalik diagnostika uchun — Telegram Desktop'da nima uzatilayotganini ekranda
 * ko'rish imkonini beradi (DevTools ochish qiyin bo'lgan muhitlarda). */
export function getDebugInfo(): string {
  const w = WebApp as unknown as { platform?: string; version?: string };
  return `platform=${w.platform ?? "?"} version=${w.version ?? "?"} initDataLen=${WebApp.initData?.length ?? 0} hasTelegramObj=${Boolean(
    (window as unknown as { Telegram?: unknown }).Telegram,
  )} ua=${navigator.userAgent.slice(0, 60)}`;
}

export default WebApp;
