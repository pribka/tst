
<template>
    <div class="flex justify-center">
        <template v-if="record.excluded">
            <i 
                v-tippy="{ inertia : true, duration : '[600,300]'}"
                :content="$t('task.removed_from_sprint')"
                class="fi fi-rr-cross"></i>
        </template>
        <template v-else>
            <a-spin v-if="loading" size="small" />
            <div 
                v-else
                v-tippy="{ inertia : true, duration : '[600,300]'}"
                :content="$t('task.result_approving')">
                <a-checkbox v-model="proxyValue" />
            </div>
        </template>
    </div>
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
            loading: false
        }
    },
    computed: {
        proxyValue: {
            get() {
                return this.tableRow?.approved
            },
            set(value) {
                this.tableData[this.tableRowIndex].approved = value
                this.save()
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
            this.loading = true
            this.$http.patch(url, {
                approved: this.proxyValue
            })
                .then(({ data }) => {
                    
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error('Не удалось совершить изменения')
                })
                .finally(() => {
                    this.loading = false
                })
        },
    }
}
</script>