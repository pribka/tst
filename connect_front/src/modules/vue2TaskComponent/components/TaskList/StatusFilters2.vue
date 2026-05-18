<template>
    <a-spin 
        :spinning="loading" 
        size="small">
        <div class="flex items-center mb-2 filters_block">
            <a-button 
                v-for="({ key, label }) in filterButtons" 
                :key="key"
                :type="filters[key] ? 'primary' : 'ui'" 
                @click="changeFilter(key)">
                <div class="flex items-center">
                    {{ $t(label) }}
                    <a-badge 
                        v-if="filtersCount[key]"
                        class="ml-2" 
                        :count="filtersCount[key]"
                        :overflow-count="9999"
                        :number-style="numberStyle(key)" />
                </div>
            </a-button>
        </div>
    </a-spin>
</template>

<script>
import eventBus from "@/utils/eventBus"
import Axios from 'axios'
import { mapState } from 'vuex'
let timer;
export default {
    props: {
        page_name: {
            type: String,
            default: ''
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            filterActiveState: state => state.filter.filterActive,
            filterSelectedState: state => state.filter.filterSelected
        }),
        filterButtons() {
            return [
                { key: "operator", label: "task.im_operator" },
                { key: "owner", label: "task.im_owner" },
                { key: "visor", label: "task.im_visor" },
                { key: "overdue", label: "task.overdue" }
            ]
        }
    },
    data() {
        return {
            loading: false,
            countCancelSource: null,
            filters: {
                owner: false,
                operator: false,
                visor: false,
                overdue: false
            },
            filtersCount: {
                owner: 0,
                operator: 0,
                visor: 0,
                overdue: 0
            }
        }
    },
    created() {
        this.getFilterCount()
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
        async getFilterCount() {
            let cancelSource = null
            try {
                this.cancelCountRequest()
                this.loading = true
                cancelSource = Axios.CancelToken.source()
                this.countCancelSource = cancelSource
                const { data } = await this.$http.get('/tasks/task/my_tasks_count/', {
                    params: {
                        task_type: 'task,stage',
                        page_name: this.page_name
                    },
                    cancelToken: cancelSource.token
                })
                if(data) {
                    this.filtersCount = {
                        owner: data.im_owner,
                        operator: data.im_operator,
                        visor: data.im_visor,
                        overdue: data.overdue
                    }
                }
            } catch(e) {
                if (!Axios.isCancel(e)) {
                    console.log(e)
                }
            } finally {
                if (this.countCancelSource === cancelSource) {
                    this.countCancelSource = null
                }
                this.loading = false
            }
        },
        changeFilter(type) {
            this.filters[type] = !this.filters[type]

            // Превращаем в радио-кнопки
            if (type !== 'overdue') {
                Object.keys(this.filters).forEach(key => {
                    if (key !== type && key !== 'overdue') this.$set(this.filters, key, false)
                })
            }

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
                owner: "owner",
                operator: "operator",
                visor: "is_visor_filter",
                overdue: "is_overdue_filter"
            }

            Object.entries(filterConfig).forEach(([key, field]) => {
                const isActive = this.filters[key]

                if (key === "overdue") {
                    const currentField = this.getCurrentFieldState(field)
                    if (!isActive && !currentField.active) return
                } else if (!isActive && !this.shouldResetUserRoleFilter(field)) {
                    return
                }

                filters.fields[field] = {
                    active: isActive,
                    values: { value: isActive ? (key === "overdue" ? true : [this.user.id]) : [] }
                }

                filters.filterTags.structure[field] = isActive ? (key === "overdue" ? 'Да' : [userObject]) : []
            })

            clearTimeout(timer)
            timer = setTimeout(() => {
                eventBus.$emit(`send_include_fields_${this.page_name}`, filters)
            }, 900)
        },
        numberStyle(type) {
            return {
                backgroundColor: this.filters[type] ? "#fff" :"var(--blue)",
                color: this.filters[type] ? "#000" : "#fff"
            }
        }
    },
    mounted() {
        eventBus.$on(`filter_active_${this.page_name}`, data => {
            const filtersMap = {
                operator: this.user.id,
                owner: this.user.id,
                is_visor_filter: this.user.id,
                is_overdue_filter: true
            }
            Object.entries(filtersMap).forEach(([key, targetValue]) => {
                const field = data[key]
                if (!field?.active || !field.values?.value) return
                if (key === 'is_overdue_filter')
                    this.filters.overdue = Array.isArray(field.values.value) ? false : field.values.value || false
                else
                    this.filters[key === "is_visor_filter" ? "visor" : key] = field.values.value.includes(targetValue)
            })

        })
        eventBus.$on('UPDATE_LIST', () => {
            this.getFilterCount()
        })
        eventBus.$on(`update_filter_tasks.TaskModel`, () => {
            this.getFilterCount()
        })
        eventBus.$on(`update_filter_data_${this.page_name}`, ({ fields }) => {
            const checkFilter = (fieldName, targetValue) => {
                const field = fields[fieldName]
                if (!field?.active || !field.values?.value) return false
                return fieldName === 'is_overdue_filter'
                    ? !Array.isArray(field.values.value) && field.values.value
                    : field.values.value.includes(targetValue)
            }
            Object.assign(this.filters, {
                operator: checkFilter("operator", this.user.id),
                owner: checkFilter("owner", this.user.id),
                visor: checkFilter("is_visor_filter", this.user.id),
                overdue: checkFilter("is_overdue_filter", true)
            })
        })
    },
    beforeDestroy() {
        this.cancelCountRequest()
        eventBus.$off(`filter_active_${this.page_name}`)
        eventBus.$off(`update_filter_data_${this.page_name}`)
        eventBus.$off('UPDATE_LIST')
        eventBus.$off('update_filter_tasks.TaskModel')
    }
}
</script>

<style lang="scss" scoped>
.filters_block{
    &::v-deep{
        .ant-badge-count{
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        }
        .ant-btn{
            &:not(:last-child){
                margin-right: 5px;
            }
            .ant-badge-count{
                box-shadow: initial;
            }
        }
    }
}
</style>
