importScripts(
  "https://www.gstatic.com/firebasejs/10.13.2/firebase-app-compat.js"
);

importScripts(
  "https://www.gstatic.com/firebasejs/10.13.2/firebase-messaging-compat.js"
);

firebase.initializeApp({
  apiKey: "AIzaSyBEe7zXias071A2GhfZjo9ACQOHCH5MmeY",
  authDomain: "astro-mobile-notifications.firebaseapp.com",
  projectId: "astro-mobile-notifications",
  storageBucket: "astro-mobile-notifications.firebasestorage.app",
  messagingSenderId: "399578007574",
  appId: "1:399578007574:web:f0aa8d63b81b64a5dc0d37"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const title =
    payload.notification?.title ||
    payload.data?.title ||
    "طلب جديد - ASTRO MOBILE";

  const options = {
    body:
      payload.notification?.body ||
      payload.data?.body ||
      "لديك إشعار جديد من المتجر.",
    icon: "./icon-192.png",
    data: {
      url: "https://kabar90.github.io/astro-mobile/admin/"
    }
  };

  self.registration.showNotification(title, options);
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const url =
    event.notification.data?.url ||
    "https://kabar90.github.io/astro-mobile/admin/";

  event.waitUntil(
    clients.matchAll({
      type: "window",
      includeUncontrolled: true
    }).then((windowClients) => {
      for (const client of windowClients) {
        if ("focus" in client) {
          return client.focus().then(() => client.navigate(url));
        }
      }

      return clients.openWindow(url);
    })
  );
});
