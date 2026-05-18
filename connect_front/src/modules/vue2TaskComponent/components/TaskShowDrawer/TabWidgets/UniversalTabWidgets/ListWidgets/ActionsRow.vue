<template>
    <div
        v-if="checkAccess"
        :ref="`actions_${row.id}`"
        :class="isMobile && 'mt-2'">
        <a-dropdown :getPopupContainer="getPopupContainer">
            <a-button 
                :type="actionsButtonType || actionsButton.type" 
                :size="actionsButton.size"
                :block="actionsAsBlock"
                class="ant-btn-icon-only"
                
                :loading="loading">
                <i 
                    class="fi" 
                    :class="actionsButton.icon" />
            </a-button>
            <a-menu 
                v-if="actionsButton" 
                slot="overlay">
                <a-menu-item 
                    v-if="actionsButton.edit" 
                    key="1"
                    class="flex items-center"
                    @click="editHandler()">
                    <i 
                        class="fi mr-2" 
                        :class="actionsButton.edit.icon" />
                    {{ actionsButton.edit.title }}
                </a-menu-item>
                <template v-if="actionsButton.delete" >
                    <a-menu-divider />
                    <a-menu-item 
                        key="2" 
                        class="flex items-center text-red-500"
                        @click="deleteHandler()">
                        <i 
                            class="fi mr-2" 
                            :class="actionsButton.delete.icon" />
                        {{ actionsButton.delete.title }}
                    </a-menu-item>
                </template>
            </a-menu>
        </a-dropdown>
    </div>
</template>

<script>
import widgetMixins from './widgetMixins.js'
import eventBus from '@/utils/eventBus'
export default {
    mixins: [
        widgetMixins
    ],
    computed: {
        user() {
            return this.$store.state.user.user
        },
        formAccess() {
            return this.$store.getters['task/getTabFormAccess'](this.task.id, this.code)
        },
        actionsButton() {
            if(this.column?.actionsButton)
                return this.column.actionsButton
            else
                return null
        },
        checkAccess() {
            if(this.user?.id === this.row?.author?.id)
                return true
            if(this.formAccess?.operator && this.user?.id === this.task?.operator?.id)
                return true
            if(this.formAccess?.owner && this.user?.id === this.task?.owner?.id)
                return true
            if(this.formAccess?.visors && this.user && this.task?.visors?.length) {
                const find = this.task.visors.find(f => f.id === this.user.id)
                return find ? true : false
            }
            return false
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            loading: false
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs[`actions_${this.row.id}`]
        },
        editHandler() {
            let item = JSON.parse(JSON.stringify(this.row))

            for (let prop in item) {
                const find = this.allColumns.find(f => f.key === prop)
                if(find?.scopedSlots?.customRender === 'RelatedRow') {
                    item[prop] = item[prop]?.id || null
                }
            }

            eventBus.$emit(`update_universal_${this.code}`, item)
        },
        deleteHandler() {
            this.$confirm({
                title: this.$t('task.delete_message'),
                okText: this.$t('task.remove'),
                okType: 'danger',
                zIndex: 5000,
                cancelText: this.$t('task.handler.cancel'),
                maskClosable: true,
                onOk: () => {
                    return new Promise(async (resolve, reject) => {
                        try {
                            this.loading = true
                            await this.$store.dispatch('task/deleteTabData', {
                                id: this.row.id,
                                code: this.code,
                                task: this.task
                            })
                            resolve()
                        } catch(e) {
                            console.log(e)
                            reject(e)
                        } finally {
                            this.loading = false
                        }
                    })
                },
                onCancel() {}
            })
        }
    }
}
</script>
