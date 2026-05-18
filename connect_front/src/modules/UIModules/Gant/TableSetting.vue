<template>
    <div>
        <span @click="openModal">
            <slot name="button">
                <a-button
                    type="ui" 
                    flaticon
                    shape="circle"
                    icon="fi-rr-settings" />
            </slot>
        </span>
        <a-modal
            @cancel="closeModal"
            :visible="modalVisible">
            <div class="columns_checkbox_group flex flex-col">
                <div class="mb-2 font-semibold">
                    {{ $t('table.settings') }}
                </div>
                <a-checkbox-group 
                    v-model="activeColumns">
                    <div
                        v-for="column in columns"
                        :key="column.value"
                        class="mt-1 first:mt-0">
                        <a-checkbox :value="column.value" class="flex items-center">
                            {{ column.label }}
                        </a-checkbox>
                    </div>
                </a-checkbox-group>
            </div>
            <template #footer>
                <div class="flex">
                    <a-button 
                        class="mr-2"
                        type="ui"
                        block
                        @click="setDefaultSettings">
                        {{ $t('table.default') }}
                    </a-button>
                    <a-button 
                        block
                        type="primary"
                        @click="submit">
                        {{ $t('table.confirm') }}
                    </a-button>
                </div>
            </template>
        </a-modal>
    </div>
</template>

<script>
export default {
    data() {
        return {
            modalVisible: false,
            activeColumns: [
                'start_date',
                'duration',
                'progress',
                'result',
            ],
            columns: [
                { 
                    value: 'start_date', 
                    label: this.$t('Start date'), 
                    active: true 
                },
                { 
                    value: 'duration', 
                    label: this.$t('Duration'), 
                    active: true 
                },
                { 
                    value: 'progress', 
                    label: this.$t('Progress'), 
                    active: true 
                },
                { 
                    value: 'result', 
                    label: this.$t('Result'), 
                    active: true 
                },
            ]
        }
    },
    created() {
        this.initColumns()
    },
    methods: {
        initColumns() {
            const localConfig = JSON.parse(localStorage.getItem('gant_conf'))
            if (localConfig?.selectedColumns) {
                this.activeColumns = localConfig.selectedColumns
            }
        },
        openModal() {
            this.modalVisible = true
        },
        closeModal() {
            this.modalVisible = false
        },
        saveColumns() {
            const localConfig = JSON.parse(localStorage.getItem('gant_conf'))
            localConfig.selectedColumns = this.activeColumns
            localStorage.setItem('gant_conf', JSON.stringify(localConfig))
            this.$emit('change', this.activeColumns)
        },
        setDefaultSettings() {
            this.activeColumns = [
                'start_date',
                'duration',
                'progress',
                'result',
            ]
        },
        submit() {
            this.saveColumns()
            this.closeModal()
        }
    },
}
</script>


