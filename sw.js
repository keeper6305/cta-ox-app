/* 세법 OX 서비스 워커 — 앱 셸 오프라인 캐시 */
var CACHE = 'sebeop-ox-v19';
var ASSETS = ['./', './index.html', './bank.js?v=19', './manifest.json',
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
  /* 점검 페이지(?qa=1)·qa/ 하위는 서비스 워커를 거치지 않는다 —
     예전 셸 캐시가 QA 화면을 덮어쓰면 새 빌드가 검증되지 않은 채 통과한다 */
  if(/[?&]qa=1/.test(req.url) || /\/qa\//.test(url.pathname)) return;
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
  /* v19: 자산도 network-first(ETag 재검증)로 바꿨다.
     예전 cache-first 는 index 의 ?v= 와 이 CACHE 이름을 함께 올리지 않으면
     bank.js 같은 데이터를 기존 사용자에게 영구 고정시켰다. 이제 배포하면 다음 로드에 바로 반영되고,
     바뀐 게 없으면 304 라 본문을 다시 받지 않는다. 네트워크가 없을 때만 캐시로 대체한다. */
  e.respondWith(fetch(req, {cache:'no-cache'}).then(function(r){
    if(r && r.status === 200 && r.type === 'basic'){
      var cp = r.clone();
      caches.open(CACHE).then(function(c){ c.put(req, cp); });
    }
    return r;
  }).catch(function(){
    return caches.match(req, {ignoreSearch:true}).then(function(hit){
      return hit || Response.error();
    });
  }));
});
