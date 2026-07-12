const CACHE_NAME = "opendte-v26";
const DYNAMIC_CACHE = "opendte-dynamic-v26";
const OFFLINE_URL = "/static/offline.html";

// Archivos básicos para que la app cargue el layout principal sin internet
const ASSETS_TO_CACHE = [
  OFFLINE_URL,
  "/static/css/bootstrap.min.css",
  "/static/css/bootstrap-icons.css",
  "/static/css/style.css",
  "/static/js/bootstrap.bundle.min.js",
  "/static/js/localforage.min.js",
  "/static/js/offline-db.js",
  "/static/js/api.js",
  "/static/js/inventario.js",
  "/static/img/logo.webp",
  "/static/img/favicon.ico",
  "/manifest.json",
  // Precarga de Vistas Fundamentales para acceso offline
  "/",
  "/productos/",
  "/clientes/",
  "/facturas/",
  "/despacho/historial/",
];

self.addEventListener("install", (event) => {
  self.skipWaiting(); // Fuerza la actualización del SW inmediatamente
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE)),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(clients.claim()); // Toma el control de los clientes de inmediato
  // Elimina cachés antiguos si cambiamos CACHE_NAME
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== DYNAMIC_CACHE) {
            return caches.delete(cacheName);
          }
        }),
      );
    }),
  );
});

self.addEventListener("fetch", (event) => {
  // Ignorar peticiones que no sean GET (como el POST del formulario offline)
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  const isApiOrDynamic = url.pathname.includes('/api/') || url.pathname.includes('/compartida/');

  // Si la petición es para una API o una ruta del buzón compartido, usamos Network-First
  if (isApiOrDynamic) {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          // Si hay red y todo sale bien, guardamos una copia fresca en caché dinámico
          return caches.open(DYNAMIC_CACHE).then((cache) => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        })
        .catch(() => {
          // Si no hay red, intentamos leer la versión anterior del caché
          return caches.match(event.request);
        })
    );
    return;
  }

  // Si la petición es de navegación (ej. el usuario cambia de página en el sistema)
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          // Si hay red y todo sale bien, guardamos una copia fresca en caché dinámico
          return caches.open(DYNAMIC_CACHE).then((cache) => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        })
        .catch(() => {
          // Si la red falla (apagó los datos/wifi o el server Django cayó), probamos suerte en caché dinámico
          return caches.match(event.request).then((cachedResponse) => {
             // Si el operario ya había visitado esta página, se la mostramos intacta.
             // Si NUNCA la había visitado, le mostramos "offline.html" tristemente.
             return cachedResponse || caches.match(OFFLINE_URL);
          });
        })
    );
  } else {
    // Peticiones de recursos como imágenes, css, js
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request).then((networkResponse) => {
            // Guardamos los assets cargados dinámicamente también
            return caches.open(DYNAMIC_CACHE).then((cache) => {
                cache.put(event.request, networkResponse.clone());
                return networkResponse;
            });
        }).catch(() => {});
      })
    );
  }
});
