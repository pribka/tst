
<template>
    <div class="-m-0.5">
        <a-tag 
            v-for="blocker in blockers"
            :key="blocker.id"
            class="m-0.5"
            contrastText
            :color="blocker.color">
            {{ blocker.name }}
        </a-tag>
    </div>
</template>


<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        text: {
            type: Array,
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
        blockers() {
            return this.text
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
        openTask(id) {
            eventBus.$emit('OPEN_TASK_DRAWER', id)
        }
    }
}
</script>

<style scoped>
.text-on-danger {
    color: #FF5C5C;
}
</style>