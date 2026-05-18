<template>
    <div class="h-full w-full flex items-center justify-center">
        <template v-if="mode === 'single'">
            <a-radio 
                :checked="checked"    
                @click.stop="toggleSelect" />
        </template>
        <template v-else-if="mode === 'multiple'">
            <a-checkbox 
                :checked="checked"    
                @click.stop="toggleSelect"/>
        </template>
    </div>
</template>

<script>
export default {
    props: {
        selectedRows: {
            type: Array,
            required: true
        },
        onSelectChange: {
            type: Function,
            required: true
        },
        record: {
            type: Object,
            required: true
        },
        mode: {
            type: String,
            default: 'single'
        }
    },
    computed: {
        checked() {
            return this.selectedRows.findIndex(item => item.id === this.record.id) !== -1
        }
    },
    methods: {
        toggleSelect() {
            this.onSelectChange?.(this.record)
        }
    }
}
</script>
