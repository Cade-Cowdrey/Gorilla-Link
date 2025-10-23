/* PittState-Connect Service Worker (v1) */
const CACHE_NAME = "psu-connect-v1";
const ASSETS = [
  "/",
  "/templates/core/home.html",
  "/static/css/psu-theme.css",
  "/static/images/psu-logo.png"
];

// Install: pre-cache core assets
self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
});

// Activate: cleanup old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
});

// Fetch: network-first for HTML, cache-first for others
self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.headers.get("accept")?.includes("text/html")) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then((r) => r || caches.match("/")))
    );
  } else {
    event.respondWith(
      caches.match(req).then((cached) => cached || fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
        return res;
      }))
    );
  }
});
