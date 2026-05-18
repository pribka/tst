import { updateTheme } from '@/config/dynamicTheme'
export default {
    SET_CONFIG(state, value) {
        let config = JSON.parse(JSON.stringify(value))

        /*if(config?.sounds) {
            for (let sound in config.sounds) {
                if(typeof config.sounds[sound] === 'string') {
                    config.sounds[sound] = new Audio(config.sounds[sound])
                }
            }
        }*/

        state.config = config
    },
    SET_BANNER_NEWS(state, value) {
        state.bannerNews = value || null
        state.bannerNewsLoaded = true
    },
    SET_PRIMARY_COLOR(state, color) {
        try {
            state.primaryColor = color
            updateTheme(color)
        } catch(e) {
            console.log(e, 'SET_PRIMARY_COLOR')
        }
    }
}
