<template>
    <div class="flex-grow">
        <UniversalTable 
            :model="pageModel"
            :pageName="pageName"
            class="min-h-0"
            autoHeight
            :colParams="{
                getPopupContainer: getPopupContainer,
                actions: actions,
                editHandler: editTime,
                deleteHandler: deleteHandler,
                listType: 'eventList',
                workObj: event
            }"
            :scrollWrapper="tableFullHeight ? {} : {x: 1300, y: minHeight}"
            :params="{
                event_calendar: event.id
            }"
            tableType="time_tracking_event"
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