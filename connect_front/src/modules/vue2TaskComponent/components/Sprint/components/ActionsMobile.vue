<template>
    <div>
        <a-button 
            size="default"
            class="open_button w-full"
            type="button"
            :loading="loading" 
            @click="openDrawer">
            <i class="fi fi-rr-menu-burger"></i>
        </a-button>
        <ActivityDrawer v-model="visible">
            <ActivityItem
                v-if="(record.status === 'new' && isAuthor)"
                @click="start()">
                <i class="fi fi-rr-caret-circle-right mr-2"></i> {{ $t('task.start_sprint') }}
            </ActivityItem>
            <ActivityItem
                v-if="(record.status === 'in_process') && isAuthor"
                @click="end()">
                <i class="fi fi-rr-comment-check mr-2"></i> {{ $t('task.complete_sprint') }}
            </ActivityItem>
            <ActivityItem 
                @click="share()">
                <i class="fi fi-rr-share mr-2"></i> {{$t('task.share_to_chat')}}
            </ActivityItem>
            <ActivityItem 
                v-if="isAuthor"
                @click="edit()">
                <i class="fi fi-rr-edit mr-2"></i> {{$t('task.edit')}}
            </ActivityItem>
            <ActivityItem 
                v-if="isAuthor"
                @click="deleteSprint()">
                <span class="text-red-500">
                    <i class="fi fi-rr-trash mr-2"></i> {{$t('task.remove')}}
                </span>
            </ActivityItem>
        </ActivityDrawer>
    </div>
</template>

<script>
import { ActivityItem, ActivityDrawer } from '@/components/ActivitySelect'

export default {
    props: {
    
        record: {
            type: Object,
            required: true
        },
      
    },
    data() {
        return{
            loading: false,
            visible: false
        }
    },
    computed: {
        isAuthor() {
            if(this.$store.state.user.user?.id === this.record.author.id)
                return true
            else
                return false
        },
    },
    components: {
        ActivityDrawer,
        ActivityItem
    },
    methods: {
        share() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'tasks.TaskModel',
                // shareId: this.item.id,
                // object: this.item,
                // shareUrl: `${window.location.href}?task=${this.item.id}`,
                // shareTitle: `Задача - ${this.item.name}`
            })
        },
        async deleteSprint() {
            try {
                await this.$http.post(`table_actions/update_is_active/`, [
                    {id: this.record.id, is_active: false}
                ] 
                )
                this.$emit('delete', this.record.id)
            } catch(e) {
                this.$message.error(this.$t('error') + e)
            } finally {
                this.loading = false
            }
        },
        
        async start() {
            try {
                await this.$http.put(`tasks/sprint/${this.record.id}/update_status/`, {status: 'in_process'})
                this.$emit('updateStatus', {status: 'in_process', id: this.record.id})
                this.$message.success(this.$t('task.sprint_started'))
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('error'))
            } finally {
                this.loading = false
            }
        },
        async end() {
            try {
                await this.$http.put(`tasks/sprint/${this.record.id}/update_status/`, {status: 'completed'})
                this.$emit('updateStatus', {status: 'completed', id: this.record.id})
                this.$message.success(this.$t('task.sprint_completed'))
            } catch(e) {
                this.$message.error(this.$t('error'))
            } finally {
                this.loading = false
            }
        },
        async edit() {
            this.$emit('edit', this.record)
        },
        openDrawer() {
            this.visible = true
        }
       
    }
}
</script>

<style lang="scss" scoped>
.open_button {
    display: flex;
    justify-content: center;
    align-items: center;

    line-height: 100%;
}
</style>