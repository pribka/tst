<template>
    <Segmented 
        v-model="activeStatus" 
        :options="statusList"
        multiselect
        deselectable
        :bgInvert="bgInvert"
        @change="changeFilter" />
</template>

<script>
import eventBus from '@/utils/eventBus'
import Axios from 'axios'
import { mapState } from 'vuex'
import { errorHandler } from '@/utils/index.js'
let timer;
export default {
    props: {
        page_name: {
            type: String,
            required: true
        },
        model: {
            type: String,
            required: true
        },
        bgInvert: {
            type: Boolean,
            default: false
        },
        showCount: {
            type: Boolean,
            default: true
        },
        queryParams: {
            type: Object,
            default: () => {}
        }
    },
    components: {
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            completeStatus: state => state.task.completeStatus,
            filterActiveState: state => state.filter.filterActive,
            filterSelectedState: state => state.filter.filterSelected
        })
    },
    data() {
        return {
            activeStatus: [],
            countCancelSource: null,
            statusList: [
                {
                    key: 'is_executor_filter',
                    title: this.$t('task.im_operator'),
                    single: true,
                    count: 0
                },
                {
                    key: 'owner',
                    title: this.$t('task.im_owner'),
                    single: true,
                    count: 0
                },
                {
                    key: 'visor',
                    title: this.$t('task.im_visor'),
                    single: true,
                    count: 0
                },
                {
                    key: 'is_participant_filter',
                    title: this.$t('task.participant'),
                    single: true,
                    count: 0
                },
                {
                    key: 'overdue',
                    title: this.$t('task.overdue'),
                    count: 0,
                    color: 'danger'
                }
            ]
        }
    },
    created() {
        if(this.showCount)
            this.getCount()
        this.getFilters()
    },
    methods: {
        cancelCountRequest() {
            if (this.countCancelSource) {
                this.countCancelSource.cancel('Canceled stale my_tasks_count request')
                this.countCancelSource = null
            }
        },
        getCurrentFieldState(fieldName) {
            return {
                active: this.filterActiveState?.[this.page_name]?.[fieldName] === true,
                value: this.filterSelectedState?.[this.page_name]?.[fieldName]
            }
        },
        shouldResetUserRoleFilter(fieldName) {
            const { active, value } = this.getCurrentFieldState(fieldName)
            return active && Array.isArray(value) && value.length === 1 && String(value[0]) === String(this.user.id)
        },
        shouldResetStatusExclude(completeCodes) {
            const { active, value } = this.getCurrentFieldState('status__exclude')
            if (!active || !Array.isArray(value) || !completeCodes.length || value.length !== completeCodes.length) {
                return false
            }

            const currentCodes = value.map(item => {
                if (typeof item === 'string') return item
                if (item && typeof item === 'object') return item.code || item.value || item.id || ''
                return ''
            }).filter(Boolean)

            return currentCodes.length === completeCodes.length
                && currentCodes.every(code => completeCodes.includes(code))
        },
        async changeFilter() {
            try {
                const userObject = {
                    id: this.user.id,
                    avatar: this.user.avatar,
                    full_name: `${this.user.last_name} ${this.user.first_name} ${this.user.middle_name}`,
                    first_name: this.user.first_name,
                    last_name: this.user.last_name,
                    middle_name: this.user.middle_name
                }

                const filters = {
                    fields: {},
                    filterTags: { structure: {} }
                }

                const filterConfig = {
                    owner: 'owner',
                    is_executor_filter: 'is_executor_filter',
                    visor: 'is_visor_filter',
                    is_participant_filter: 'is_participant_filter',
                    overdue: 'is_overdue_filter'
                }

                Object.entries(filterConfig).forEach(([key, backendKey]) => {
                    const isActive = this.activeStatus.includes(key)

                    if (key === 'overdue') {
                        const currentField = this.getCurrentFieldState(backendKey)
                        if (!isActive && !currentField.active) return

                        filters.fields[backendKey] = {
                            active: isActive,
                            values: { value: isActive }
                        }
                        filters.filterTags.structure[backendKey] = isActive ? this.$t('task.yes') : ''
                    } else {
                        if (!isActive && !this.shouldResetUserRoleFilter(backendKey)) return

                        filters.fields[backendKey] = {
                            active: isActive,
                            values: { value: isActive ? [this.user.id] : [] }
                        }
                        filters.filterTags.structure[backendKey] = isActive ? [userObject] : []
                    }
                })

                const roleKeys = ['owner', 'is_executor_filter', 'visor', 'is_participant_filter']
                const anyRoleActive = roleKeys.some(k => this.activeStatus.includes(k))

                if (anyRoleActive) {
                    await this.$store.dispatch('task/getCompleteStatus')
                    const codes = Array.isArray(this.completeStatus) ? this.completeStatus.map(s => s.code) : []
                    filters.fields['status__exclude'] = {
                        active: true,
                        values: { value: codes }
                    }
                    const tagStructure = Array.isArray(this.completeStatus)
                        ? this.completeStatus.map(s => ({
                            id: s.id,
                            code: s.code,
                            string_view: s.string_view || s.name || '',
                            name: s.string_view || s.name || '',
                            value: s.id
                        }))
                        : []
                    filters.filterTags.structure['status__exclude'] = tagStructure
                } else {
                    await this.$store.dispatch('task/getCompleteStatus')
                    const codes = Array.isArray(this.completeStatus) ? this.completeStatus.map(s => s.code) : []
                    if (this.shouldResetStatusExclude(codes)) {
                        filters.fields['status__exclude'] = {
                            active: false,
                            values: { value: [] }
                        }
                        filters.filterTags.structure['status__exclude'] = []
                    }
                }

                clearTimeout(timer)
                timer = setTimeout(() => {
                    eventBus.$emit(`send_include_fields_${this.page_name}`, filters)
                }, 900)
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async getCount() {
            let cancelSource = null
            try {
                this.cancelCountRequest()
                const params = {
                    page_name: this.page_name,
                    ...(this.queryParams && Object.keys(this.queryParams).length ? this.queryParams : {})
                }
                cancelSource = Axios.CancelToken.source()
                this.countCancelSource = cancelSource
                const { data } = await this.$http.get('/tasks/task/my_tasks_count/', {
                    params,
                    cancelToken: cancelSource.token
                })

                const backendKeyMap = {
                    is_executor_filter: 'im_operator',
                    owner: 'im_owner',
                    visor: 'im_visor',
                    is_participant_filter: 'im_participant',
                    overdue: 'overdue'
                }

                if (data) {
                    this.statusList = this.statusList.map(item => {
                        const backendKey = backendKeyMap[item.key]
                        return {
                            ...item,
                            count: backendKey in data ? data[backendKey] : 0
                        }
                    })
                }
            } catch (error) {
                if (!Axios.isCancel(error)) {
                    errorHandler({error, show: false})
                }
            } finally {
                if (this.countCancelSource === cancelSource) {
                    this.countCancelSource = null
                }
            }
        },
        async getFilters() {
            try {
                const { data } = await this.$http.get('/app_info/active_filters/', {
                    params: {
                        model: this.model,
                        page_name: this.page_name
                    }
                })
                if(data) {
                    this.applyActiveFilters(data.activeFilters)
                }
            } catch(error) {
                errorHandler({error, show: false})
            }
        },
        async applyActiveFilters(data) {
            const reverseMap = {
                is_overdue_filter: 'overdue',
                is_visor_filter: 'visor',
                is_participant_filter: 'is_participant_filter',
                is_executor_filter: 'is_executor_filter',
                owner: 'owner'
            }

            const roleKeys = ['owner', 'is_executor_filter', 'visor', 'is_participant_filter']
            const active = []
            const candidateRoles = []

            Object.entries(data).forEach(([key, val]) => {
                if (key.includes('_exclude')) return
                if (!val || typeof val !== 'object') return

                const shortKey = reverseMap[key]
                if (!shortKey) return

                const isActive = val.active === true
                const value = val.values?.value

                if (shortKey === 'overdue') {
                    if (isActive && value === true) active.push(shortKey)
                    return
                }

                if (Array.isArray(value) && value.includes(this.user.id)) {
                    if (roleKeys.includes(shortKey)) {
                        candidateRoles.push(shortKey)
                    } else {
                        active.push(shortKey)
                    }
                }
            })

            const statusExcludeRaw = data['status__exclude']?.values?.value
            const statusExcludeValues = Array.isArray(statusExcludeRaw)
                ? statusExcludeRaw.map(v => {
                    if (typeof v === 'string') return v
                    if (v && typeof v === 'object') return v.code || v.value || v.id || ''
                    return ''
                }).filter(Boolean)
                : []

            if (candidateRoles.length > 0 && statusExcludeValues.length > 0) {
                await this.$store.dispatch('task/getCompleteStatus')
                const completeCodes = Array.isArray(this.completeStatus) ? this.completeStatus.map(s => s.code) : []
                const intersect = statusExcludeValues.filter(v => completeCodes.includes(v))
                if (intersect.length > 0) active.push(...candidateRoles)
            }

            this.activeStatus = active
        },
        async handleFilterActive(data) {
            const reverseMap = {
                is_overdue_filter: 'overdue',
                is_visor_filter: 'visor',
                is_participant_filter: 'is_participant_filter',
                is_executor_filter: 'is_executor_filter',
                owner: 'owner'
            }

            const roleKeys = ['owner', 'is_executor_filter', 'visor', 'is_participant_filter']
            const active = []
            const candidateRoles = []

            Object.entries(data).forEach(([key, val]) => {
                if (key.includes('_exclude')) return
                if (!val || typeof val !== 'object') return

                const isActive = val.active === true
                const value = val.values?.value

                const hasValidValue = (
                    typeof value === 'boolean' && value === true
                ) || (
                    Array.isArray(value) && value.length > 0
                )

                if (isActive && hasValidValue) {
                    const shortKey = reverseMap[key]
                    if (!shortKey) return
                    if (roleKeys.includes(shortKey)) {
                        candidateRoles.push(shortKey)
                    } else {
                        active.push(shortKey)
                    }
                }
            })

            const statusExcludeRaw = data['status__exclude']?.values?.value
            const statusExcludeValues = Array.isArray(statusExcludeRaw)
                ? statusExcludeRaw.map(v => {
                    if (typeof v === 'string') return v
                    if (v && typeof v === 'object') return v.code || v.value || v.id || ''
                    return ''
                }).filter(Boolean)
                : []

            if (candidateRoles.length > 0 && statusExcludeValues.length > 0) {
                await this.$store.dispatch('task/getCompleteStatus')
                const completeCodes = Array.isArray(this.completeStatus) ? this.completeStatus.map(s => s.code) : []
                const intersect = statusExcludeValues.filter(v => completeCodes.includes(v))
                if (intersect.length > 0) {
                    active.push(...candidateRoles)
                }
            }

            this.activeStatus = active
        }
    },
    mounted() {
        eventBus.$on('UPDATE_LIST', () => {
            if(this.showCount)
                this.getCount()
        })
        eventBus.$on(`update_filter_${this.model}`, () => {
            if(this.showCount)
                this.getCount()
        })
        eventBus.$on(`update_filter_${this.page_name}`, () => {
            if(this.showCount)
                this.getCount()
        })
        eventBus.$on(`update_filter_data_${this.page_name}`, ({ fields }) => {
            this.applyActiveFilters(fields)
        })
    },
    beforeDestroy() {
        this.cancelCountRequest()
        eventBus.$off(`update_filter_data_${this.page_name}`)
        eventBus.$off('UPDATE_LIST')
        eventBus.$off(`update_filter_${this.model}`)
        eventBus.$off(`update_filter_${this.page_name}`)
    }
}
</script>
