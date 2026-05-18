export default {
    getPushRouterByKey: (state) => (key) => {
        return state.pushRoutes.filter(f => f.name === key).length
    },
    getRouteByName: state => name => {
        let route = null
        state.appRoute.forEach(r => {
            if(r.children?.length) {
                const find = r.children.find(c => c.name === name)
                if(find)
                    route = find
            }
        })
        
        return route
    },
    getMenuCounter: state => name => {
        if(state.counterLink?.[name])
            return state.counterLink[name]
        else
            return null
    },
    getRouteInfo: state => name => {
        if(Object.keys(state.routeInfo)?.length) {
            return state.routeInfo[name] ? state.routeInfo[name] : null
        } else
            return null
    }
}