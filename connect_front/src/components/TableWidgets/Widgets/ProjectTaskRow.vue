<template>
    <div v-if="isNewTask">
        
        <a-form-model
            :model="storeRecord">
            <template v-if="column.key === 'description'">
                <a-form-model-item>
                    <a-input 
                        :placeholder="$t('task.task_desc')" 
                        v-model="storeRecord.description" />
                        <!-- @change="setValue($event.target.value, 'description')" -->
                </a-form-model-item>
            </template>
            <template v-else-if="column.key === 'duration' && record.task_type === 'task'">
                <a-form-model-item 
                    prop="duration" 
                    :rules="[{ required: true, message: $t('field_required') }]">
                    <a-input-number 
                        :min="1"
                        class="w-full"
                        :placeholder="$t('task.task_duration')" 
                        v-model="storeRecord.duration" />
                        <!-- @change="setValue($event, 'duration')"  -->
                </a-form-model-item>
            </template>
        </a-form-model>
    </div>
    <div v-else>
        {{ text }}
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        text: {
            type: [Object, String, Number],
            default: ''
        },
        column: {
            type: Object,
            required: true
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
    computed: {
        isNewTask() {
            return this.record.new
        },
        computedStoreKey() {
            if (this.storeKey) return this.storeKey
            return this.model+this.pageName
        },

        storeRecord() {
            const tableRows = this.$store.state.table.tableRows[this.computedStoreKey]
            const record = tableRows.find(row => this.record.id === row.id)
            return record
        }
    },
    data() {
        return{
            loading: false,
            actionLoading: false
        }
    },
    methods: {
        setValue(value, field) {
            if (this.storeRecord) {
                this.storeRecord[field] = value
            }
        }
    },
    
}
</script>