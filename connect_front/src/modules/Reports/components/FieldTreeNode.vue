<template>
    <li class="node" @mouseenter="hover = true" @mouseleave="hover = false">
        <div class="node__title" :class="node.name === 'add_aggregate_field' && 'blue_color'">
            <a-spin 
                v-if="loading"
                size="small"
                class="w-4 -mb-0.5" />
            <span v-else-if="hasChildren" class="toggle-icon" @click="toggle">
                <a-icon :type="expanded ? 'down' : 'right'" />
            </span>

            <span class="node-name">{{ node.verbose_name }}</span>

            <span class="node__actions">
                <div 
                    v-if="isChecked" 
                    class="flex items-center justify-center w-6 h-6">
                    <i class="check-icon fi fi-rr-check"></i>
                </div>
                <a-button
                    v-else-if="showPlusIcon"
                    @click="plusClickHandler"
                    type="ui"
                    ghost
                    shape="circle"
                    flaticon
                    size="small"
                    class="node__add-button"
                    :class="isMobile && 'node__add-button_mobile'">
                    <i class="plus-icon fi fi-rr-plus-small"></i>
                </a-button>
            </span>
        </div>

        <!-- Дочерние узлы, если есть и раскрыты -->
        <ul v-if="hasChildren && expanded">
            <FieldTreeNode
                v-for="(child, index) in children"
                :key="index"
                :checkedFields="checkedFields"
                :node="child"
                @add="$emit('add', $event)"/>
        </ul>
    </li>
</template>

<script>
export default {
    name: 'FieldTreeNode',
    props: {
        node: {
            type: Object,
            required: true,
        },
        checkedFields: {
            type: Array,
            default: () => [],
        },
        loadData: {
            type: Function,
            default: () => {},
        },
    },
    data() {
        return {
            hover: false,
            expanded: false,
            children: this.node.children || [],
            loading: false
        };
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        isChecked() {
            const nodeNameField = this.node.aggregate ? 'verbose_name' : 'name'
            return this.checkedFields.some(fieldName => fieldName === this.node[nodeNameField])
        },
        hasChildren() {
            if (this.node.is_leaf) { return false }
            return this.node.related_model || this.children?.length;
        },
        showPlusIcon() {
            return this.node.create_aggregate || !this.node.unselectable
        }
    },
    methods: {
        plusClickHandler() {
            if (this.node.name === 'add_aggregate_field') {
                this.$store.commit('reports/OPEN_CREATE_AGGREGATE_FIELD_MODAL')
            } else {
                this.$emit('add', this.node)
            }
        },
        loadTreeData(node) {
            this.loading = true
            this.getRelatedModelMeta(node.related_model.toLowerCase())
                .then(data => {
                    const fields = data.fields.map(field => ({
                        ...field,
                        active: true,
                        name: `${node.name}__${field.name}`,
                        key: `${node.name}__${field.name}`,
                        defaultTitle: `${node.defaultTitle} > ${field.verbose_name}`,
                        title: `${node.defaultTitle} > ${field.verbose_name}`
                    }))

                    this.children = fields

                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('Failed to get available fields'))
                })
                .finally(() => 
                    this.loading = false
                )
        },
        getRelatedModelMeta(modelName) {
            const params = { meta: true }
            const url = `reports/${modelName}/`
            return this.$http.get(url, { params })
                .then(({ data }) => data?.meta)
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('Failed to get fields list'))
                })
        },
        toggle() {
            this.expanded = !this.expanded;
            if (this.expanded) {
                if (!this.children.length) {
                    this.loadTreeData(this.node)
                }
            }
        },
    },
};
</script>

<style lang="scss" scoped>
.node {
}

.node__title {
  display: flex;
  align-items: center;
  justify-content: space-between;

  padding: 8px 12px;
  border-radius: 8px;
  user-select: none;
  &:hover {
    background-color: #ffffff;   
  }
}

.node__actions {
  height: 24px;
}

.node__add-button {
  display: none;
}

.node__add-button {
  &.node__add-button_mobile {
    display: flex;
    justify-content: center;
    align-items: center;
  }
}

.node__title:hover .node__add-button {
  display: flex;
  justify-content: center;
  align-items: center;
}

.plus-icon {
  color: #888888;
  font-size: 18px;
}

.check-icon {
  color: #A8C985;
}


.node-name {
  flex-grow: 1;
  padding-left: 4px;
}

.actions {
  cursor: pointer;
  color: #1890ff;
  font-size: 14px;
  padding-left: 8px;
}


.toggle-icon {
  cursor: pointer;
  width: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-placeholder {
  display: inline-block;
  width: 16px;
}

ul {
  list-style: none;
  padding-left: 16px;
  margin: 0;
}
</style>
