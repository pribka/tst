<template>
    <div class="time_card">
        <div class="item_field">
            <div v-if="item.description">
                <span class="item_head">
                    {{ $t('calendar.desc') }}:
                </span>
                <div class="mt-1">
                    <TextViewer 
                        collapsible
                        overlayColor="#fff"
                        :body="item.description" />
                </div>
            </div>
        </div>
        <div class="item_field">
            <span class="item_head">
                {{ $t('calendar.hours') }}:
            </span>
            <span>
                {{ formattedDuration }} 
            </span>
        </div>
        <div v-if="item.date" class="item_field">
            <span class="item_head">
                {{ $t('calendar.date') }}:
            </span>
            <span>
                {{ $moment(item.date).format('DD.MM.YYYY') }}
            </span>
        </div>
        <div v-if="item.author" class="item_field flex items-center">
            <span class="item_head mr-2">
                {{ $t('calendar.author') }}:
            </span>
            <span>
                <Profiler 
                    :user="item.author"
                    :avatarSize="18"
                    :getPopupContainer="trigger => trigger.parentNode"
                    hideSupportTag />
            </span>
        </div>
        <div v-if="isAuthor" class="item_field flex items-center gap-2 mt-4">
            <a-button type="flat_primary" @click="editTime(item)" block>
                {{ $t('calendar.edit') }}
            </a-button>
            <a-button type="flat_danger" @click="deleteTime(item)" block>
                {{ $t('calendar.delete') }}
            </a-button>
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import eventBus from "@/utils/eventBus"
export default {
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
    },
    props: {
        event: {
            type: Object,
            required: true
        },
        item: {
            type: Object,
            required: true
        },
        deleteHandler: {
            type: Function,
            default: () => {}
        },
        editTime: {
            type: Function,
            default: () => {}
        },
        pageModel: {
            type: String,
            required: true
        },
        pageName: {
            type: String,
            required: true
        },
    },
    computed: {
        user() {
            return this.$store.state.user.user
        },
        isAuthor() {
            return this.user?.id === this.item.author?.id
        },
        formattedDuration() {
            const sec = Number(this.item.duration)
            if (!sec || !Number.isFinite(sec)) return '0 секунд'

            const hours = Math.floor(sec / 3600)
            const minutes = Math.floor((sec % 3600) / 60)
            const seconds = sec % 60

            const plural = (num, one, few, many) => {
                const n = Math.abs(num) % 100
                const n1 = n % 10
                if (n > 10 && n < 20) return many
                if (n1 > 1 && n1 < 5) return few
                if (n1 === 1) return one
                return many
            }

            let res = ''

            if (hours > 0)
                res += `${hours} ${plural(hours, this.$t('helpdesk.hour1'), this.$t('helpdesk.hour2'), this.$t('helpdesk.hour3'))}`

            if (minutes > 0) {
                if (res) res += ' '
                res += `${minutes} ${plural(minutes, this.$t('helpdesk.minute1'), this.$t('helpdesk.minute2'), this.$t('helpdesk.minute3'))}`
            }

            if (!res)
                res = `${seconds} ${plural(seconds, this.$t('helpdesk.second1'), this.$t('helpdesk.second2'), this.$t('helpdesk.second3'))}`

            return res
        }
    },
    methods: {
        deleteTime(item) {
            this.$confirm({
                title: this.$t('task.warning'),
                content: this.$t('task.item_delete_message'),
                zIndex: 9999,
                cancelText: this.$t('task.close'),
                okText: this.$t('task.remove'),
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: item.id, is_active: false }])
                            .then(() => {
                                this.$message.success(this.$t('task.item_removed'))
                                if (this.$store.hasModule('workplan')) {
                                    this.$store.dispatch('workplan/updateItem', {
                                        item: this.event,
                                        list: 'eventList'
                                    })
                                    if(item.related_object) {
                                        if(item.related_object && item.related_object.type === 'tasks.TaskModel') {
                                            this.$store.dispatch('workplan/updateItem', {
                                                item: item.related_object,
                                                list: 'taskList'
                                            })
                                        }
                                    }
                                }
                                eventBus.$emit(`update_filter_${this.pageModel}_${this.pageName}`)
                                this.deleteHandler(item)
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({error})
                                reject()
                            })
                    })
                },
                onCancel() {}
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.time_card{
    &:not(:last-child) {
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--borderColor);
    }
    .item_field {
        margin-bottom: 8px;
    }
    .item_head {
        margin-bottom: 0.3em;   
    }
}
</style>