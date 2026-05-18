function switchStoreFolder(route) {
    switch (route.name) {
    case 'dashboard':
        return 'Dashboard'
        break;
    case 'meetings':
        return 'vue2MeetingComponent'
        break;
    case 'calendar':
        return 'Calendar'
        break;
    case 'chat':
        return 'vue2ChatComponent'
        break;
    case 'tasks':
        return 'vue2TaskComponent'
        break;
    case 'team':
        return 'Team'
        break;
    case 'my-bases':
        return 'MyBases'
        break;
    case 'groups':
        return 'vue2GroupsAndProjectsComponent'
        break;
    case 'files':
        return 'vue2Files'
        break;
    case 'contractors':
        return 'Contractors'
        break;
    case 'logistic-monitor':
        return 'LogisticMonitor'
        break;
    case 'goods':
        return 'Products'
        break;
    case 'orders':
        return 'Orders'
        break;
    case 'geoviewer':
        return 'GeoViewer'
        break;
    default:
        return null
    }
}

function switchStoreName(route) {
    switch (route.name) {
    case 'dashboard':
        return 'dashboard'
        break;
    case 'meetings':
        return 'meeting'
        break;
    case 'calendar':
        return 'calendar'
        break;
    case 'chat':
        return 'chat'
        break;
    case 'tasks':
        return 'task'
        break;
    case 'team':
        return 'organization'
        break;
    case 'my-bases':
        return 'mybases'
        break;
    case 'groups':
        return 'workgroups'
        break;
    case 'files':
        return 'files'
        break;
    case 'contractors':
        return 'contractors'
        break;
    case 'logistic-monitor':
        return 'monitor'
        break;
    case 'goods':
        return 'products'
        break;
    case 'orders':
        return 'orders'
        break;
    case 'geoviewer':
        return 'geoviewer'
        break;
    default:
        return null
    }
}

async function asyncRouteInit(route) {
    return import(`@apps/${switchStoreFolder(route)}/store/index.js`)
        .then(module => {
            return module.default
        })
        .catch(e => {
            return null
        })
}

const initModules = async store => {
    const appRoute = [...store.state.navigation.routerApp].filter(f => !f.isHidden) || []
    if(appRoute.length) {
        for (const i in appRoute) {
            const storeModel = await asyncRouteInit(appRoute[i])
            if(storeModel && !store.hasModule(switchStoreName(appRoute[i]))) {
                await store.registerModule(switchStoreName(appRoute[i]), storeModel)
            }
        }
    }
}

export default initModules