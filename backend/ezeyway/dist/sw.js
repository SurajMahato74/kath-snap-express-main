// Service Worker for background notifications
const CACHE_NAME = 'kath-snap-v1';

// Install event
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  event.waitUntil(self.clients.claim());
});

// Background sync for notifications
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync-orders') {
    event.waitUntil(checkForNewOrders());
  }
});

// Push notification event
self.addEventListener('push', (event) => {
  console.log('Push notification received:', event);
  
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { title: 'New Order', body: event.data.text() };
    }
  }

  const options = {
    body: data.body || 'You have a new order!',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    tag: data.tag || 'order-notification',
    requireInteraction: true,
    actions: [
      {
        action: 'view',
        title: 'View Order'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ],
    data: data.data || {}
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'New Order Received!', options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  event.notification.close();

  if (event.action === 'view' || !event.action) {
    // Open the app and focus on orders page
    event.waitUntil(
      self.clients.matchAll({ type: 'window' }).then((clients) => {
        // Check if app is already open
        for (const client of clients) {
          if (client.url.includes('/vendor') && 'focus' in client) {
            client.focus();
            client.postMessage({
              type: 'SHOW_ORDER_MODAL',
              data: event.notification.data
            });
            return;
          }
        }
        
        // If app is not open, open it
        if (self.clients.openWindow) {
          return self.clients.openWindow('/vendor/home');
        }
      })
    );
  }
});

// Message event for communication with main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker received message:', event.data);
  
  if (event.data && event.data.type === 'VISIBILITY_CHANGE') {
    // Handle visibility changes for background notifications
    if (event.data.hidden) {
      // Page is hidden, enable background notifications
      console.log('Page hidden, enabling background notifications');
    } else {
      // Page is visible, disable background notifications
      console.log('Page visible, disabling background notifications');
    }
  }
});

// Function to check for new orders (background sync)
async function checkForNewOrders() {
  try {
    // This would typically make an API call to check for new orders
    // For now, we'll just log that the background sync occurred
    console.log('Background sync: Checking for new orders...');
    
    // In a real implementation, you would:
    // 1. Make an API call to check for new orders
    // 2. Compare with locally stored order IDs
    // 3. Show notifications for new orders
    // 4. Store new order IDs locally
    
    return Promise.resolve();
  } catch (error) {
    console.error('Background sync failed:', error);
    return Promise.reject(error);
  }
}