<template>
    <div class="two_rows cursor-pointer" :title="expectedResult" @click="openSprint()">
        {{ expectedResult }}
    </div>
</template>
<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
    },
    computed: {
        expectedResult() {
            if(this.record.expected_result?.length)
                return this.record.expected_result.join(', ')
            return ''
        }
    },
    methods: {
        openSprint() {
            const query = Object.assign({}, this.$route.query);
            if (query.sprint === this.record.id) {
                delete query.sprint;
                this.$router.replace({ query });
            }
            if (
                (query.sprint && Number(query.sprint) !== this.record.id) ||
        !query.sprint
            ) {
                query.sprint = this.record.id;
                this.$router.push({ query });
            }
        },
    }
}
</script>