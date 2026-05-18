import { register } from 'register-service-worker'

if (process.env.NODE_ENV === 'production') {
    register(`${process.env.BASE_URL}service-worker.js`, {
        ready () {
            console.log(
                'App is being served from cache by a service worker.\n' +
        'For more details, visit https://goo.gl/AFskqB'
            )
        },
        registered () {
            console.log('%c Service worker has been registered ✅', 'color: #52c41a')
        },
        cached () {
            console.log('%c Content has been cached for offline use. 📥', 'color: #7367f0')
        },
        updatefound () {
            console.log('%c New content is downloading. 🤘', 'color: #7367f0')
        },
        updated(registration) {
            window.__swRegistration__ = registration
            try {
                if (registration && registration.waiting) {
                    registration.waiting.postMessage({ type: 'SKIP_WAITING' })
                }
                const onControllerChange = () => {
                    navigator.serviceWorker.removeEventListener('controllerchange', onControllerChange)
                    window.location.reload()
                }
                navigator.serviceWorker.addEventListener('controllerchange', onControllerChange)
            } catch (e) {}
        },
        offline () {
            console.log('%c No internet connection found. App is running in offline mode. ⛔️', 'color: #7367f0')
        },
        error (error) {
            console.error('Error during service worker registration:', error)
        }
    })
}

