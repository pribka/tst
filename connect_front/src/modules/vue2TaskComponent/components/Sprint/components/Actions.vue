<template>
    <div>
        <a-dropdown :trigger="['click']">
            <a-button :loading="loading" icon="menu" type="link" />
            <a-menu slot="overlay">
               
                <a-menu-item 
                    v-if="(record.status === 'new') && isAuthor" 
                    key="start" 
                    class="flex items-center" 
                    @click="start()">
                    <i class="fi fi-rr-caret-circle-right mr-2"></i> {{ $t('task.start_sprint') }}
                </a-menu-item>
                <a-menu-item 
                    v-if="(record.status=== 'in_process') && isAuthor" 
                    class="flex items-center" 
                    key="end" 
                    @click="end()">
                    <i class="fi fi-rr-comment-check mr-2"></i> {{ $t('task.complete_sprint') }}
                </a-menu-item>
                <a-menu-item 
                    key="share" 
                    class="flex items-center"
                    @click="share()">
                    <i class="fi fi-rr-share mr-2"></i> {{$t('task.share_to_chat')}}
                </a-menu-item>
                <a-menu-item 
                    v-if="isAuthor" 
                    key="edit" 
                    class="flex items-center" 
                    @click="edit()">
                    <i class="fi fi-rr-edit mr-2"></i> {{$t('task.edit')}}
                </a-menu-item>
               
                <a-menu-divider />

                <a-menu-item 
                    v-if="isAuthor"
                    class="text-red-500 flex items-center" 
                    key="delete" 
                    @click="deleteSprint()">
                    <i class="fi fi-rr-trash mr-2"></i> {{$t('task.remove')}}
                </a-menu-item>
            </a-menu>
        </a-dropdown>
    </div>
</template>

<script>

export default {
    props: {
    
        record: {
            type: Object,
            required: true
        },
      
    },
    data() {
        return{
            loading: false
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
    methods: {
        share() {
            this.$store.commit('share/SET_SHARE_PARAMS', { 
                model: 'tasks.TaskModel',
                shareId: this.record.id,
                object: this.record,
                shareUrl: `${window.location.origin}/ru/dashboard?sprint=${this.record.id}`,
                shareTitle: `${this.$t('task.sprint_menu')} - ${this.record.name}`
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
       
    }
}
</script>
