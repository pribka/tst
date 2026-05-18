<template>
    <div>
        <a-dropdown 
            :trigger="dropTrigger"
            :destroyPopupOnHide="true">
            <span class="cursor-pointer select-none">
                {{ $t('Status') }}: 
                <a-tag :color="currentStatus?.color" class="p-0 bg-transparent border-0 text-sm underline">
                    {{ currentStatus?.name }}
                </a-tag>
            </span>
            <a-menu slot="overlay">
                <a-menu-item 
                    v-for="status in cStatusFiltered"
                    :key="status.code"
                    class="flex items-center"
                    @click="changeStatus(status)">
                    <a-badge 
                        v-if="status.color !== 'default'" 
                        :color="status.color" />
                    {{ status.btn_title ? status.btn_title : status.name }}
                </a-menu-item>
            </a-menu>
        </a-dropdown>
    </div>
</template>

<script>
import { mapState } from 'vuex'
import mixins from './mixins.js'
import { errorHandler } from '@/utils/index.js'
export default {
    mixins: [
        mixins
    ],
    props: {
        isFull: {
            type: Boolean,
            default: false
        },
        item: {
            type: Object,
            required: true
        },
        cooperator: {
            type: Object,
            required: true
        },
        model: {
            type: String,
            default: 'tasks.TaskModel'
        },
        dropTrigger: {
            type: Array,
            default: () => ['click']
        },
        getPopupContainer: {
            type: Function,
            default: () => document.body
        },
        showStatus: {
            type: Boolean,
            default: true
        },
        pageName: {
            type: String,
            default: ''
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            statusList: state => state.task.statusList,
            statusLoader: state => state.task.statusLoader
        }),
        isAuthor() {
            if (!this.user?.id) { return false }
            return [
                this.item.owner.id,
                this.item.workgroup?.author,
                this.item.sprint?.author,
                this.item.project?.author,
            ].includes(this.user.id)
        },
        filteredList() {
            if(this.statusList?.[this.item.task_type]?.length)
                return this.statusList[this.item.task_type]
            return []
        },
        currentStatus() {
            return this.filteredList.find(item => item.code === this.cooperator.status.code)
        },

        cStatusFiltered() {
            const changeCooperatorStatuses = this.dropActions?.change_cooperator_status?.available_statuses
            if (changeCooperatorStatuses?.length) {
                return changeCooperatorStatuses
            }
            return []
        },
        isOperator() {
            return this.user?.id === this.item.operator?.id
        },
        isLogistic() {
            return this.item?.task_type === 'logistic'
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return{
            loading: false,
        }
    },
    methods: {
        async changeStatus(status) {
            this.loading = true
            const payload = {
                id: this.cooperator.id,
                status: status.code
            }
            const url = `tasks/task/${this.item.id}/cooperator_status/`
            this.$http.put(url, payload) 
                .then(({ data }) => {
                    if (this.$store.hasModule('workplan')) {
                        this.$store.dispatch('workplan/updateItem', {
                            item: this.item,
                            list: 'taskList'
                        })
                    }
                    const cooperator = this.$store.state.task.task.cooperators.find(cooperator => cooperator.id === data.id)
                    cooperator.status.code = data.status
                })
                .catch(error => {
                    errorHandler({error})
                })
        },
    },
}
</script>