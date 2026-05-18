<template>
    <div class="time_card">
        <div 
            v-for="col in pageConfig.tableInfo" 
            :key="col.field"
            :class="col.class ? col.class : ''"
            class="item_field">
            <template v-if="col.field === 'work_type'">
                <template v-if="item.work_type">
                    <div class="item_field">
                        <span class="item_head">
                            {{ col.headerName }}:
                        </span>
                        <span>
                            {{ item.work_type.name }}
                        </span>
                    </div>
                </template>
            </template>
            <template v-if="col.field === 'description'">
                <div class="item_field">
                    <div v-if="item.description">
                        <span class="item_head">
                            {{ col.headerName }}:
                        </span>
                        <div class="mt-1">
                            <TextViewer 
                                collapsible
                                overlayColor="#fff"
                                :body="item.description" />
                        </div>
                    </div>
                </div>
            </template>
            <template v-if="col.field === 'is_result' && item.is_result">
                <div class="item_field">
                    <div>
                        <span class="item_head">
                            {{ col.headerName }}:
                        </span>
                        <div class="mt-1">
                            <i class="fi fi-rr-check text-green-500" />
                        </div>
                    </div>
                </div>
            </template>
            <template v-if="col.field === 'author'">
                <div class="item_field flex items-center">
                    <span class="item_head mr-2">
                        {{ col.headerName }}:
                    </span>
                    <span>
                        <Profiler 
                            :user="item.author"
                            :avatarSize="18"
                            :getPopupContainer="trigger => trigger.parentNode"
                            hideSupportTag />
                    </span>
                </div>
                <template v-if="isModerator && item.user">
                    <div class="item_field flex items-center">
                        <span class="item_head mr-2">
                            {{ $t('task.user') }}:
                        </span>
                        <span>
                            <Profiler 
                                :user="item.user"
                                :avatarSize="18"
                                :getPopupContainer="trigger => trigger.parentNode"
                                hideSupportTag />
                        </span>
                    </div>
                </template>
            </template>
            <div v-if="col.field === 'hours'" class="item_field">
                <span class="item_head">
                    {{ col.headerName }}:
                </span>
                <span>
                    <span v-if="isDurations" :title="formattedDuration">
                        {{ formattedDuration }}
                    </span>
                    <template v-else>
                        <span v-if="item.measure_unit" :title="`${item.hours} ${item.measure_unit.name}`">
                            {{ item.hours }} {{ item.measure_unit.name }}
                        </span>
                        <span v-else :title="item.hours">
                            {{ item.hours }}
                        </span>
                    </template>
                </span>
            </div>
            <template v-if="col.field === 'date'">
                <div v-if="item.date" class="item_field">
                    <span class="item_head">
                        {{ col.headerName }}:
                    </span>
                    <span>
                        {{ $moment(item.date).format('DD.MM.YYYY') }}
                    </span>
                </div>
            </template>
            <div v-if="col.field === 'actions'" class="item_field flex items-center gap-2 mt-4">
                <template v-if="canAny">
                    <a-button v-if="canEdit" type="flat_primary" @click="editTime(item)" block>
                        {{ $t('task.edit') }}
                    </a-button>
                    <a-button v-if="canDelete" type="flat_danger" @click="deleteTime(item)" block>
                        {{ $t('task.remove') }}
                    </a-button>
                </template>
            </div>
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
        actions: {
            type: Object,
            default: () => null
        },
        editTime: {
            type: Function,
            default: () => {}
        },
        deleteHandler: {
            type: Function,
            default: () => {}
        },
        pageModel: {
            type: String,
            default: ""
        },
        pageName: {
            type: String,
            default: ""
        },
        item: {
            type: Object,
            required: true
        },
        task: {
            type: Object,
            required: true
        },
        isModerator: { type: Boolean, default: true }
    },
    computed: {
        workTimeSettings() {
            return this.$store.state.task.workTimeSettings
        },
        pageConfig() {
            if(this.workTimeSettings?.[this.task.task_type])
                return this.workTimeSettings[this.task.task_type]
            else
                return null
        },
        user() {
            return this.$store.state.user.user
        },
        isAuthor() {
            return !!(this.user && this.item && this.item.author && this.user?.id === this.item.author.id)
        },
        canEdit() {
            if(this.actions?.edit_accounting?.availability)
                return true
            return this.isAuthor
        },
        canDelete() {
            if(this.actions?.delete_accounting?.availability)
                return true
            return this.isAuthor
        },
        canAny() {
            return this.canEdit || this.canDelete
        },
        isDurations() {
            return this.item?.measure_unit?.code === 'hours' && this.item?.duration
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
                                        item: this.task,
                                        list: 'taskList'
                                    })
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

<style lang="scss">
.time_card {
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