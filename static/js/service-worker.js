// PSU Connect Service Worker for Push Notifications

self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    event.waitUntil(clients.claim());
});

self.addEventListener('push', (event) => {
    console.log('Push notification received');
    
    if (!event.data) {
        return;
    }
    
    const data = event.data.json();
    
    const options = {
        body: data.body,
        icon: data.icon || '/static/img/psu-logo.png',
        badge: data.badge || '/static/img/psu-badge.png',
        data: data.data || {},
        requireInteraction: data.requireInteraction || false,
        vibrate: [200, 100, 200],
        actions: [
            {
                action: 'view',
                title: 'View',
                icon: '/static/img/icons/eye.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/img/icons/close.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked');
    
    event.notification.close();
    
    if (event.action === 'dismiss') {
        return;
    }
    
    // Open the URL from notification data
    const url = event.notification.data.url || '/';
    const fullUrl = self.location.origin + url;
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Check if there's already a window open
                for (const client of clientList) {
                    if (client.url === fullUrl && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(fullUrl);
                }
            })
    );
});

self.addEventListener('notificationclose', (event) => {
    console.log('Notification closed');
});
