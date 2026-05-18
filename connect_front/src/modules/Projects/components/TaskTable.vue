<template>
    <a-table 
        :columns="columns" 
        :data-source="tableData" 
        :row-key="record => record.id || record.key"
        bordered 
        :loading="loading"
        :pagination="false"
        :rowClassName="rowClassName"
        :scroll="tableScroll"
        :locale="{
            emptyText: $t('no_data')
        }"
        :expanded-row-keys.sync="expandedRowKeys">
        <template slot="expandIcon" slot-scope="props">
            <template v-if="props.record?.children?.length">
                <a-button 
                    flaticon 
                    :icon="getExpandIcon(props.expanded)"
                    type="link" 
                    size="small" 
                    @click="props.onExpand(props.record, $event)">
                </a-button>
            </template>
            <span></span>
        </template>
    </a-table>
</template>

<script>

import {h} from 'vue'
import TaskTableActionsRow from './TaskTableActionsRow.vue';
import TaskTableAddRow from './TaskTableAddRow.vue';
import TaskTableNameRow from './TaskTableIdNameRow.vue';
export default {
    components: {
        // eslint-disable-next-line vue/no-unused-components
        TaskTableActionsRow,
        // eslint-disable-next-line vue/no-unused-components
        TaskTableNameRow
    },
    props: {
        template: {
            type: Object,
            default: null
        },
        loading: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            expandedRowKeys: [],
            columns: [
                {
                    title: "Задача",
                    dataIndex: "name",
                    key: "name",
                    customRender: this.nameRender
                },
                {
                    title: "Описание",
                    dataIndex: "description",
                    key: "description",
                    customRender: this.renderContent,
                },
                {
                    title: "Продолжительность в днях",
                    dataIndex: "duration",
                    width: 170,
                    key: "duration",
                    customRender: this.renderContent,
                },
                {
                    title: "",
                    dataIndex: "actions",
                    key: "actions",
                    width: 200,
                    customRender: this.renderContent,
                },
            ],
        }
    },
    computed: {
        tableData() {
            return this.$store.state.projects.templateTable?.results
        },
        user() {
            return this.$store.state.user.user
        },
        isPublic() {
            return this.template?.is_public
        },
        canChange() {
            return this.user.id === this.template?.author?.id
        },
        windowWidth() {
            return this.$store.state.windowWidth
        },
        tableScroll() {
            const scroll = {
                x: 1000,
            }
            if (this.windowWidth < 1000) {
                scroll.y = 300
            }
            return scroll
        }
    },
    methods: {
        rowClassName(record) {
            if (record.task_type === 'stage') {
                return 'special-row'
            }
            return ''
        },
        renderContent(value, row, index, column) {
            const obj = {
                children: value,
                attrs: {},
            };
            if (column.key === 'duration') {
                if (value) {
                    obj.children = value.replace('00:00:00', '')
                }
            }
            if (column.key === 'actions') {
                if (this.canChange) {
                    obj.children = h(TaskTableActionsRow, {
                        props: { record: row, template: this.template?.id,  },
                    })
                } else {
                    obj.children = ''
                }
            }
            if (row.is_action) {
                obj.attrs.colSpan = 0;
            }

            return obj;
        },
        nameRender(text, row, index) {
            if (!row.is_action) {
                return {
                    children: h(TaskTableNameRow, {
                        props: { record: row, template: this.template?.id },
                    }),
                }
            }
            return {
                children: h(TaskTableAddRow, {
                    props: { record: row, template: this.template?.id },
                }),
                attrs: { colSpan: 4 }
            }
        },
        getExpandIcon(expanded) {
            return expanded ? 'fi-rr-cross-circle' : 'fi-rr-add'
        }
    }
};
</script>

<style lang="scss" scoped>
::v-deep {
    .ant-table-row {
        td[colspan] {
            padding: 8px 16px;
        }
    }

    .special-row {
        background: var(--primaryHover);
    }
}
</style>