import { mapGetters, mapState } from "vuex"
export default {
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        ...mapGetters({
            getTabFormAccess: 'task/getTabFormAccess'
        }),
        formAccess() {
            return this.getTabFormAccess(this.task.id, this.code)
        },
        checkAccess() {
            if(this.formAccess) {
                if(this.formAccess.operator && this.user?.id === this.task?.operator?.id) {
                    return true
                }
                if(this.formAccess.owner && this.user?.id === this.task?.owner?.id) {
                    return true
                }
                if(this.formAccess.visors && this.user && this.task.visors?.length) {
                    const find = this.task.visors.find(f => f.id === this.user.id)
                    return find ? true : false
                }

                return false
            } else
                return false
        }
    }
}