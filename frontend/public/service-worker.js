/**
 * Service Worker for Push Notifications
 * Placeholder for future push notification support
 */

// Service Worker version
const CACHE_VERSION = 'v1'
const CACHE_NAME = `todo-app-${CACHE_VERSION}`

// Install event - cache essential assets
self.addEventListener('install', function(event) {
  console.log('[Service Worker] Installing service worker...')

  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      console.log('[Service Worker] Caching essential assets')
      return cache.addAll([
        '/',
        '/icon.png',
        '/badge.png',
      ]).catch(function(error) {
        console.error('[Service Worker] Cache failed:', error)
      })
    })
  )

  // Force the waiting service worker to become the active service worker
  self.skipWaiting()
})

// Activate event - clean up old caches
self.addEventListener('activate', function(event) {
  console.log('[Service Worker] Activating service worker...')

  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cacheName)
            return caches.delete(cacheName)
          }
        })
      )
    })
  )

  // Claim all clients immediately
  return self.clients.claim()
})

// Push event - handle push notifications
self.addEventListener('push', function(event) {
  console.log('[Service Worker] Push notification received')

  let notificationData = {
    title: 'Task Reminder',
    body: 'You have a task reminder',
    icon: '/icon.png',
    badge: '/badge.png',
    tag: 'task-reminder',
    requireInteraction: false,
    data: {}
  }

  // Parse push data if available
  if (event.data) {
    try {
      const data = event.data.json()
      notificationData = {
        title: data.title || notificationData.title,
        body: data.body || notificationData.body,
        icon: data.icon || notificationData.icon,
        badge: data.badge || notificationData.badge,
        tag: data.tag || notificationData.tag,
        requireInteraction: data.requireInteraction || false,
        data: data.data || {}
      }
    } catch (error) {
      console.error('[Service Worker] Error parsing push data:', error)
      notificationData.body = event.data.text()
    }
  }

  event.waitUntil(
    self.registration.showNotification(notificationData.title, {
      body: notificationData.body,
      icon: notificationData.icon,
      badge: notificationData.badge,
      tag: notificationData.tag,
      requireInteraction: notificationData.requireInteraction,
      data: notificationData.data,
      vibrate: [200, 100, 200],
      actions: [
        {
          action: 'view',
          title: 'View Task'
        },
        {
          action: 'dismiss',
          title: 'Dismiss'
        }
      ]
    })
  )
})

// Notification click event - handle user interaction
self.addEventListener('notificationclick', function(event) {
  console.log('[Service Worker] Notification clicked:', event.action)

  event.notification.close()

  if (event.action === 'view') {
    // Open the app and navigate to task
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
        // Check if app is already open
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i]
          if (client.url.includes('/tasks') && 'focus' in client) {
            return client.focus()
          }
        }

        // Open new window if not already open
        if (clients.openWindow) {
          const taskId = event.notification.data?.taskId
          const url = taskId ? `/tasks?taskId=${taskId}` : '/tasks'
          return clients.openWindow(url)
        }
      })
    )
  } else if (event.action === 'dismiss') {
    // Just close the notification (already closed above)
    console.log('[Service Worker] Notification dismissed')
  } else {
    // Default action - open app
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then(function(clientList) {
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i]
          if ('focus' in client) {
            return client.focus()
          }
        }

        if (clients.openWindow) {
          return clients.openWindow('/tasks')
        }
      })
    )
  }
})

// Notification close event
self.addEventListener('notificationclose', function(event) {
  console.log('[Service Worker] Notification closed:', event.notification.tag)
})

// Fetch event - network-first strategy for API calls, cache-first for assets
self.addEventListener('fetch', function(event) {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return
  }

  // Skip chrome-extension and other non-http(s) requests
  if (!event.request.url.startsWith('http')) {
    return
  }

  // Network-first for API calls
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(function(response) {
          return response
        })
        .catch(function(error) {
          console.error('[Service Worker] Fetch failed for API:', error)
          return new Response(
            JSON.stringify({ error: 'Network error' }),
            {
              status: 503,
              headers: { 'Content-Type': 'application/json' }
            }
          )
        })
    )
    return
  }

  // Cache-first for assets
  event.respondWith(
    caches.match(event.request).then(function(response) {
      if (response) {
        return response
      }

      return fetch(event.request).then(function(response) {
        // Don't cache if not a valid response
        if (!response || response.status !== 200 || response.type === 'error') {
          return response
        }

        // Clone the response
        const responseToCache = response.clone()

        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(event.request, responseToCache)
        })

        return response
      })
    })
  )
})

// Message event - handle messages from client
self.addEventListener('message', function(event) {
  console.log('[Service Worker] Message received:', event.data)

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})
