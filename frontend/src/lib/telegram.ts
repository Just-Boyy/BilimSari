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

/** @twa-dev/sdk'ning WebApp.initData/platform getter'lari — sahifa birinchi yuklanganda
 * location.hash'dan BIR MARTA o'qib keshlangan qiymatlar (Object.defineProperty get orqali
 * qaytariladi, lekin qiymat o'zi bir martalik parse natijasi). Telegram Desktop'da hash
 * (#tgWebAppData=...) sahifa skripti ishga tushgandan BIRO OZ KEYIN biriktiriladi — shuning
 * uchun SDK'ning bir martalik parse'i uni butunlay o'tkazib yuboradi va keyin hech qachon
 * yangilanmaydi (getter reaktiv emas). Shu sababli bu yerda location.hash'ni SDK keshiga
 * tayanmasdan, har safar o'zimiz to'g'ridan-to'g'ri qayta o'qiymiz. */
function parseHashParam(name: string): string {
  const hash = location.hash.startsWith("#") ? location.hash.slice(1) : location.hash;
  return new URLSearchParams(hash).get(name) ?? "";
}

export async function waitForTelegramReady(
  timeoutMs = 3000,
  intervalMs = 100,
): Promise<{ insideTelegram: boolean; initData: string }> {
  const start = Date.now();
  while (true) {
    const initData = WebApp.initData || parseHashParam("tgWebAppData");
    if (initData) return { insideTelegram: true, initData };

    const platform = (WebApp as unknown as { platform?: string }).platform || parseHashParam("tgWebAppPlatform");
    const insideTelegram = Boolean(platform && platform !== "unknown");

    if (Date.now() - start >= timeoutMs) return { insideTelegram, initData: "" };
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}

/** Vaqtinchalik diagnostika uchun — Telegram Desktop'da nima uzatilayotganini ekranda
 * ko'rish imkonini beradi (DevTools ochish qiyin bo'lgan muhitlarda).
 * hash/href — platform/initData asosida URL hash fragmentidan (#tgWebAppData=...) olinadi,
 * shuning uchun bu hash bo'shmi yoki yo'qmi aynan shu ikkalasi bo'sh bo'lish sababini ko'rsatadi. */
export function getDebugInfo(): string {
  const w = WebApp as unknown as { platform?: string; version?: string };
  return `platform=${w.platform ?? "?"} version=${w.version ?? "?"} initDataLen=${WebApp.initData?.length ?? 0} hasTelegramObj=${Boolean(
    (window as unknown as { Telegram?: unknown }).Telegram,
  )} hashLen=${location.hash.length} hash=${location.hash.slice(0, 40)} href=${location.href.slice(0, 60)} ua=${navigator.userAgent.slice(0, 40)}`;
}

export default WebApp;
