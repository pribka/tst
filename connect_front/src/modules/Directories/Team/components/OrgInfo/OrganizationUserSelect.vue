<template>
    <a-select
        class="organization_user_select"
        show-search
        allowClear
        :value="selectedValue"
        :placeholder="placeholder"
        :filterOption="false"
        :notFoundContent="fetching ? undefined : null"
        :disabled="disabled"
        :getPopupContainer="popupContainer"
        @search="onSearch"
        @change="onChange"
        @dropdownVisibleChange="onDropdownVisibleChange">
        <template v-if="fetching">
            <a-spin
                slot="notFoundContent"
                size="small" />
        </template>
        <a-select-option
            v-for="user in options"
            :key="user.id"
            :value="user.id">
            <div class="user_option">
                <div class="user_option__name">{{ user.full_name || `${user.last_name || ''} ${user.first_name || ''}`.trim() }}</div>
                <div
                    v-if="user.email"
                    class="user_option__email">
                    {{ user.email }}
                </div>
            </div>
        </a-select-option>
    </a-select>
</template>

<script>
import debounce from '@/utils/lodash/debounce'

export default {
    props: {
        value: {
            type: Object,
            default: null
        },
        organizationId: {
            type: String,
            required: true
        },
        excludedUserIds: {
            type: Array,
            default: () => []
        },
        placeholder: {
            type: String,
            default: ''
        },
        disabled: {
            type: Boolean,
            default: false
        },
        getPopupContainer: {
            type: Function,
            default: null
        }
    },
    data() {
        return {
            options: [],
            fetching: false
        }
    },
    computed: {
        selectedValue() {
            return this.value?.id || undefined
        }
    },
    watch: {
        value: {
            immediate: true,
            handler(value) {
                if (value?.id) {
                    this.addOption(value)
                }
            }
        }
    },
    created() {
        this.debouncedSearch = debounce(this.fetchUsers, 300)
    },
    methods: {
        popupContainer(trigger) {
            if (this.getPopupContainer) {
                return this.getPopupContainer(trigger)
            }

            return trigger.parentNode
        },
        addOption(user) {
            if (!user?.id) return

            const exists = this.options.some(item => item.id === user.id)
            if (!exists) {
                this.options = [user, ...this.options]
            }
        },
        async fetchUsers(search = '') {
            if (!this.organizationId) return

            try {
                this.fetching = true
                const { data } = await this.$http.get(`/users/my_organizations/${this.organizationId}/users/`, {
                    params: {
                        page: 1,
                        page_size: 20,
                        page_name: 'fire_employee_select',
                        text: search
                    }
                })

                const excludedIds = new Set(this.excludedUserIds)
                const results = (data?.results || []).filter(user => !excludedIds.has(user.id))

                this.options = results
                this.addOption(this.value)
            } catch (error) {
                console.error(error)
            } finally {
                this.fetching = false
            }
        },
        onDropdownVisibleChange(open) {
            if (open && !this.options.length) {
                this.fetchUsers()
            }
        },
        onSearch(value) {
            this.debouncedSearch(value)
        },
        onChange(userId) {
            if (!userId) {
                this.$emit('input', null)
                return
            }

            const selectedUser = this.options.find(item => item.id === userId) || null
            this.$emit('input', selectedUser)
        }
    }
}
</script>

<style lang="scss" scoped>
.organization_user_select {
    width: 100%;
}

.user_option {
    line-height: 1.35;

    &__name {
        color: var(--text);
    }

    &__email {
        color: var(--gray);
        font-size: 12px;
    }
}
</style>
