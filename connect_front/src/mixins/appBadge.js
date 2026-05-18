export const setAppBadge = (c) => { // Установить badge pwa приложения
    try {
        let count = getValueFromObject(c)
        if (count === 0) clearAppBadge()
        else if (navigator.setAppBadge) {
            navigator.setAppBadge(count)
        } else if (navigator.setExperimentalAppBadge) {
            navigator.setExperimentalAppBadge(count)
        } else if (window.ExperimentalBadge) {
            window.ExperimentalBadge.set(count)
        }
    } catch (e) {
        // console.log(e, 'setAppBadge')
    }
}

export const clearAppBadge = () => { // Очистить badge pwa приложения
    try {
        if (navigator.clearAppBadge) {
            navigator.clearAppBadge()
        } else if (navigator.clearExperimentalAppBadge) {
            navigator.clearExperimentalAppBadge()
        } else if (window.ExperimentalBadge) {
            window.ExperimentalBadge.clear()
        }
    } catch (e) {
        // console.log(e, 'clearAppBadge')
    }
}

const getValueFromObject = (object) => {
    let res = 0
    Object.values(object).forEach(el => {
        res += +el
    })
    return res
}