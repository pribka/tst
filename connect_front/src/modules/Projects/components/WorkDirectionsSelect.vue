<template>
    <div
        class="work_directions_select"
        :class="{
            'work_directions_select--ghost': inputType === 'ghost',
            'work_directions_select--default': inputType === 'default'
        }">
        <DSelect
            ref="selectRef"
            :key="`${organization || 'work-directions-empty'}_${selectKey}`"
            :value="value"
            apiUrl="/catalogs/work_directions/"
            class="w-full"
            multiple
            infinity
            disallowCustomValues
            showSearch
            :size="size"
            :inputType="inputType"
            :disabled="disabled || !organization"
            :initList="Boolean(organization)"
            :initOptionList="selectedDirections"
            :showAllHandler="organization ? showAllDirectionsHandler : false"
            :placeholder="$t('project.select_work_directions')"
            :params="selectParams"
            resultsKey="results"
            labelKey="name"
            valueKey="id"
            :listObject="false"
            :default-active-first-option="false"
            :filter-option="false"
            :not-found-content="null"
            @change="changeDirections"
            @changeGetObject="changeDirectionsObjects">
            <template #suffixSlot>
                <a-button
                    type="ui"
                    ghost
                    shape="circle"
                    size="small"
                    flaticon
                    v-tippy
                    :content="$t('project.add_work_direction')"
                    icon="fi-rr-add"
                    @click="openCreateDirection" />
            </template>
        </DSelect>

        <WorkDirectionsSelectModal
            ref="selectModalRef"
            :organization="organization"
            :selectedItems="selectedDirections"
            @select="selectDirectionsFromModal" />

        <WorkDirectionFormModal
            ref="createModalRef"
            model="catalogs.WorkDirectionModel"
            contractorSelect
            :contractor="organization"
            :eventsEnabled="false"
            :afterCreate="afterCreateDirection" />
    </div>
</template>

<script>
export default {
    components: {
        DSelect: () => import('@apps/DrawerSelect/Select.vue'),
        WorkDirectionsSelectModal: () => import('./WorkDirectionsSelectModal.vue'),
        WorkDirectionFormModal: () => import('@/modules/Directories/components/WorkDirectionFormModal.vue')
    },
    props: {
        value: {
            type: Array,
            default: () => []
        },
        organization: {
            type: String,
            default: ''
        },
        disabled: {
            type: Boolean,
            default: false
        },
        inputType: {
            type: String,
            default: 'ghost'
        },
        size: {
            type: String,
            default: 'default'
        }
    },
    data() {
        return {
            selectedDirections: [],
            syncRequestId: 0,
            selectKey: 0
        }
    },
    computed: {
        selectParams() {
            const params = {
                filters: {
                    is_archive: false
                }
            }
            if (this.organization) {
                params.contractor = this.organization
            }
            return params
        }
    },
    watch: {
        organization(newValue, oldValue) {
            if (newValue === oldValue) return
            const hasSelectedValue = Array.isArray(this.value) && this.value.length
            if (!oldValue && newValue && hasSelectedValue) {
                this.selectKey += 1
                this.$nextTick(() => {
                    this.$refs.selectRef?.listReload?.()
                })
                return
            }
            this.selectedDirections = []
            this.$emit('input', [])
            this.selectKey += 1
            this.$refs.selectRef?.listReload?.()
        },
        value: {
            immediate: true,
            handler(nextValue) {
                this.syncSelectedDirections(nextValue)
            }
        }
    },
    methods: {
        async fetchDirectionById(id) {
            const { data } = await this.$http.get(`/catalogs/work_directions/${id}/`)
            return data
        },
        async syncSelectedDirections(ids) {
            const requestId = ++this.syncRequestId
            if (!Array.isArray(ids) || !ids.length) {
                this.selectedDirections = []
                return
            }

            const existingMap = new Map(
                (this.selectedDirections || [])
                    .filter(item => item?.id)
                    .map(item => [item.id, item])
            )

            const resolved = await Promise.all(ids.map(async id => {
                const existing = existingMap.get(id)
                if (existing?.name) return existing
                try {
                    return await this.fetchDirectionById(id)
                } catch (error) {
                    return existing || { id, name: String(id) }
                }
            }))

            if (requestId !== this.syncRequestId) return
            this.selectedDirections = resolved.filter(Boolean)
        },
        async normalizeDirection(direction) {
            if (!direction?.id) return direction
            if (direction.name) return direction
            try {
                return await this.fetchDirectionById(direction.id)
            } catch (error) {
                return direction
            }
        },
        changeDirections(value) {
            this.$emit('input', value || [])
        },
        changeDirectionsObjects(items) {
            if (!Array.isArray(items)) return
            const map = new Map(this.selectedDirections.map(item => [item.id, item]))
            items.forEach(item => {
                if (item?.id) map.set(item.id, item)
            })
            this.selectedDirections = (this.value || [])
                .map(id => map.get(id))
                .filter(Boolean)
        },
        showAllDirectionsHandler() {
            this.$refs.selectModalRef?.open()
        },
        openCreateDirection() {
            this.$refs.createModalRef?.open()
        },
        selectDirectionsFromModal(items) {
            const ids = items.map(item => item.id)
            this.selectedDirections = items
            this.selectKey += 1
            this.$emit('input', ids)
        },
        async afterCreateDirection(direction, meta = {}) {
            const normalizedDirection = await this.normalizeDirection(direction)
            if (!normalizedDirection?.id) return
            const nextDirections = [...this.selectedDirections]
            const index = nextDirections.findIndex(item => item.id === normalizedDirection.id)
            if (index === -1) {
                if (!meta.edit) {
                    nextDirections.unshift(normalizedDirection)
                }
            } else {
                nextDirections.splice(index, 1, normalizedDirection)
            }
            this.selectedDirections = nextDirections
            const nextIds = meta.edit
                ? [...(this.value || [])]
                : Array.from(new Set([...(this.value || []), normalizedDirection.id]))
            this.selectKey += 1
            this.$emit('input', nextIds)
            this.$refs.selectRef?.unshiftItem?.(normalizedDirection)
            this.$refs.selectModalRef?.selectCreatedDirection?.(normalizedDirection, meta)
            this.$nextTick(() => {
                this.syncSelectedDirections(nextIds)
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.work_directions_select{
    width: 100%;
    display: flex;
    align-items: center;
    min-height: 30px;
    &--ghost::v-deep{
        .ant-select-selection--multiple{
            .ant-select-selection__rendered{
                margin-left: 0 !important;
                margin-right: 0 !important;
            }
            .ant-select-search--inline{
                margin-left: 0 !important;
            }
            .ant-select-selection__placeholder{
                left: 0 !important;
                margin-left: 0 !important;
            }
        }
    }
    &--default::v-deep{
        .ant-select-selection--multiple{
            .ant-select-selection__rendered{
                margin-left: 11px !important;
                margin-right: 32px !important;
            }
            .ant-select-search--inline{
                margin-left: 0 !important;
            }
            .ant-select-selection__placeholder{
                left: 11px !important;
                margin-left: 0 !important;
            }
        }
    }
}
</style>
