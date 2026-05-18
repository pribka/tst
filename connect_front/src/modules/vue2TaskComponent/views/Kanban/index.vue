<template>
    <Kanban 
        main
        :taskType="taskType"        
        :showPageTitle="showPageTitle"
        :pageConfig="pageConfig">
        <slot />
    </Kanban>
</template>

<script>
import viewProps from '../../mixins/viewProps.js'
import '../../assets/main.scss'
export default {
    mixins: [viewProps],
    components: {
        Kanban: () => import('../../components/Kanban/KanbanPageSwitch.vue')
    },
    props: {
        showPageTitle: {
            type: Boolean,
            default: false
        }
    }
}
</script>