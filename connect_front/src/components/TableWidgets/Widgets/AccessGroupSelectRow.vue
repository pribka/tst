<template>
    <div v-if="record.is_touched">
        <div class="flex flex-wrap -m-0.5">
            <a-tag 
                v-for="accessGroup in record.access_groups" 
                :key="accessGroup.id"
                :title="accessGroup.name"
                class="max-w-[180px] truncate m-0.5">
                {{ accessGroup.name }}
            </a-tag>
        </div>
    </div>
    <DSelect
        v-else
        v-model="accessGroups"
        size="large"
        :apiUrl="apiUrl"
        class="w-full"
        infinity
        multiple
        :maxTagCount="1"
        :initList="false"
        usePopupContainer
        :getPContainer="getPopupContainer"
        :listObject="false"
        labelKey="name"
        @change="changeHandler"
        :placeholder="$t('sports.selectFromList')"
        :default-active-first-option="false"
        :filter-option="false"
        :not-found-content="null" />
</template>


<script>
export default {
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue')
    },
    props: {
        record: {
            type: Object,
            required: true,
        },
        pageName: {
            type: String,
            default: ''
        },
        model: {
            type: String,
            default: ''
        }
    },

    data() {
        return {
            accessGroups: []
        }
    },
    computed: {
        computedStoreKey() {
            if (this.storeKey) return this.storeKey
            return this.model+this.pageName
        },

        tableData() {
            return this.$store.state.table.tableRows?.[this.computedStoreKey]
        },
        apiUrl() {
            return `/contractor_permissions/access_groups/?contractor=${this.record.organization.id}`
        }
        
    },
    methods: {
        getPopupContainer() {
            return document.body
        },
        changeHandler(value) {
            const index = this.tableData?.findIndex(item => item.id === this.record.id)
            if (index >= 0) {
                this.tableData[index].access_groups = value || null
            }
        },
    }
}
</script>