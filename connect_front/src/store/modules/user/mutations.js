import Vue from 'vue'
import moment from 'moment'
import { i18n } from '@/config/i18n-setup'
export default {
    SET_USER(state, value) {
        state.user = {
            ...state.user,
            ...value
        }
    },
    CHANGE_USER_ORG(state, value) {
        state.user.current_contractor = value
    },
    SET_USER_AUTH(state, value) {
        state.usersAuth = JSON.parse(value)
    },
    SET_REDIRECT_LANG(state) {
        localStorage.setItem('redirectLang', i18n?.locale || 'ru')
    },
    SETTING_DRAWER_TOGGLE(state, value) {
        state.settingVisible = value
    },
    SET_DEFAULT_TAB_KEY(state, value) {
        state.defaultTabKey = value
    },
    SET_PROFILE_MENU(state, value) {
        state.profileMenu = value
    },
    SET_AVATAR(state, avatar) {
        if (state.user)
            state.user.avatar = avatar
    },
    DISABLE_PASS_GENERATE(state) {
        state.user.password_generated = false
    },
    SET_ONLINE_USER(state, {user}) {
        const find = state.onlineUsers.find(f => f === user)
        if(!find)
            state.onlineUsers.push(user)

        const index2 = state.offlineUser.findIndex(f => f.id === user)
        if(index2 !== -1)
            Vue.delete(state.offlineUser, index2)
    },
    SET_ONLINE_USERS(state, users = []) {
        users.forEach(user => {
            const find = state.onlineUsers.find(f => f === user)
            if(!find)
                state.onlineUsers.push(user)

            const index = state.offlineUser.findIndex(f => f.id === user)
            if(index !== -1)
                Vue.delete(state.offlineUser, index)
        })
    },
    SET_OFFLINE_USER(state, {user}) {
        const index = state.onlineUsers.findIndex(f => f === user)
        if(index !== -1)
            Vue.delete(state.onlineUsers, index)

        const usState = {
            id: user,
            date: moment().format()
        }
        const index2 = state.offlineUser.findIndex(f => f.id === user)
        if(index2 !== -1) {
            Vue.set(state.offlineUser, index2, usState)
        } else {
            state.offlineUser.push(usState)
        }
    },
    SET_ONLINE_USER_EVENT(state, user) {
        const find2 = state.firstOnlineCheck.find(f => f === user.id)
        if(!find2)
            state.firstOnlineCheck.push(user.id)

        if(user?.online) {
            const find = state.onlineUsers.find(f => f === user.id)
            if(!find)
                state.onlineUsers.push(user.id)
        }
    },
    SET_REG_STEP(state, value) {
        state.regStep = value
    },
    SET_AUTH_CONFIG(state, value) {
        state.authConfig = value
    }
}
