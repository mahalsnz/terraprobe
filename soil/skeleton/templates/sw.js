const CACHE_NAME = 'onsite';

const ONSITE_CACHE = ['/'];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
        .then(function(cache) {
            console.log('Cache Opened');
            return cache.addAll(ONSITE_CACHE);
        });
    );
});
