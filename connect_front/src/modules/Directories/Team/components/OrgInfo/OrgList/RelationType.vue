<template>
    <div>{{ currentType }}</div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        org: {
            type: [Object],
            required: true
        }
    },
    computed: {
        currentType() {
            if(this.record.contractor.id === this.org.id)
                return this.record.relation_type.name_parent
            else
                return this.record.relation_type.name
        }
    }
}
</script>