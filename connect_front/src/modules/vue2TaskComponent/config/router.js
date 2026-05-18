export default function taskRouters({ meta = null, state = null }) {
    const routes = [
        {
            name: 'task-list-page',
            path: 'list',
            component: () => import(`../views/Table/Page.vue`),
            meta: {
                ...meta,
                navWidget: "NavPage",
                title: "Задачи",
                icon: 'unordered-list'
            }
        },
        /*{
            name: 'task-calendar-page',
            path: 'calendar',
            component: () => import(`../views/TaskCalendar/index.vue`),
            meta: {
                ...meta,
                navWidget: "NavPage",
                title: "Календарь задач",
                icon: 'calendar'
            }
        },*/
        {
            name: 'task-kanban-page',
            path: 'kanban',
            component: () => import(`../views/Kanban/index.vue`),
            meta: {
                ...meta,
                navWidget: "NavPage",
                title: "Канбан",
                icon: 'database'
            }
        },
        /*{
            name: 'task-gantt-page',
            path: 'gantt',
            component: () => import(`../views/Gantt/index.vue`),
            meta: {
                ...meta,
                navWidget: "NavPage",
                title: "Диаграмма Ганта",
                icon: 'line-chart'
            }
        },*/
        // {
        //     name: 'task-sprint-page',
        //     path: 'sprint',
        //     component: () => import(`../components/Sprint/List.vue`),
        //     meta: {
        //         ...meta,
        //         navWidget: "NavPage",
        //         title: "Спринты",
        //         icon: 'retweet'
        //     }
        // }
    ]
    /*if(state?.config.config?.task_modules) {
        const task_modules = state.config.config.task_modules
        if(!task_modules.gantt)
            routes.splice(routes.findIndex(route => route.name === 'task-gantt-page'), 1)
    }*/
    
    return routes
}