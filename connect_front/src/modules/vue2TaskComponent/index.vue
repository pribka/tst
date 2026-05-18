<template>
    <div class="task_wrapper">
        <div class="task_body_wrapper">
            <router-view 
                :taskType="taskType" 
                :pageConfig="pageConfig"
                :page_name="page_name">
                <slot />
            </router-view>
        </div>
    </div>
</template>

<script>
export default {
    name: 'TaskIndex',
    props: {
        taskType: {
            type: String,
            default: 'task'
        },
        pageConfig: {
            type: Object,
            default: () => null
        },
        meetings: {
            type: Boolean,
            default: false
        },
        page_name: {
            type: String,
            default: ''
        }
    }
}
</script>