/* 세법 OX 서비스 워커 — 앱 셸 오프라인 캐시 */
var CACHE = 'sebeop-ox-v15-s2';
var ASSETS = ['./', './index.html', './bank.js?v=15', './manifest.json',
              './icon-192.png', './icon-512.png', './icon-maskable-512.png',
              './apple-touch-icon.png', './favicon-32.png'];

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

/* 앱 셸(index.html)만 오프라인 폴백 대상이다.
   예전에는 모든 내비게이션이 './index.html' 키로 저장돼, qa/ 같은 다른 페이지를 한 번 열면
   앱 껍데기 캐시가 그 페이지로 덮어써졌다. 이제 앱 셸 주소일 때만 캐시에 쓴다. */
function isShell(url){
  return /(^\/$)|(\/index\.html$)/.test(url.pathname);
}

self.addEventListener('fetch', function(e){
  var req = e.request;
  if(req.method !== 'GET') return;
  var url = new URL(req.url);
  if(url.origin !== self.location.origin) return;
  if(req.mode === 'navigate'){
    /* no-cache = ETag로 재검증. 새 빌드가 올라오면 설치된 앱도 다음 실행에 바로 받는다 */
    e.respondWith(fetch(req, {cache:'no-cache'}).then(function(r){
      if(isShell(url) && r && r.ok){
        var cp = r.clone();
        caches.open(CACHE).then(function(c){ c.put('./index.html', cp); });
      }
      return r;
    }).catch(function(){
      return caches.match('./index.html').then(function(hit){
        return hit || new Response('오프라인입니다. 연결한 뒤 다시 열어 주세요.', {
          status: 503, headers: {'Content-Type': 'text/plain; charset=utf-8'}
        });
      });
    }));
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
