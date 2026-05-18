<template>
    <a-button 
        type="ui" 
        size="large"
        ghost
        :loading="loading"
        @click="getFile()">
        {{ $t('task.excel_download') }}
    </a-button>
</template>

<script>
export default {
    props: {
        page_name: {
            type: [String, Number],
            default: 'analytics_table'
        },
        task_type: {
            type: String,
            default: 'task'
        },
        queryParams: {
            type: Object,
            default: () => null
        },
        orderQuery: {
            type: [String, Number],
            default: () => null
        },
        requestData: {
            type: Object,
            default: () => {}
        }
    },
    data() {
        return {
            loading: false,
            defoultURL: '/tasks/analytics/file/'
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
                this.loading = true
                let params = {
                    page_name: this.page_name,
                    task_type: this.task_type
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
                }
            } catch(e) {
                console.log(e)
                this.$message.error(this.$t('task.error'))
            } finally {
                this.loading = false
            }
        }
    }
}
</script>