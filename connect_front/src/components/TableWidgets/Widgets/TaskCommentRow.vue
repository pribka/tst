
<template>
    <!-- <div v-if="record.is_touched">
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
        :not-found-content="null" /> -->
    <a-input 
        inputType="ghost"
        v-model="proxyValue"
        :placeholder="$t('task.add_comment')"
        @blur="save"
        @keyup.enter="save" />
</template>


<script>
export default {
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
        proxyValue: {
            get() {
                return this.tableRow?.comment
            },
            set(value) {
                this.tableData[this.tableRowIndex].comment = value
            }
        },
        computedStoreKey() {
            if (this.storeKey) return this.storeKey
            return this.model+this.pageName
        },

        tableData() {
            return this.$store.state.table.tableRows?.[this.computedStoreKey]
        },
        tableRowIndex() {
            return this.tableData?.findIndex(item => item.id === this.record.id)
        },
        tableRow() {
            
            if (this.tableRowIndex >= 0) {
                return this.tableData[this.tableRowIndex]
            }
            return ''
        },
        
    },
    methods: {
        save() {
            const url = `/tasks/sprint/expected_results/${this.record.id}/update/`
            this.$http.patch(url, {
                comment: this.proxyValue
            })
                .then(({ data }) => {
                    
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error('Не удалось совершить изменения')
                })
        },
    }
}
</script>