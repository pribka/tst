<template>
    <div ref="treeSelectWrapper" class="flex">
        <a-tree-select
            v-model="innerValue"
            :treeData="treeData"
            tree-data-simple-mode
            :loadData="loadTreeData"
            :placeholder="$t('Select field for aggregation')"
            inputType="ghost"
            size="large"
            allowClear
            :getPopupContainer="() => $refs.treeSelectWrapper"
            :dropdown-style="{ maxHeight: '400px', overflow: 'auto' }">
            <template #suffixIcon>
                <i class="fi fi-rr-angle-small-down" />
            </template>
            <template slot="notFoundContent">
                <a-empty :description="$t('no_data')" />
            </template>
        </a-tree-select>
    </div>
</template>

<script>
export default {
    name: 'TreeSelectField',
    props: {
        value: {
            type: [Object],
            default: null,
        },
        modelName: {
            type: String,
            required: true,
        },
    },
    data() {
        return {
            treeData: [],
        };
    },
    computed: {
        innerValue: {
            get() {
                return this.value?.id || null;
            },
            set(value) {
                const objectValue = this.treeData.find(node => node.id === value)
                this.$emit('input', objectValue);
                this.$emit('change', objectValue);
            }
        },
    },
    mounted() {
        this.$store.dispatch('reports/getModelMeta', this.modelName)
            .then(modelMeta => {
                this.treeData = modelMeta.fields.map(field => ({ 
                    ...field, 
                    pId: 0,
                    value: field.name,
                    title: field.verbose_name,
                    defaultTitle: field.verbose_name,
                    id: field.name,
                    isLeaf: field.is_leaf || !field.related_model,
                    active: true
                }))
            })
            .catch(error => {
                console.error(error)
            })
    },
    methods: {
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
        loadTreeData(rawNode) {
            const node = rawNode.dataRef 
            return this.getRelatedModelMeta(node.related_model.toLowerCase())
                .then(data => {
                    const fields = data.fields.map(field => ({
                        ...field,
                        active: true,
                        id: `${node.name}__${field.name}`,
                        pId: node.id,
                        name: `${node.name}__${field.name}`,
                        value: `${node.name}__${field.name}`,
                        key: `${node.name}__${field.name}`,
                        defaultTitle: `${node.defaultTitle} > ${field.verbose_name}`,
                        title: `${node.defaultTitle} > ${field.verbose_name}`,
                        isLeaf: !field.related_model
                    }))
                    this.treeData = this.treeData.concat(...fields)
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('Failed to get available fields'))
                })
        },
    },
};
</script>
