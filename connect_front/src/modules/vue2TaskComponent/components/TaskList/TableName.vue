<template>
    <div class="t_name" :style="indentStyle">
        <div class="flex items-center">
            <div class="mr-2 flex items-center gap-1" v-if="showChildren && record.children_count > 0">
                <a-button
                    v-if="!record.children"
                    type="link"
                    size="small"
                    :loading="loading"
                    class="p-0 text-current"
                    flaticon
                    @click="getChildren()"
                    icon="fi-rr-angle-small-down" />
                <a-button
                    v-else
                    type="link"
                    size="small"
                    flaticon
                    class="p-0 text-current"
                    @click="clearChildren()"
                    icon="fi-rr-angle-small-up" />
                <div v-if="record.children_count" :title="$t('task.subtask_count_tooltip')">
                    <div class="child_badge flex items-center justify-center">
                        {{ record.children_count }}
                    </div>
                </div>
            </div>

            <div class="item_name" :class="record.status === 'completed' && 'completed'" :title="text" @click="openTask(record)">
                {{ text }}
            </div>

            <!--<a-tag class="mr-1 name_tag" v-if="record.attachments && record.attachments.length" @click="openTask(record)">
                <a-icon type="paper-clip" />
                {{ record.attachments.length }}
            </a-tag>-->

            <span
                v-if="record.priority === 3"
                class="priority priority_large"
                v-tippy="{ inertia : true, duration : '[600,300]'}"
                :content="$t('task.large_priority')">
                <i class="fi fi-rr-bolt" />
            </span>
            <span
                v-if="record.priority === 4"
                v-tippy="{ inertia : true, duration : '[600,300]'}"
                :content="$t('task.very_large_priority')"
                class="priority priority_very_large">
                <i class="fi fi-rr-flame" />
            </span>
            <span
                v-if="record.priority === 0"
                v-tippy="{ inertia : true, duration : '[600,300]'}"
                :content="$t('task.very_low_priority')"
                class="priority priority_low">
                <i class="fi fi-rr-hourglass-start" />
            </span>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        value: Array,
        extendDrawer: {
            type: Boolean,
            default: false
        },
        text: {
            type: String,
            required: true
        },
        record: {
            type: Object,
            required: true
        },
        showChildren: {
            type : Boolean,
            default: true
        },
        main: {
            type: Boolean,
            default: false
        },
        reloadTask: {
            type: Function,
            default: () => null
        },
        indent: {
            type: Object,
            default: () => null
        },
        expanded: {
            type: Number,
            default: null
        },
        pageName: {
            type: String,
            default: ''
        },
        childParams: {
            type: Object,
            default: () => null
        }
    },
    computed: {
        indentStyle() {
            // Настройка приходит из props.indent: { step: number, levelField: string }
            const step = this.indent && typeof this.indent.step === 'number' ? this.indent.step : 20;
            const levelField = this.indent && this.indent.levelField ? this.indent.levelField : '_level';

            // Если в записи есть уровень — используем его; иначе, если есть parent_expand — считаем уровнем 1
            let level = 0;
            if (this.record && this.record[levelField] != null) {
                level = Number(this.record[levelField]) || 0;
            } else if (this.record && this.record.parent_expand) {
                level = 1;
            }
            return { paddingLeft: `${step * level}px` };
        }
    },
    data() {
        return {
            expandList: this.value,
            loading: false
        }
    },
    methods: {
        clearChildren() {
            // Шлём якорь конкретного экземпляра строки: (id + parent_expand)
            eventBus.$emit(`table_expand_row_${this.pageName}`, {
                action: 'collapse',
                anchor: {
                    id: this.record.id,
                    parent_expand: this.record.parent_expand ?? null
                }
            })

            const index = this.expandList.findIndex(row => row === this.record.id)
            if (index !== -1) {
                this.expandList.splice(index, 1)
                this.$emit('input', this.expandList)
            }
            this.$store.commit('task/TASK_CLEAR_CHILD', this.record)
        },
        async getChildren() {
            try {
                console.log(this.childParams, 'this.childParams')
                this.loading = true
                const data = await this.$store.dispatch('task/getChildren', {
                    task: this.record,
                    childParams: this.childParams || null
                })

                // Шлём тот же «якорь» экземпляра, по которому кликнули
                eventBus.$emit(`table_expand_row_${this.pageName}`, {
                    action: 'expand',
                    anchor: {
                        id: this.record.id,
                        parent_expand: this.record.parent_expand ?? null
                    },
                    row: data.results
                })

                this.expandList.push(`${this.record.id}-${this.expanded}`)
                this.$emit('input', this.expandList)
            } catch (error) {
                errorHandler({error, show: false})
            } finally {
                this.loading = false
            }
        },
        async openTask() {
            this.$store.commit('task/SET_PAGE_NAME', {
                pageName: this.pageName
            })

            if(this.main) {
                let query = Object.assign({}, this.$route.query)
                if(query.task && Number(query.task) !== this.record.id || !query.task) {
                    query.task = this.record.id
                    this.$router.push({query})
                    this.reloadTask(this.record)
                }
            } else {
                let query = Object.assign({}, this.$route.query)
                delete query.stab
                if(!query.task) {
                    query.task = this.record.id
                } else {
                    delete query.task
                }
                await this.$router.push({query})

                this.reloadTask(this.record)
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.child_badge{
    min-height: 20px;
    min-width: 20px;
    font-size: 12px;
    line-height: 12px;
    border-radius: 50%;
    background: #f9f0ff;
    color: #722ed1;
}
.t_name{
    display: inline-block;
    .name_tag{
        font-size: 10px;
        padding: 0 3px;
        line-height: 16px;
        margin-left: 5px;
    }
    .priority{
        margin-left: 5px;
        min-height: 16px;
        min-width: 16px;
        &.priority_very_large{
            color: rgb(255, 92, 92);
        }
        &.priority_large{
            color: rgb(255, 154, 1);
        }
        &.priority_low{
            color: rgb(68, 70, 72);
        }
    }
}
.item_name{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: color 0.3s;
    word-break: break-word;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    line-height: 20px;
    &:hover{
        color: var(--blue);
    }
    &.completed{
        color: var(--grayColor2);
        text-decoration: line-through;
    }
}
</style>
