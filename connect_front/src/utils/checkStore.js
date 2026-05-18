import store from '../store'

const checkStore = name => {
    return store.hasModule(name) ? true : false
}

const hasInInjectInit = value => {
    return store.state.config.config.injectInit.includes(value)
}

export {
    checkStore,
    hasInInjectInit
}