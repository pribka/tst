<template>
    <div>
        <a-dropdown :trigger="['click']">
            <a-button :loading="loading" icon="menu" type="link" />
            <a-menu slot="overlay">
                <template v-if="statusFilter.length && item.status !== 'completed'">
                    <a-menu-item
                        @click="changeStatus(item.name)"
                        v-for="item in statusFilter"
                        :key="item.name">
                        {{$t(`task.${item.name2}`)}}
                    </a-menu-item>
                    <a-menu-divider />
                </template>
                <template v-if="myTask && item.status === 'completed'">
                    <a-menu-item @click="changeStatus('new')">
                        {{$t('task.resume')}}
                    </a-menu-item>
                    <a-menu-divider />
                </template>
                <a-menu-item v-if="item.level < 3" key="add" @click="addSubtask()">
                    {{$t('task.add_subtask')}}
                </a-menu-item>
                <a-menu-item key="share" @click="share()">
                    {{$t('task.share_to_chat')}}
                </a-menu-item>
                <a-menu-item key="edit" v-if="myTask" @click="edit()">
                    {{$t('task.edit')}}
                </a-menu-item>
                <a-menu-item key="copy" @click="copy()">
                    {{$t('task.copy')}}
                </a-menu-item>
                <a-menu-item 
                    class="text-red-500" 
                    v-if="isAuthor && !item.children_count" 
                    key="delete" 
                    @click="deleteTask()">
                    {{$t('task.remove')}}
                </a-menu-item>
            </a-menu>
        </a-dropdown>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        extendDrawer: {
            type: Boolean,
            default: false
        },
        user: {
            type: Object,
            required: true
        },
        item: {
            type: Object,
            required: true
        },
        statusList: {
            type: Array,
            required: true
        }
    },
    data() {
        return{
            loading: false
        }
    },
    computed: {
        isAuthor() {
            if(this.user?.id === this.item.owner.id)
                return true
            else
                return false
        },
        myTask() {
            if(this.user?.id === this.item.owner.id || this.user?.id === this.item.operator.id || this.item.workgroup?.author === this.user?.id || this.item.project?.author === this.user?.id)
                return true
            else
                return false
        },
        statusFilter() {
            let status = this.statusList
            if(this.user?.id === this.item.operator.id && this.user.id !== this.item.owner.id) {
                return status.filter(e => e.name !== this.item.status).filter(e => e.rule === 'operator')
            }
            if(this.user?.id === this.item.owner.id || this.item.workgroup?.author === this.user?.id || this.item.project?.author === this.user?.id) {
                return status.filter(e => e.name !== this.item.status)
            }
            return []
        }
    },
    methods: {
        share() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'tasks.TaskModel',
                shareId: this.item.id,
                object: this.item,
                shareUrl: `${window.location.origin}/ru/dashboard?task=${this.item.id}`,
                shareTitle: `Task - ${this.item.name}`
            })
        },
        async deleteTask() {
            try {
                this.loading = true
                const res = await this.$store.dispatch('task/deleteTask', this.item)

                if(res)
                    this.$message.success(this.$t('task.task_deleted'))
            } catch(e) {
                this.$message.error(this.$t('error') + e)
            } finally {
                this.loading = false
            }
        },
        async edit() {
            try {
                this.loading = true
                const res = await this.$store.dispatch('task/getFullTask', this.item.id)
                if(res)
                    eventBus.$emit('EDIT_TASK', false)
            } catch(e) {
                this.$message.error(this.$t('error'))
            } finally {
                this.loading = false
            }
        },
        async changeStatus(status) {
            try {
                this.loading = true
                await this.$store.dispatch('task/changeStatus', {task: this.item, status})
            } catch(e) {
                this.$message.error(this.$t('error'))
            } finally {
                this.loading = false
            }
        },
        addSubtask() {
            eventBus.$emit('ADD_WATCH', {key: 'parent', data: this.item})
        },
        copy() {
            eventBus.$emit('ADD_WATCH', {type: 'copy', data: this.item})
        }
    }
}
</script>
