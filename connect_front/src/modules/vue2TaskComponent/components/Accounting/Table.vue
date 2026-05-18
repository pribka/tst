<template>
    <div class="table_wrapper flex-grow">
        <UniversalTable 
            :model="pageModel"
            :pageName="pageName"
            class="min-h-0"
            autoHeight
            :excludeCol="excludeCol"
            :colParams="{
                getPopupContainer: getPopupContainer,
                actions: actions,
                editHandler: editTime,
                deleteHandler: deleteHandler,
                listType: 'taskList',
                workObj: task
            }"
            :scrollWrapper="tableFullHeight ? {} : {x: 1300, y: minHeight}"
            :params="{
                task: task.id
            }"
            tableType="tasks_time_tracking"
            endpoint="/tasks/time_tracking/" />
    </div>
</template>

<script>
import initProps from './props.js'
export default {
    props: {...initProps},
    components: {
        UniversalTable: () => import('@/components/TableWidgets/UniversalTable')
    }
}
</script>