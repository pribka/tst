<template>
    <div ref="wrapRef" class="h-full flex flex-col">
        <UniversalTable
            :model="initPageModel"
            class="flex-grow"
            :pageName="initPageName"
            tableType="pulse_employees"
            :openHandler="openHandler"
            :params="tableParams"
            :colParams="{
                getPopupContainer: getPopupContainer
            }"
            :endpoint="endpoint" />
    </div>
</template>

<script>
import { dateFormat } from '../../utils.js'

export default {
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    },
    props: {
        initPageName: {
            type: String,
            default: ""
        },
        initPageModel: {
            type: String,
            default: ""
        },
        openUserModal: {
            type: Function,
            default: () => {}
        },
        dateRange: {
            type: Array,
            default: () => []
        }
    },
    computed: {
        tableParams() {
            const start = this.dateRange?.[0]
            const end = this.dateRange?.[1]
            if (!start || !end) return {}
            return {
                start: dateFormat(start),
                end: dateFormat(end)
            }
        }
    },
    data() {
        return {
            endpoint: '/day_summary/note/list_latest/'
        }
    },
    methods: {
        openHandler(record) {
            this.openUserModal(record)
        },
        getPopupContainer() {
            return this.$refs.wrapRef
        }
    }
}
</script>
