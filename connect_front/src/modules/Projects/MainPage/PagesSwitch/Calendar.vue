<template>
    <Calendar 
        :related_object="id" 
        :addEventCheck="addEventCheck" />
</template>

<script>
export default {
    components: {
        Calendar: () => import('@apps/Calendar')
    },
    props: {
        id: {
            type: [String, Number],
            required: true
        },
        isStudent: {
            type: Boolean,
            required: true
        },
        isFounder: {
            type: Boolean,
            required: true
        }
    },
    computed: {
        addEventCheck() {
            return this.isStudent || this.isFounder ? true : false
        }
    }
}
</script>