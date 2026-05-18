import axios from "axios"
import Buffer from 'buffer'
import store from "@/store"

const BASE_URL = process.env.VUE_APP_API_URL
const REFRESH_ENDPOINT = '/users/token/refresh/'

const userLogount = async () => {
    //await store.dispatch('user/localUserLogout')
    //location.reload()
}

const getAccessToken = async (data) => {
    let token = localStorage.getItem('access_token')

    if(!token || data?.code === 'token_not_valid')
        token = await getNewToken()

    if(!token)
        return false

    return checkExpire(token)
}


const getRefreshToken = () => {
    const refresh = localStorage.getItem('refresh_token')
    return !refresh ? false : refresh
}

const getAllTokens = () => {
    return {
        access: localStorage.getItem('access_token'),
        refresh: localStorage.getItem('refresh_token')
    }
}

const decodeToken = async (token) => {
    try {
        const splited = token.split('.')
        return JSON.parse(Buffer.Buffer.from(splited[1], 'base64').toString('utf8'))
    } catch(e) {
        console.log(e)
        await userLogount()
    }
}

const checkExpire = async (token) => {
    try{
        const payload = decodeToken(token)
        const now = Math.ceil(Date.now() / 1000)

        if(payload.exp <= now)
            return await getNewToken()

        return token
    } catch(e) {
        console.log(e, 'checkExpire')
        return false
    }
}

const getNewToken = async () => {
    const refresh = await getRefreshToken()

    if(!refresh)
        return false;

    try{
        const {data} = await axios({
            url: `${BASE_URL}${REFRESH_ENDPOINT}`,
            method: 'POST',
            data: {
                refresh: refresh
            }
        })

        if(window?.ReactNativeWebView) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
                type: 'refreshToken',
                access: data.access,
                refresh: data.refresh
            }))
        }

        localStorage.setItem('access_token', data.access)
        localStorage.setItem('refresh_token', data.refresh)

        return data.access
    } catch(error) {
        console.log(error, 'getNewToken')
        await userLogount()
        return false
    }
}

const checkAllToken = async () => {
    const user = store.state.user.user
    const tokens = getAllTokens()

    if(user) {
        if(!tokens.refresh) {
            await userLogount()
            return false
        }
    }
    
    return true
}

const TokenService = {
    getAccessToken,
    getRefreshToken,
    decodeToken,
    getAllTokens,
    checkAllToken
}

export default TokenService
