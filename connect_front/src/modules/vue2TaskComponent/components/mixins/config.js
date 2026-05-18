export default {
    props: {
        pageConfig: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        getRouteInfo() {
            return this.$store.getters['navigation/getRouteInfo'](this.$route.name)
        },
        addButton() {
            if(this.extendDrawer) {
                return {
                    task_type: this.taskType,
                    label: this.$t('task.add_task')
                }
            } else {
                if(this.getRouteInfo?.pageActions?.add) {
                    return {
                        task_type: this.getRouteInfo?.task_type || 'task',
                        label: this.getRouteInfo?.buttonConfig?.label || this.$t('task.add_task')
                    }
                } else
                    return null
            }
            
        },
        filterConfig() {
            return this.pageConfig?.showFilter ? true : false
        }
    }
}