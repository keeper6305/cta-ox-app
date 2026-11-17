/* 세법 OX 서비스 워커 — 앱 셸 오프라인 캐시 */
var CACHE = 'sebeop-ox-v3-rounds';
var ASSETS = ['./', './index.html', './bank.js', './manifest.json',
              './icon-192.png', './icon-512.png', './icon-maskable-512.png', './apple-touch-icon.png'];

self.addEventListener('install', function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){
    return Promise.all(ASSETS.map(function(u){
      return c.add(new Request(u, {cache:'reload'})).catch(function(){});
    }));
  }).then(function(){ return self.skipWaiting(); }));
});

self.addEventListener('activate', function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){ return k !== CACHE; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});

self.addEventListener('fetch', function(e){
  var req = e.request;
  if(req.method !== 'GET') return;
  var url = new URL(req.url);
  if(url.origin !== self.location.origin) return;
  if(req.mode === 'navigate'){
    e.respondWith(fetch(req).then(function(r){
      var cp = r.clone();
      caches.open(CACHE).then(function(c){ c.put('./index.html', cp); });
      return r;
    }).catch(function(){ return caches.match('./index.html'); }));
    return;
  }
  e.respondWith(caches.match(req).then(function(hit){
    if(hit) return hit;
    return fetch(req).then(function(r){
      if(r && r.status === 200 && r.type === 'basic'){
        var cp = r.clone();
        caches.open(CACHE).then(function(c){ c.put(req, cp); });
      }
      return r;
    });
  }));
});
