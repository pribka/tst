<template>
    <div>
        <template v-if="isTask">
            <template v-if="record.new">
                <a-form-model
                    :model="storeRecord">
                    <a-form-model-item 
                        prop="name" 
                        :rules="[{ required: true, message: $t('field_required') }]">
                        <a-input :placeholder="$t('task.task_name')" v-model="storeRecord.name"></a-input>                
                    </a-form-model-item>
                </a-form-model>
            </template>
            <template v-else>
                {{ record.name }}
            </template>
        </template>
        <template v-else>
            <div class="t_name">
                <div class="flex items-center">
                    <template v-if="hasChildren">
                        <div class="mr-1">
                            <a-button
                                v-if="!isExpanded"
                                type="link"
                                size="small"
                                :loading="loading"
                                class="p-0 text-current"
                                @click="getChildren()"
                                icon="plus-circle" />
                            <a-button 
                                v-else
                                type="link"
                                size="small"
                                class="p-0 text-current"
                                @click="clearChildren()"
                                icon="minus-circle" />
                        </div>
                    </template>
                    <div class="item_name blue_color">
                        {{ record.name }}
                    </div>
                    <a-tag class="ml-1 mr-0 name_tag" v-if="record.children_count">
                        <span class="flex items-center">
                            <i class="fi fi-rr-folder-tree mr-1"></i>
                            {{ record.children_count }}
                        </span>
                    </a-tag>
                </div>
            </div>
        </template>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'

export default {
    props: {
        state: {
            type: Object,
            default: () => {}
        },
        changeState: {
            type: Function,
            default: () => {}
        },
        record: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            default: ''
        },
        model: {
            type: String,
            default: ''
        }
    },
    computed: {
        computedStoreKey() {
            if (this.storeKey) return this.storeKey
            return this.model+this.pageName
        },

        isMilestone() {
            return this.record.task_type === 'milestone'
        },
        isExpanded() {
            return this.state?.[this.record.id]
        },
        hasChildren() {
            return this.record.has_children
        },
        isTask() {
            return this.record.hasOwnProperty('task_type')
        },
        storeRecord() {
            const tableRows = this.$store.state.table.tableRows[this.computedStoreKey]
            const record = tableRows.find(row => this.record.id === row.id)
            return record
        }
    },
    data() {
        return {
            loading: false,
        }
    },
    methods: {
        clearChildren() {
            eventBus.$emit(`table_row_${this.pageName}`, {
                action: 'collapse',
                parentId: this.record.id,
            })

            this.changeState({
                ...this.state,
                [this.record.id]: false
            })
            this.$store.commit('task/TASK_CLEAR_CHILD', this.record)
        },
        async getChildren() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/work_groups/task_templates/?project_stage=${this.record.id}`)
                if (data?.length) {
                    eventBus.$emit(`table_row_${this.pageName}`, {
                        action: 'expand',
                        parentId: this.record.id,
                        row: data
                    })
                }
                
                this.changeState({
                    ...this.state,
                    [this.record.id]: true
                })
                
            } catch(error) {
                console.error(error)
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
.t_name{
    display: inline-block;
    .name_tag{
        font-size: 10px;
        padding: 0 3px;
        line-height: 16px;
    }
    .priority{
        margin-left: 5px;
        min-height: 16px;
        min-width: 16px;
        img{
            width: 16px;
            height: 16px;
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
    &:hover{
        color: var(--primaryColor);
    }
    &.completed{
        color: var(--grayColor2);
        text-decoration: line-through;
    }
}
</style>
