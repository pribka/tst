<template>
    <div class="cursor-pointer" @click="openSprint()">
        <template v-if="record.begin_date && record.dead_line">
            {{ $moment(record.begin_date).format('DD.MM.YYYY') }} - {{ $moment(record.dead_line).format('DD.MM.YYYY') }}
        </template>
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