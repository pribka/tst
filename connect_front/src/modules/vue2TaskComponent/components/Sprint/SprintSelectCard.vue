<template>
    <div 
        class="sprint_select_card" 
        :class="bgNegative && 'bg_negative'"
        ref="sprintCard">
        <div class="sprint_select_card__header">
            <div 
                class="flex items-center pr-2">
                <a-tag :color="statusColor">
                    {{ $t(`sprint.${sprint.status}`) }}
                </a-tag>
                <div class="card_info ml-3">
                    <div v-if="sprint.begin_date && sprint.dead_line" class="sprint_dates">
                        {{ $moment(sprint.begin_date).format('DD.MM.YY') }} - {{ $moment(sprint.dead_line).format('DD.MM.YY') }}
                    </div>
                    <div 
                        class="card_name" 
                        :title="sprint.name">
                        {{ sprint.name }}
                    </div>
                </div>
            </div>
            <div class="mt-3 sm:mt-0 sm:flex sm:items-center sm:justify-end">
                <a-button 
                    type="primary" 
                    ghost 
                    :block="isMobile"
                    :loading="addLoading"
                    size="large"
                    @click="addToSprint()">
                    {{ $t('task.add_to_sprint') }}
                </a-button>
            </div>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus';
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        sprint: {
            type: Object,
            required: true
        },
        inject: {
            type: Boolean,
            default: false
        },
        task: {
            type: Object,
            required: true
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        bgNegative: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            loading: false,
            addLoading: false
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        statusColor() {
            switch (this.sprint.status) {
            case "new":
                return "blue";
                break;
            case "in_process":
                return "purple";
                break;
            case "completed":
                return "green";
                break;
            default:
                return "blue";
            }
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.sprintCard
        },
        openSprint() {
            const query = Object.assign({}, this.$route.query)
            if(query.sprint && Number(query.sprint) !== this.sprint.id || !query.sprint) {
                query.sprint = this.sprint.id
                this.$router.push({query})
            }
        },
        async addToSprint() {
            try {
                this.addLoading = true
                const { data } = await this.$http.put(`/tasks/task/${this.task.id}/set_sprint/`, {
                    sprint: this.sprint.id
                })
                if(data) {
                    this.$message.success(`${this.$t('task.task_added_to_sprint')}: ${this.sprint.name}`)
                    eventBus.$emit(`task_update_actions_${this.task.id}`)
                    eventBus.$emit('sprint_update_table_reload')
                    this.closeDrawer()
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.addLoading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.sprint_select_card{
    padding: 20px 15px;
    color: #000;
    border-radius: 8px;
    &.bg_negative{
        background: #f7f9fc;
    }
    &:not(:last-child){
        border-bottom: 1px solid var(--border2);
    }
    &__header{
        @media (min-width: 768px) {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
    }
    .sprint_status{
        background: #1D65C0;
        border-radius: 30px;
        height: 30px;
        padding-left: 10px;
        padding-right: 10px;
        color: #fff;
        line-height: 30px;
        text-align: center;
        white-space: nowrap;
        @media (max-width: 767.98px) {
            font-size: 12px;
        }
        @media (min-width: 768px) {
            min-width: 112px;
            line-height: 35px;
            padding-left: 20px;
            padding-right: 20px;
            height: 35px;
        }
    }
    .sprint_dates{
        opacity: 0.3;
        margin-bottom: 1px;
        font-size: 14px;
    }
    .card_name{
        font-size: 16px;
        line-height: 20px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        word-break: break-word;
    }
}
</style>