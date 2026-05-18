<template>
    <div class="two_rows cursor-pointer" :title="record.target" @click="openSprint()">
        {{ record.target }}
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