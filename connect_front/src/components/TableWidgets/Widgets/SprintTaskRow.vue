<template>
    <div class="count_stat mr-2 cursor-pointer gap-2" @click="openSprint()">
        <div
            v-tippy
            :content="$t('task.new')"
            class="count_stat__item new">
            {{ record.new_task_count }}
        </div>
        <div
            v-tippy
            :content="$t('task.in_work')"
            class="count_stat__item process">
            {{ record.in_work_task_count }}
        </div>
        <div
            v-tippy
            :content="$t('task.completed')"
            class="count_stat__item completed">
            {{ record.completed_task_count }}
        </div>
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
                query.sptab = 'analytics'
                this.$router.push({ query });
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.count_stat {
    display: flex;
    align-items: center;

    &__item {
        height: 40px;
        width: 40px;
        color: #000;
        font-size: 14px;
        line-height: 40px;
        text-align: center;
        border-radius: 6px;

        &.new {
            background: #ced3fb;
        }

        &.process {
            background: #efbdbd;
        }

        &.completed {
            background: #bdf0cc;
        }
    }
}
</style>