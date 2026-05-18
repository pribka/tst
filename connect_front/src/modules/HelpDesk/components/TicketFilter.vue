<template>
    <Segmented 
        v-model="activeStatus" 
        :options="statusList"
        multiselect
        deselectable
        @change="changeFilter" />
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
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
        }
    },
    components: {
        Segmented: () => import('@apps/UIModules/Segmented')
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        })
    },
    data() {
        return {
            activeStatus: [],
            statusList: [
                {
                    key: 'specialist',
                    title: this.$t('helpdesk.doing'),
                    single: true,
                    count: 0
                },
                {
                    key: 'author',
                    title: this.$t('helpdesk.assigned'),
                    single: true,
                    count: 0
                },
                {
                    key: 'visors',
                    title: this.$t('helpdesk.watching'),
                    single: true,
                    count: 0
                },
                {
                    key: 'is_overdue',
                    title: this.$t('helpdesk.overdue'),
                    count: 0,
                    color: 'danger'
                }
            ]
        }
    },
    created() {
        this.getCount()
        this.getFilters()
    },
    methods: {
        changeFilter() {
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
                author: 'author',
                specialist: 'specialist',
                visors: 'visors_filter',
                is_overdue: 'is_overdue_filter'
            }

            Object.entries(filterConfig).forEach(([key, backendKey]) => {
                const isActive = this.activeStatus.includes(key)

                if (key === 'is_overdue') {
                    filters.fields[backendKey] = {
                        active: isActive,
                        values: { value: isActive }
                    }
                    filters.filterTags.structure[backendKey] = isActive ? this.$t('Yes') : ''
                } else {
                    filters.fields[backendKey] = {
                        active: isActive,
                        values: {
                            value: isActive ? [this.user.id] : []
                        }
                    }
                    filters.filterTags.structure[backendKey] = isActive ? [userObject] : []
                }
            })

            clearTimeout(timer)
            timer = setTimeout(() => {
                eventBus.$emit(`send_include_fields_${this.page_name}`, filters)
            }, 900)
        },
        async getCount() {
            try {
                const { data } = await this.$http.get('/help_desk/tickets/my_tickets_count/', {
                    params: {
                        page_name: this.page_name
                    }
                })
                if (data) {
                    this.statusList = this.statusList.map(item => ({
                        ...item,
                        count: item.key in data ? data[item.key] : 0
                    }))
                }
            } catch(e) {
                console.log(e)
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
                    this.handleFilterActive(data.activeFilters)
                }
            } catch(e) {
                console.log(e)
            }
        },
        handleFilterActive(data) {
            const reverseMap = {
                is_overdue_filter: 'is_overdue',
                visors_filter: 'visors',
                specialist: 'specialist',
                author: 'author'
            }

            const active = []

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
                    if (shortKey) active.push(shortKey)
                }
            })

            this.activeStatus = active
        }
    },
    mounted() {
        eventBus.$on('UPDATE_LIST', () => {
            this.getCount()
        })
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.getCount()
        })
        eventBus.$on(`update_filter_data_${this.page_name}`, ({ fields }) => {
            const reverseMap = {
                is_overdue_filter: 'is_overdue',
                visors_filter: 'visors',
                specialist: 'specialist',
                author: 'author'
            }

            const active = []

            Object.entries(fields).forEach(([key, val]) => {
                if (key.includes('_exclude')) return

                const shortKey = reverseMap[key]
                if (!shortKey || !val || typeof val !== 'object') return

                const isActive = val.active === true
                const value = val.values?.value

                if (shortKey === 'is_overdue') {
                    if (isActive && value === true) {
                        active.push(shortKey)
                    }
                } else {
                    if (
                        isActive &&
                Array.isArray(value) &&
                value.includes(this.user.id)
                    ) {
                        active.push(shortKey)
                    }
                }
            })

            this.activeStatus = active
        })
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_data_${this.page_name}`)
        eventBus.$off('UPDATE_LIST')
        eventBus.$off(`update_filter_${this.model}`)
    }
}
</script>