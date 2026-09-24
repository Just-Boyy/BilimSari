// BilimSari — SVG ikonkalar. Saytda emoji ishlatilmaydi.
//
// Ishlatish:
//   BSIcons.icon('home')                → <svg>...</svg>
//   BSIcons.icon('lock', 'nishon')      → class qo'shilgan holda
//   BSIcons.icon('lock', '', 28)        → o'lchamini o'zgartirib
//   BSIcons.shapes('apple', 4)          → 4 ta olma shakli (sanash mashqi uchun)
//
// Barcha ikonkalar `currentColor` dan rang oladi — CSS orqali boshqariladi.

const ICONS = (function () {
  // Chiziqli ikonkalar uchun umumiy o'ram
  function line(body, vb) {
    return '<svg viewBox="' + (vb || '0 0 24 24') + '" fill="none" stroke="currentColor" ' +
      'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ' +
      'aria-hidden="true" focusable="false">' + body + '</svg>';
  }
  // To'ldirilgan ikonkalar uchun
  function solid(body, vb) {
    return '<svg viewBox="' + (vb || '0 0 24 24') + '" fill="currentColor" ' +
      'aria-hidden="true" focusable="false">' + body + '</svg>';
  }

  return {
    // ── Navigatsiya va umumiy ──────────────────────────
    home: line('<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'),
    library: line('<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M9 6h7"/><path d="M9 10h7"/>'),
    chart: line('<line x1="3" y1="21" x2="21" y2="21"/><rect x="5" y="12" width="4" height="8" rx="1"/><rect x="10" y="7" width="4" height="13" rx="1"/><rect x="15" y="3" width="4" height="17" rx="1"/>'),
    user: line('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
    arrowLeft: line('<line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>'),
    chevronRight: line('<polyline points="9 18 15 12 9 6"/>'),
    send: line('<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>'),
    refresh: line('<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>'),
    logout: line('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>'),
    settings: line('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6 1.65 1.65 0 0 0 10 3.09V3a2 2 0 0 1 4 0v.09A1.65 1.65 0 0 0 15 4.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9v0a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'),

    // ── Mavzu bosqichlari ──────────────────────────────
    bookOpen: line('<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>'),
    brain: line('<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/>'),
    pencil: line('<path d="M12 20h9"/><path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838a.5.5 0 0 1-.62-.62l.838-2.872a2 2 0 0 1 .506-.854z"/>'),

    // ── Holatlar ───────────────────────────────────────
    lock: line('<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>'),
    unlock: line('<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/>'),
    clock: line('<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>'),
    check: line('<polyline points="20 6 9 17 4 12"/>'),
    checkCircle: line('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'),
    xCircle: line('<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>'),
    x: line('<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>'),
    play: line('<circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8" fill="currentColor" stroke="none"/>'),
    alert: line('<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'),
    inbox: line('<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>'),
    tools: line('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'),
    sparkle: line('<path d="M12 3v4M12 17v4M3 12h4M17 12h4"/><path d="M6.3 6.3 9 9M15 15l2.7 2.7M17.7 6.3 15 9M9 15l-2.7 2.7"/>'),
    graduation: line('<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5"/>'),
    award: line('<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>'),
    target: line('<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>'),
    moon: line('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'),
    party: line('<path d="M5.8 11.3 2 22l10.7-3.79"/><path d="M4 3h.01M22 8h.01M15 2h.01M22 20h.01"/><path d="M22 2 11 13"/><path d="M11 13 8 8l5-5 5 5-5 5Z"/>'),

    // ── Fanlar ─────────────────────────────────────────
    calc: line('<rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="8" y2="10.01"/><line x1="12" y1="10" x2="12" y2="10.01"/><line x1="16" y1="10" x2="16" y2="10.01"/><line x1="8" y1="14" x2="8" y2="14.01"/><line x1="12" y1="14" x2="12" y2="14.01"/><line x1="16" y1="14" x2="16" y2="14.01"/><line x1="8" y1="18" x2="16" y2="18"/>'),
    divide: line('<circle cx="12" cy="6" r="1.4" fill="currentColor"/><line x1="5" y1="12" x2="19" y2="12"/><circle cx="12" cy="18" r="1.4" fill="currentColor"/>'),
    ruler: line('<path d="M21.3 8.7 8.7 21.3a1 1 0 0 1-1.4 0l-4.6-4.6a1 1 0 0 1 0-1.4L15.3 2.7a1 1 0 0 1 1.4 0l4.6 4.6a1 1 0 0 1 0 1.4Z"/><path d="m7.5 10.5 2 2M10.5 7.5l2 2M13.5 4.5l2 2M4.5 13.5l2 2"/>'),
    book: line('<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>'),
    scroll: line('<path d="M8 21h12a2 2 0 0 0 2-2v-2H10v2a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v3h4"/><path d="M19 17V5a2 2 0 0 0-2-2H4"/>'),
    leaf: line('<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>'),
    lang: line('<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'),
    chat: line('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'),
    landmark: line('<line x1="3" y1="22" x2="21" y2="22"/><line x1="6" y1="18" x2="6" y2="11"/><line x1="10" y1="18" x2="10" y2="11"/><line x1="14" y1="18" x2="14" y2="11"/><line x1="18" y1="18" x2="18" y2="11"/><polygon points="12 2 20 7 4 7"/>'),
    map: line('<polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/>'),
    atom: line('<circle cx="12" cy="12" r="1.2" fill="currentColor"/><ellipse cx="12" cy="12" rx="10" ry="4.5"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(120 12 12)"/>'),
    flask: line('<path d="M10 2v6.5L4.8 17.2A2 2 0 0 0 6.5 20h11a2 2 0 0 0 1.7-2.8L14 8.5V2"/><line x1="9" y1="2" x2="15" y2="2"/><line x1="7" y1="15" x2="17" y2="15"/>'),
    dna: line('<path d="M2 15c6.667-6 13.333 0 20-6"/><path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/><path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"/><path d="m17 6-2.5-2.5"/><path d="m14 8-1-1"/><path d="m7 18 2.5 2.5"/><path d="m3.5 14.5.5.5"/><path d="m20 9 .5.5"/><path d="m6.5 12.5 1 1"/><path d="m16.5 10.5 1 1"/><path d="m10 16 1.5 1.5"/>'),
    code: line('<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>'),
    scales: line('<path d="M12 3v18"/><path d="M7 21h10"/><path d="M5 7h14"/><path d="M5 7 2 14h6L5 7Z"/><path d="M19 7l-3 7h6l-3-7Z"/>'),

    // ── Eski sahifalar uchun saqlangan ─────────────────
    flame: line('<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>'),
    zap: line('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'),
    // Ionicons "flash-outline"
    chaqmoq: '<svg viewBox="0 0 512 512" fill="none" stroke="currentColor" stroke-width="32" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' +
      '<path d="M315.27 33L96 304h128l-31.51 173.23a2.36 2.36 0 0 0 2.33 2.77h0a2.36 2.36 0 0 0 1.89-.95L416 208H288l31.66-173.25a2.45 2.45 0 0 0-2.44-2.75h0a2.42 2.42 0 0 0-1.95 1z"/></svg>',
    heart: solid('<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'),
    heartEmpty: line('<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'),
    gem: line('<path d="M6 3h12l4 6-10 13L2 9z"/><path d="M2 9h20"/><path d="M12 22V9"/><path d="m6 3 4 6"/><path d="m18 3-4 6"/>'),
    trophy: line('<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/>'),
    star: solid('<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>'),
    dumbbell: line('<path d="m6.5 6.5 11 11"/><path d="m21 21-1-1"/><path d="m3 3 1 1"/><path d="m18 22 4-4"/><path d="m2 6 4-4"/><path d="m3 10 7-7"/><path d="m14 21 7-7"/>'),
    pen: line('<path d="M12 20h9"/><path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838a.5.5 0 0 1-.62-.62l.838-2.872a2 2 0 0 1 .506-.854z"/>'),
    medal: line('<path d="M7.21 15 2.66 7.14a2 2 0 0 1 .13-2.2L4.4 2.8A2 2 0 0 1 6 2h12a2 2 0 0 1 1.6.8l1.6 2.14a2 2 0 0 1 .14 2.2L17.21 15"/><path d="M11 12 5.12 2.2"/><path d="m13 12 5.88-9.8"/><path d="M8 7h8"/><circle cx="12" cy="17" r="5"/>'),

    // ── Geometrik shakllar (dars sarlavhalari uchun) ───
    shapeCircle: line('<circle cx="12" cy="12" r="9"/>'),
    shapeTriangle: line('<polygon points="12 3 22 20 2 20"/>'),
    shapeSquare: line('<rect x="4" y="4" width="16" height="16" rx="1"/>'),
    shapeRect: line('<rect x="2" y="7" width="20" height="10" rx="1"/>'),

    // ── Girih yulduzi (brend belgisi) ──────────────────
    girih: '<svg viewBox="0 0 72 72" fill="currentColor" aria-hidden="true" focusable="false">' +
      '<path d="M36 4l8.5 16.5L63 23l-13.5 12L53 54l-17-9-17 9 3.5-19L9 23l18.5-2.5z"/></svg>',
  };
})();

// ── Sanash mashqlari uchun shakllar ───────────────────
// Bolalar 1-sinfda narsalarni sanaydi — emoji o'rniga shu shakllar chiziladi.
const BS_SHAPES = {
  apple: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<path d="M16 9c-1.2-2-3.4-3-5.6-2.6C7.4 7 5 9.9 5 14c0 5.6 4 12 8 12 1.1 0 2-.5 3-.5s1.9.5 3 .5c4 0 8-6.4 8-12 0-4.1-2.4-7-5.4-7.6C19.4 6 17.2 7 16 9Z" fill="#E2574C"/>' +
    '<path d="M16 9c0-2.2.9-4.2 2.6-5.4" stroke="#6B4A2F" stroke-width="1.8" fill="none" stroke-linecap="round"/>' +
    '<path d="M17.5 5.5c1.8-1.3 4-1.3 5.5 0-1 1.9-3.4 2.6-5.5 1.6Z" fill="#4B9B52"/></svg>',
  star: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<polygon points="16 3 20 12 30 13 22.5 19.6 25 29.5 16 24.3 7 29.5 9.5 19.6 2 13 12 12" fill="#E2A03F"/></svg>',
  bird: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<path d="M6 20c0-5 4-9 9-9 3.5 0 6.5 2 8 5l5 2-5 1.5c-1 3.7-4.4 6.5-8.4 6.5C9.6 26 6 23.3 6 20Z" fill="#1D9FA8"/>' +
    '<circle cx="19" cy="16" r="1.3" fill="#16283C"/>' +
    '<path d="m26 18 4-1.5-4-1.5z" fill="#E2A03F"/>' +
    '<path d="M13 13c-1-3 .5-5.5 2.5-6.5-.3 2.3.3 4.2 1.5 5.5z" fill="#16808A"/></svg>',
  circle: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<circle cx="16" cy="16" r="12" fill="none" stroke="#1D9FA8" stroke-width="3"/></svg>',
  square: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<rect x="5" y="5" width="22" height="22" rx="2" fill="none" stroke="#4F7DF3" stroke-width="3"/></svg>',
  triangle: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<polygon points="16 4 29 27 3 27" fill="none" stroke="#C1544A" stroke-width="3" stroke-linejoin="round"/></svg>',
  rectangle: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<rect x="3" y="9" width="26" height="14" rx="2" fill="none" stroke="#8E44AD" stroke-width="3"/></svg>',
  drop: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<path d="M16 3c5 7 8 11 8 15a8 8 0 0 1-16 0c0-4 3-8 8-15Z" fill="#1D9FA8"/></svg>',
  sun: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<circle cx="16" cy="16" r="7" fill="#E2A03F"/>' +
    '<g stroke="#E2A03F" stroke-width="2.4" stroke-linecap="round">' +
    '<path d="M16 2v4M16 26v4M2 16h4M26 16h4M6 6l3 3M23 23l3 3M26 6l-3 3M9 23l-3 3"/></g></svg>',
  snow: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<g stroke="#4F7DF3" stroke-width="2.2" stroke-linecap="round">' +
    '<path d="M16 3v26M5 9.5l22 13M27 9.5l-22 13"/>' +
    '<path d="m12 6 4 3 4-3M12 26l4-3 4 3"/></g></svg>',
  leaf: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<path d="M26 5C13 5 6 11 6 20c0 3 1 5 1 5s10-1 15-6c4-4 4-14 4-14Z" fill="#2E9E5B"/>' +
    '<path d="M24 7 8 24" stroke="#1B6B3A" stroke-width="1.6" fill="none" stroke-linecap="round"/></svg>',
  cloud: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<path d="M9 24a6 6 0 0 1-.6-12 8 8 0 0 1 15.3 2.2A5 5 0 0 1 23 24Z" fill="#8496AB"/></svg>',
  fish: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<path d="M4 16c4-6 10-8 15-8 3 0 6 1 8 3-2 3-2 7 0 10-2 2-5 3-8 3-5 0-11-2-15-8Z" fill="#1D9FA8"/>' +
    '<circle cx="22" cy="14" r="1.4" fill="#16283C"/>' +
    '<path d="M4 16 1 10v12Z" fill="#16808A"/></svg>',
  bug: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<ellipse cx="16" cy="18" rx="7" ry="9" fill="#C1544A"/>' +
    '<circle cx="16" cy="8" r="4" fill="#16283C"/>' +
    '<g stroke="#16283C" stroke-width="1.8" stroke-linecap="round">' +
    '<path d="M9 14 4 11M9 18H3M9 22l-5 3M23 14l5-3M23 18h6M23 22l5 3"/></g>' +
    '<path d="M16 9v18" stroke="#7E2F28" stroke-width="1.6"/></svg>',
  cow: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<ellipse cx="16" cy="17" rx="11" ry="8" fill="#F2F4F7" stroke="#16283C" stroke-width="1.6"/>' +
    '<ellipse cx="11" cy="15" rx="3" ry="2.4" fill="#16283C"/>' +
    '<ellipse cx="21" cy="20" rx="2.6" ry="2" fill="#16283C"/>' +
    '<ellipse cx="16" cy="24" rx="4" ry="2.6" fill="#E9A7A7" stroke="#16283C" stroke-width="1.2"/>' +
    '<circle cx="14.5" cy="24" r=".7" fill="#16283C"/><circle cx="17.5" cy="24" r=".7" fill="#16283C"/></svg>',
  soil: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<rect x="3" y="12" width="26" height="16" rx="2" fill="#8A6642"/>' +
    '<path d="M3 12h26" stroke="#5E432B" stroke-width="2"/>' +
    '<circle cx="9" cy="19" r="1.6" fill="#6B4E31"/><circle cx="18" cy="22" r="1.3" fill="#6B4E31"/>' +
    '<circle cx="23" cy="17" r="1.5" fill="#6B4E31"/></svg>',
  wind: '<svg viewBox="0 0 32 32" fill="none" stroke="#8496AB" stroke-width="2.4" stroke-linecap="round" aria-hidden="true" focusable="false">' +
    '<path d="M3 11h15a4 4 0 1 0-4-4"/><path d="M3 17h20a4 4 0 1 1-4 4"/><path d="M3 23h11"/></svg>',
  flower: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<g fill="#E8709E">' +
    '<circle cx="16" cy="8" r="4.6"/><circle cx="16" cy="20" r="4.6"/>' +
    '<circle cx="10" cy="14" r="4.6"/><circle cx="22" cy="14" r="4.6"/></g>' +
    '<circle cx="16" cy="14" r="3.2" fill="#E2A03F"/>' +
    '<path d="M16 24v6" stroke="#2E9E5B" stroke-width="2.2" stroke-linecap="round"/></svg>',
  sprout: '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">' +
    '<path d="M16 29V14" stroke="#2E9E5B" stroke-width="2.4" stroke-linecap="round"/>' +
    '<path d="M16 16C10 16 7 13 7 8c5 0 9 3 9 8Z" fill="#2E9E5B"/>' +
    '<path d="M16 19c6 0 9-3 9-8-5 0-9 3-9 8Z" fill="#3FB86C"/></svg>',
};

/** Ikonka HTML si. */
function icon(name, cls, size) {
  var svg = ICONS[name] || ICONS.star;
  var atr = '';
  if (cls) atr += ' class="' + cls + '"';
  if (size) atr += ' width="' + size + '" height="' + size + '"';
  return atr ? svg.replace('<svg ', '<svg' + atr + ' ') : svg;
}

/** n ta shakl — sanash mashqlari uchun. */
function shapes(name, n, cls) {
  var bitta = BS_SHAPES[name] || BS_SHAPES.circle;
  var out = '';
  for (var i = 0; i < Math.max(0, Math.min(n || 0, 20)); i++) out += bitta;
  return '<span class="shakllar ' + (cls || '') + '" role="img" aria-label="' +
    (n || 0) + ' ta">' + out + '</span>';
}

window.BSIcons = { icon: icon, shapes: shapes, ICONS: ICONS, SHAPES: BS_SHAPES };
