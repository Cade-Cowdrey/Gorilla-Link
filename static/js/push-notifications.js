// PSU Connect - Push Notification Client
// Add to your main JavaScript file or include separately

class PushNotifications {
    constructor() {
        this.registration = null;
        this.subscription = null;
    }
    
    async init() {
        // Check if service workers and push are supported
        if (!('serviceWorker' in navigator)) {
            console.log('Service Workers not supported');
            return false;
        }
        
        if (!('PushManager' in window)) {
            console.log('Push notifications not supported');
            return false;
        }
        
        try {
            // Register service worker
            this.registration = await navigator.serviceWorker.register('/static/js/service-worker.js');
            console.log('Service Worker registered');
            
            // Check if already subscribed
            this.subscription = await this.registration.pushManager.getSubscription();
            
            return true;
        } catch (error) {
            console.error('Service Worker registration failed:', error);
            return false;
        }
    }
    
    async subscribe() {
        if (!this.registration) {
            console.error('Service Worker not registered');
            return false;
        }
        
        try {
            // Get VAPID public key from server
            const response = await fetch('/push/vapid-public-key');
            const data = await response.json();
            const vapidPublicKey = data.publicKey;
            
            // Convert to Uint8Array
            const convertedVapidKey = this.urlBase64ToUint8Array(vapidPublicKey);
            
            // Subscribe to push
            this.subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: convertedVapidKey
            });
            
            // Send subscription to server
            const subscribeResponse = await fetch('/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.subscription.toJSON())
            });
            
            const result = await subscribeResponse.json();
            
            if (result.success) {
                console.log('Successfully subscribed to push notifications');
                return true;
            } else {
                console.error('Failed to subscribe on server');
                return false;
            }
        } catch (error) {
            console.error('Push subscription failed:', error);
            return false;
        }
    }
    
    async unsubscribe() {
        if (!this.subscription) {
            return true;
        }
        
        try {
            // Unsubscribe from push
            await this.subscription.unsubscribe();
            
            // Notify server
            await fetch('/push/unsubscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    endpoint: this.subscription.endpoint
                })
            });
            
            this.subscription = null;
            console.log('Unsubscribed from push notifications');
            return true;
        } catch (error) {
            console.error('Unsubscribe failed:', error);
            return false;
        }
    }
    
    async requestPermission() {
        if (Notification.permission === 'granted') {
            return true;
        }
        
        if (Notification.permission === 'denied') {
            alert('Push notifications are blocked. Please enable them in your browser settings.');
            return false;
        }
        
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }
    
    async enablePushNotifications() {
        // Request permission
        const hasPermission = await this.requestPermission();
        if (!hasPermission) {
            return false;
        }
        
        // Initialize if not done
        if (!this.registration) {
            const initialized = await this.init();
            if (!initialized) {
                return false;
            }
        }
        
        // Subscribe
        return await this.subscribe();
    }
    
    async testNotification() {
        try {
            const response = await fetch('/push/test', {
                method: 'POST'
            });
            
            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('Test notification failed:', error);
            return false;
        }
    }
    
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
    
    isSubscribed() {
        return this.subscription !== null;
    }
}

// Create global instance
window.pushNotifications = new PushNotifications();

// Auto-initialize on page load for logged-in users
if (document.querySelector('meta[name="user-authenticated"]')?.content === 'true') {
    window.addEventListener('load', async () => {
        await window.pushNotifications.init();
    });
}

// Helper function to show notification banner
function showNotificationBanner() {
    if (Notification.permission === 'default') {
        const banner = document.createElement('div');
        banner.className = 'notification-banner';
        banner.innerHTML = `
            <div style="background: var(--psu-crimson); color: white; padding: 1rem; text-align: center; position: fixed; top: 0; left: 0; right: 0; z-index: 9999; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                <p style="margin: 0 0 0.5rem 0;">
                    <i class="fas fa-bell"></i> Enable notifications to get instant updates on job matches, messages, and more!
                </p>
                <button onclick="enableNotifications()" class="btn-primary" style="margin-right: 0.5rem; background: white; color: var(--psu-crimson);">
                    Enable Notifications
                </button>
                <button onclick="dismissNotificationBanner()" class="btn-secondary" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid white;">
                    Maybe Later
                </button>
            </div>
        `;
        document.body.appendChild(banner);
    }
}

async function enableNotifications() {
    const success = await window.pushNotifications.enablePushNotifications();
    if (success) {
        alert('Notifications enabled! You\'ll now receive updates.');
        dismissNotificationBanner();
    } else {
        alert('Failed to enable notifications. Please check your browser settings.');
    }
}

function dismissNotificationBanner() {
    const banner = document.querySelector('.notification-banner');
    if (banner) {
        banner.remove();
    }
    // Remember dismissal
    localStorage.setItem('notification-banner-dismissed', 'true');
}

// Show banner after 5 seconds if not dismissed before
window.addEventListener('load', () => {
    if (!localStorage.getItem('notification-banner-dismissed')) {
        setTimeout(showNotificationBanner, 5000);
    }
});
