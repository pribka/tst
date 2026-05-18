<template>
    <Calendar 
        :related_object="task.id"
        :addEventCheck="addEventCheck" />
</template>

<script>
export default {
    props: {
        task: {
            type: Object,
            required: true
        },
        isOperator: {
            type: Boolean,
            default: false
        },
        isAuthor: {
            type: Boolean,
            required: true
        },
        myTask: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        addEventCheck() {
            return this.myTask || this.isAuthor || this.isOperator ? true : false
        }
    },
    components: {
        Calendar: () => import('@apps/Calendar')
    }
}
</script>