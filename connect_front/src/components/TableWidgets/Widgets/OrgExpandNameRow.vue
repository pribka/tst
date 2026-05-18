<template>
    <div class="org_name" :style="indentStyle">
        <div class="row_wrap flex items-center">
            <div v-if="showExpandControl" class="expand_wrap flex items-center">
                <a-button
                    v-if="!isExpanded"
                    type="link"
                    size="small"
                    :loading="loading"
                    class="p-0 text-current"
                    flaticon
                    icon="fi-rr-angle-small-down"
                    @click="getChildren" />
                <a-button
                    v-else
                    type="link"
                    size="small"
                    class="p-0 text-current"
                    flaticon
                    icon="fi-rr-angle-small-up"
                    @click="clearChildren" />
            </div>

            <div class="child_badge_wrap" v-if="hasChildren">
                <div class="child_badge flex items-center justify-center">
                    {{ childrenCount }}
                </div>
            </div>

            <div class="logo_wrap">
                <a-avatar :size="26" v-if="record.logo" :src="record.logo" />
                <a-avatar :size="26" v-else icon="team" />
            </div>

            <div class="item_name" :title="orgName" @click="openOrganizationDrawer">
                {{ orgName }}
            </div>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        pageName: {
            type: String,
            default: ''
        },
        showChildren: {
            type: Boolean,
            default: true
        },
        state: {
            type: Object,
            default: () => ({})
        },
        changeState: {
            type: Function,
            default: () => {}
        },
        indent: {
            type: Object,
            default: () => null
        }
    },
    data() {
        return {
            loading: false
        }
    },
    computed: {
        childrenCount() {
            return Number(this.record?.structural_division_count || 0)
        },
        hasChildren() {
            return this.childrenCount > 0
        },
        orgName() {
            return this.record?.name || ''
        },
        rowAnchor() {
            return {
                id: this.record?.id,
                parent_expand: this.record?.parent_expand ?? null
            }
        },
        isExpanded() {
            return Boolean(this.record?.children)
        },
        showExpandControl() {
            return this.showChildren && this.hasChildren
        },
        indentStyle() {
            const step = this.indent && typeof this.indent.step === 'number' ? this.indent.step : 20
            const levelField = this.indent && this.indent.levelField ? this.indent.levelField : '_level'

            let level = 0
            if (this.record && this.record[levelField] != null) {
                level = Number(this.record[levelField]) || 0
            } else if (this.record && this.record.parent_expand) {
                level = 1
            }

            return { paddingLeft: `${step * level}px` }
        }
    },
    methods: {
        clearChildren() {
            eventBus.$emit(`table_expand_row_${this.pageName}`, {
                action: 'collapse',
                anchor: this.rowAnchor
            })

            this.$set(this.record, 'children', false)
        },
        async getChildren() {
            try {
                if (this.isExpanded) {
                    this.clearChildren()
                    return
                }
                this.loading = true
                const { data } = await this.$http.get('/users/my_organizations/', {
                    params: {
                        parent: this.record.id,
                        page_size: 100
                    }
                })

                const rows = Array.isArray(data?.results) ? data.results : (Array.isArray(data) ? data : [])

                if (rows.length) {
                    eventBus.$emit(`table_expand_row_${this.pageName}`, {
                        action: 'expand',
                        anchor: this.rowAnchor,
                        row: rows
                    })
                }

                this.$set(this.record, 'children', true)
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.loading = false
            }
        },
        openOrganizationDrawer() {
            const query = {
                organization_drawer: 'detail',
                organization_id: this.record.id
            }

            if (this.record?.parent_expand) {
                query.parent_id = this.record.parent_expand
            }

            this.$router.push({ query })
        }
    }
}
</script>

<style lang="scss" scoped>
.org_name {
    display: inline-block;
    width: 100%;
}

.row_wrap {
    width: 100%;
    min-width: 0;
}

.expand_wrap {
    min-width: 18px;
    margin-right: 6px;
}

.child_badge_wrap {
    margin-right: 8px;
    display: flex;
    align-items: center;
}

.logo_wrap {
    margin-right: 8px;
    flex-shrink: 0;
}

.child_badge {
    min-height: 20px;
    min-width: 20px;
    font-size: 12px;
    line-height: 12px;
    border-radius: 50%;
    background: #f9f0ff;
    color: #722ed1;
}

.item_name {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    word-break: break-word;
    line-height: 20px;
    min-width: 0;
    flex: 1;
    cursor: pointer;
    transition: color 0.2s ease;
    &:hover {
        color: var(--blue);
    }
}
</style>
