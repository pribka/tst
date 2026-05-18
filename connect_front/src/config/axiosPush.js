import axios from "axios"
import store from "@/store"

const instance = axios.create({
    baseURL: process.env.VUE_APP_PUSH_API_URL
})

instance.defaults.timeout = 60000
instance.defaults.withCredentials = true
instance.defaults.xsrfHeaderName = 'X-CSRFToken'
instance.defaults.xsrfCookieName = process.env.VUE_APP_CSRF_NAME

instance.interceptors.response.use(response => response,
    async ({ message, response: { status, config: { url }, data } }) => {
        if (status === 401) {
            await store.dispatch('user/localUserLogout')
            location.reload()
        }
        throw data
    })

export default instance