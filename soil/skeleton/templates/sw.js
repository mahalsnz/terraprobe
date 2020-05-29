const CACHE_NAME = 'onsite';

const ONSITE_CACHE = ['/static/vendor/select2/dist/css/select2.css'];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            console.log('Cache Opened');
            return cache.addAll([ONSITE_CACHE]);
        })
    );
});
