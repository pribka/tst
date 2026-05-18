<template>
    <a-button-group>
        <a-button 
            type="primary" 
            icon="fi-rr-plus-small" 
            flaticon
            @click="addTaskDrawer()">
            {{ addButton && addButton.label ? addButton.label : $t('task.add_task') }}
        </a-button>
        <a-dropdown 
            v-if="toExcel" 
            placement="bottomRight"
            :trigger="['click']">
            <a-button 
                type="primary"
                icon="fi-rr-menu-dots-vertical"
                flaticon />
            <a-menu slot="overlay">
                <a-menu-item key="0" @click="getFile()">
                    {{ $t('task.excel_download') }}
                </a-menu-item>
            </a-menu>
        </a-dropdown>
    </a-button-group>
</template>

<script>
const updateKey = 'file_loading' 
import eventBus from '@/utils/eventBus'
export default {
    props: {
        buttonType: {
            type: String,
            default: 'default'
        },
        extendDrawer: {
            type: Boolean,
            default: false
        },
        windowWidth: {
            type: Number,
            required: true
        },
        formParams: {
            type: Object,
            default: () => {}
        },
        showFastTaskAction: {
            type: Boolean,
            default: true
        },
        addButton: {
            type: Object,
            default: () => null
        },
        toExcel: {
            type: Boolean,
            default: false
        },
        page_name: {
            type: String,
            default: ''
        },
        queryParams: {
            type: Object,
            default: () => null
        },
        requestData: {
            type: Object,
            default: () => null
        },
        orderQuery: {
            type: Object,
            default: () => null
        }
    },
    data() {
        return {
            defoultURL: '/tasks/analytics/file/'
        }
    },
    computed: {
        taskType() {
            return this.addButton?.task_type || 'task'
        }
    },
    methods: {
        getEndpointURL() {
            const urlList = {
                'page_list_task_task.TaskModel': '/tasks/task_list/file/',
                'page_list_interest_task.TaskModel': '/tasks/interest_list/file/',
            }
            return urlList[this.page_name] || this.defoultURL
            if(this.page_name === 'page_list_task_task.TaskModel')
                return '/tasks/task_list/file/'

            return this.defoultURL
        },
        async getFile() {
            try {
                this.$message.loading({ content: this.$t('task.loading'), key: updateKey })
                let params = {
                    page_name: this.page_name,
                    task_type: this.taskType
                }

                if(this.queryParams) {
                    params = {
                        ...params,
                        ...this.queryParams
                    }
                }
                if(this.orderQuery)
                    params['ordering'] = this.orderQuery

                const endpointURL = this.getEndpointURL()
                const { data } = await this.$http(endpointURL, {
                    responseType: 'blob',
                    params
                })
                if(data) {
                    const url = window.URL.createObjectURL(new Blob([data]))
                    const link = document.createElement('a')
                    link.href = url
                    link.setAttribute('download', `${this.requestData?.name ? `${this.requestData.name}` : ''} ${this.$t('task.statistics_from')} ${this.$moment().format('DD-MM-YYYY HH:mm')}.xlsx`)
                    document.body.appendChild(link)
                    link.click()
                    link.remove()
                    this.$message.success({ content: this.$t('task.file_is_generated'), key: updateKey, duration: 0.5 })
                }
            } catch(e) {
                console.log(e)
                this.$message.error({ content: this.$t('task.loading_error'), key: updateKey, duration: 2 })
            }
        },
        addTaskDrawer() {
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: this.page_name
            })
            eventBus.$emit('add_task_modal', {
                ...this.formParams,
                task_type: this.taskType
            })
            /*
            if(this.extendDrawer)
                this.$store.commit('task/SET_TASK_DRAWER_ZINDEX', 1010)
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: this.page_name
            })
            this.$store.dispatch('task/sidebarOpen', {
                ...this.formParams,
                task_type: this.taskType
            })*/
        },
        addTask() {
            this.$store.dispatch('task/editDrawer', true)
        }
    }
}
</script>