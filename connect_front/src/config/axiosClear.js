import axios from "axios"
import store from "@/store"

const instance = axios.create()

instance.defaults.timeout = 60000
instance.defaults.withCredentials = true
instance.defaults.xsrfHeaderName = 'X-CSRFToken'
instance.defaults.xsrfCookieName = process.env.VUE_APP_CSRF_NAME

instance.interceptors.response.use(response => response,
    async ({ message, response, config }) => {
        const originalRequest = config
        if(response?.status === 503) {
            originalRequest._retry = true
            await new Promise((resolve) => setTimeout(resolve, 200))
            return instance(originalRequest)
        } else {
            if ((response?.status === 403 || response?.status === 405) && !originalRequest._retry) {
                throw response
                /*
                originalRequest._retry = true
                try{
                    await TokenService.getAccessToken(response.data)
                    return instance(originalRequest)
                } catch (err) {
                    return Promise.reject(err)
                }*/
            }
            if(response?.status === 401) {
                await store.dispatch('user/logout')
                location.reload()
            }
            if (response?.status === 404 || response?.status === 502 || response?.status === 500) {
                throw response
            }
            throw response?.data
        }
    })

instance.interceptors.request.use(
    (config) => {
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

export default instance
