import store from '@/store'

const menuRoutes = (project = false) => {
    const addToMobileMenu = [
        {
            name: 'about',
            menuName: project ? 'project' : 'group',
            icon: "retweet"
        }
    ]
    let taskChild = [
        {
            name: 'tasks',
            menuName: "table"
        },
        {
            name: 'kanban',
            menuName: "kanban"
        }
    ]
    if(project) {
        taskChild = taskChild.concat({
            name: 'gantt',
            menuName: "gantt"
        })
    }

    let taskRoute = {
        name: 'tasks_sub',
        menuName: "task",
        mainPage: 'tasks',
        icon: "profile",
        child: taskChild
    }

    if(store.state.isMobile) {
        taskRoute = {
            name: 'tasks',
            menuName: "task"
        }
    }

    let routes = [
        {
            name: 'news',
            menuName: "news",
            icon: 'read'
        },
        {
            ...taskRoute
        },
        {
            name: 'calendar',
            menuName: "calendar",
            icon: "profile"
        },
        {
            name: 'sprint',
            menuName: "sprints",
            icon: "retweet"
        },
        {
            name: 'analytics',
            menuName: "analytics",
            icon: "profile"
        },
        {
            name: 'files',
            menuName: "files",
            icon: "files"
        }
    ]

    if(store.state.isMobile)
        routes.unshift(...addToMobileMenu)

    return routes
}

export default menuRoutes