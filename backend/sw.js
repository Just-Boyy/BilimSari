/* BilimSari service worker.

   Qoidalar:
   • /api/* — HECH QACHON keshlanmaydi. Progress, kutish vaqti va natijalar
     doim serverdan olinadi, aks holda eskirgan ma'lumot ko'rsatiladi.
   • HTML — avval tarmoq, ulanish yo'q bo'lsa keshdan.
   • CSS/JS/rasm — avval kesh, orqa fonda yangilanadi.
*/

const CACHE = 'bilimsari-v3';

const ASSETS = [
  '/',
  '/index.html',
  '/login.html',
  '/register.html',
  '/onboarding.html',
  '/dashboard.html',
  '/subjects.html',
  '/topics.html',
  '/topic.html',
  '/progress.html',
  '/profile.html',
  '/manifest.json',
  '/css/app.css',
  '/js/api.js',
  '/js/ui.js',
  '/js/telegram.js',
  '/assets/icon-192.png',
  '/assets/icon-512.png',
  '/assets/apple-touch-icon.png',
  '/assets/apple-touch-icon-180.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((cache) => Promise.allSettled(ASSETS.map((a) => cache.add(a))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function saqlash(request, response) {
  if (response && response.status === 200 && response.type === 'basic') {
    const clone = response.clone();
    caches.open(CACHE).then((cache) => cache.put(request, clone));
  }
  return response;
}

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  if (e.request.method !== 'GET' || url.origin !== self.location.origin) return;

  // API — faqat tarmoq
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/telegram/')) return;

  const htmlmi = e.request.mode === 'navigate' ||
    (e.request.headers.get('accept') || '').includes('text/html');

  if (htmlmi) {
    // Avval tarmoq — sahifa yangilanishi darhol ko'rinsin
    e.respondWith(
      fetch(e.request)
        .then((res) => saqlash(e.request, res))
        .catch(() => caches.match(e.request).then((c) => c || caches.match('/index.html')))
    );
    return;
  }

  // Statik fayllar — avval kesh
  e.respondWith(
    caches.match(e.request).then((cached) => {
      const tarmoq = fetch(e.request)
        .then((res) => saqlash(e.request, res))
        .catch(() => cached);
      return cached || tarmoq;
    })
  );
});
