<template>
    <div class="item_name two_rows" :title="record.name" @click="openSprint()">{{ record.name }}</div>
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

<style lang="scss" scoped>
.item_name{
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        color: var(--blue);
    }
    &.completed{
        color: var(--grayColor2);
        text-decoration: line-through;
    }
}
</style>