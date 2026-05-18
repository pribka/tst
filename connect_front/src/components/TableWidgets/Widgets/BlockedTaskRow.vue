
<template>
    <div>
        <span 
            class="text-on-danger"
            v-for="task, index in tasks"
            :key="task.id">
            <a-popover placement="bottom" trigger="hover" destroyTooltipOnHide>
                <template slot="content">
                    <div class="-m-1">
                        <div
                            v-for="blocker in task.blockers"
                            :key="blocker.id"
                            class="m-1">
                            <a-tag 
                                size="small"
                                contrastText
                                :color="blocker.color">
                                {{ blocker.name }}
                            </a-tag>
                        </div>
                    </div>
                </template>
                <span class="cursor-pointer" @click.stop.prevent="openTask(task.id)">
                    {{ task.counter }}
                    <i class="fi fi-rr-info"></i>
                </span>
            </a-popover>
            <span v-if="index !== tasks.length - 1">, </span>
        </span>
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
        tasks() {
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