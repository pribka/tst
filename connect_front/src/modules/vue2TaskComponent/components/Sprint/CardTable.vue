<template>
    <a-table
        :columns="columns"
        :data-source="dataSource"  
        :loading="loading"
        :pagination="pagination"
        :scroll="scroll"
        :size="tableSize"
        :locale="{
            emptyText: $t('task.no_data')
        }"
        :row-key="record => record.id">
        <template slot="name"  slot-scope="text, record">
            <span @click="openSprint(record.id)" class="item_name blue_color">{{text}}</span>
        </template>
        <template slot="target"  slot-scope="text">
            <span class="item_name">{{text}}</span>
        </template>
        <template slot="created_at"  slot-scope="text">
            <DateWidget :date="text" noColor/> 
        </template>
        <template slot="finished_date"  slot-scope="text">
            <DateWidget :date="text" /> 
        </template>
        <template slot="expected_result"  slot-scope="text">
            <span class="item_name">{{text.join()}}</span>
        </template>
        <template slot="task_count"  slot-scope="text, record">
            <TasksCount  :record="record" />
        </template>
        <template slot="status" slot-scope="text, record">
            <SprintStatus :sprint="record" />
        </template>
        <template slot="actions" slot-scope="text, record">
            <Actions 
                :record="record" 
                @edit="startEdit" 
                @delete="deleteSprint(record.id)" 
                @updateStatus="updateStatus"/>
        </template>
    </a-table>
</template>

<script>
import TasksCount from './components/TasksCount.vue'
import SprintStatus from './components/SprintStatus.vue'
import DateWidget from './components/DateWidget.vue'
import Actions from './components/Actions.vue'
import { mapState } from 'vuex'
export default {
    props: {
        columns: {
            type: Array,
            required: true
        },
        dataSource: {
            type: Array,
            required: true
        },
        loading: {
            type: Boolean,
            required: true
        },
        pagination: {
            type: Boolean,
            required: true
        },
        scroll: {
            type: Object,
            required: true
        },
        openSprint: {
            type: Function,
            default: () => {}
        },
        startEdit: {
            type: Function,
            default: () => {}
        },
        deleteSprint: {
            type: Function,
            default: () => {}
        },
        updateStatus: {
            type: Function,
            default: () => {}
        }
    },
    components: {
        DateWidget,
        Actions,
        TasksCount, 
        SprintStatus, 
    },
    computed: {
        ...mapState({
            config: state => state.config.config
        }),
        tableSize() {
            return this.config?.theme?.tableSize ? this.config.theme.tableSize : 'small'
        }
    }
}
</script>

<style lang="scss" scoped>
</style>