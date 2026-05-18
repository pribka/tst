<template>
    <a-modal
        :visible="visible"
        @cancel="close"
        width="80%"
        :footer="null"
        destroyOnClose>
        <template #title>
            {{ title ? title : $t('list_form') }}
        </template>
        <ListView
            v-if="visible"
            ref="refListView"
            :addButtonText="addButtonText"
            :add="add"
            :tableType="tableType"
            :model="model"
            @select="select"
            :pageName="pageName"
            :endpoint="endpoint">
            <template v-slot:headerLeft="slotProps">
                <slot name="headerLeft" v-bind="slotProps" />
            </template>
        </ListView>
    </a-modal>
</template>

<script>
export default {
    components: {
        ListView: () => import('./index.vue')
    },
    props: {
        title: {
            type: String,
            default: ''
        },
        addButtonText: {
            type: String,
            default: ""
        },
        tableType: {
            type: String,
            required: true
        },
        model: {
            type: String,
            default: ""
        },
        pageName: {
            type: String,
            default: ""
        },
        endpoint: {
            type: String,
            required: true
        },
        add: {
            type: [Function, Boolean],
            default: false
        }
    },
    data() {
        return {
            visible: false
        }
    },
    methods: {
        open() {
            this.visible = true
        },
        close() {
            this.visible = false
            this.$emit('close')
        },
        select(items) {
            this.$emit('select', items)
            this.close()
        }
    }
}

</script>