// service-worker.js

const CACHE_NAME = 'aguia-florestal-v1';

const urlsToCache = [
  '/',
  '/index.html',
  '/hub.html',
  '/modules/biblioteca/index.html',
  '/modules/checklist/index.html',
  '/modules/os/index.html',
  '/css/styles.css',
  '/js/main.js',
  '/js/core/api.js',
  '/js/core/auth.js',
  '/js/core/config.js',
  '/js/core/db.js',
  '/js/core/sync.js',
  '/js/utils/utils.js',
  '/manifest.json'
];

// INSTALL
self.addEventListener('install', event => {

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache aberto');
        return cache.addAll(urlsToCache);
      })
  );

  self.skipWaiting();

});

// ACTIVATE
self.addEventListener('activate', event => {

  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );

  self.clients.claim();

});

// FETCH
self.addEventListener('fetch', event => {

  if (event.request.method !== 'GET') return;

  const requestUrl = new URL(event.request.url);

  if (
    requestUrl.pathname.startsWith('/api/') ||
    requestUrl.pathname.startsWith('/auth/') ||
    requestUrl.pathname.startsWith('/sync/')
  ) {
    return;
  }

  event.respondWith(

    caches.match(event.request)
      .then(response => {

        if (response) {
          return response;
        }

        return fetch(event.request).then(networkResponse => {

          if (
            networkResponse &&
            networkResponse.status === 200 &&
            networkResponse.type === 'basic'
          ) {

            const responseClone = networkResponse.clone();

            caches.open(CACHE_NAME)
              .then(cache => cache.put(event.request, responseClone));

          }

          return networkResponse;

        });

      })

  );

});