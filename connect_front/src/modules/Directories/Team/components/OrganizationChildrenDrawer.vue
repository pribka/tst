<template>
    <div>
        <DrawerTemplate
            v-model="visible"
            :title="organizationTitle"
            :wrapClassName="drawerWrapClass"
            @close="visible = false">
            <div v-if="listEmpty" class="pt-4">
                <a-empty :description="$t('team.no_data')" />
            </div>

            <div
                v-for="child in list"
                :key="child.id"
                class="child_org_card"
                @click="openOrganization(child)">
                <div class="child_org_card__header">
                    <div class="child_org_card__name">{{ child.name || '-' }}</div>
                    <a-button
                        v-if="hasChildren(child)"
                        size="small"
                        type="ui_ghost"
                        class="child_org_card__expand"
                        @click.stop="openNestedDrawer(child)">
                        <i class="fi fi-rr-angle-small-right mr-1"></i>
                        <span v-if="getChildrenCount(child)">{{ getChildrenCount(child) }}</span>
                    </a-button>
                </div>

                <div class="child_org_card__row">
                    <div class="child_org_card__label">{{ $t('team.bin_iin') }}:</div>
                    <div class="child_org_card__value">{{ child.inn || '-' }}</div>
                </div>

                <div class="child_org_card__row">
                    <div class="child_org_card__label">{{ $t('team.director') }}:</div>
                    <div class="child_org_card__value">
                        <Profiler
                            v-if="child.director"
                            :user="child.director"
                            :showPopup="false"
                            :showTaskButton="false"
                            :showChatButton="false"
                            wrapperClass="block"
                            nameClass="truncate"
                            trigger="click" />
                        <span v-else>-</span>
                    </div>
                </div>

                <div class="child_org_card__row">
                    <div class="child_org_card__label">{{ $t('team.employees') }}:</div>
                    <div class="child_org_card__value">{{ child.members_count || 0 }}</div>
                </div>
            </div>

            <infinite-loading
                ref="infinityRef"
                :identifier="infiniteId"
                :force-use-infinite-wrapper="infiniteWrapperSelector"
                :distance="10"
                @infinite="getChildrenList">
                <div
                    slot="spinner"
                    class="flex items-center justify-center inf_spinner mt-3">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>

            <template #footer>
                <a-button
                    type="ui_ghost"
                    size="large"
                    block
                    @click="visible = false">
                    {{ $t('close') }}
                </a-button>
            </template>
        </DrawerTemplate>

        <OrganizationChildrenDrawer
            v-if="nestedOrganization"
            v-model="nestedVisible"
            :organization="nestedOrganization" />
    </div>
</template>

<script>
import DrawerTemplate from '@/components/DrawerTemplate.vue'

export default {
    name: 'OrganizationChildrenDrawer',
    components: {
        DrawerTemplate,
        InfiniteLoading: () => import('vue-infinite-loading'),
        Profiler: () => import('@/modules/Profiler/Profiler.vue')
    },
    props: {
        value: {
            type: Boolean,
            default: false
        },
        organization: {
            type: Object,
            default: () => null
        }
    },
    data() {
        return {
            loading: false,
            next: true,
            page: 0,
            pageSize: 15,
            list: [],
            listEmpty: false,
            infiniteId: 0,
            nestedVisible: false,
            nestedOrganization: null
        }
    },
    computed: {
        visible: {
            get() {
                return this.value
            },
            set(val) {
                this.$emit('input', val)
            }
        },
        organizationTitle() {
            return this.organization?.name || ''
        },
        drawerWrapClass() {
            return `org_children_drawer_${this._uid}`
        },
        infiniteWrapperSelector() {
            return `.${this.drawerWrapClass} .drawer_body`
        }
    },
    watch: {
        value(val) {
            if (val) {
                this.reload()
            }
        },
        organization: {
            deep: false,
            handler() {
                if (this.visible) {
                    this.reload()
                }
            }
        }
    },
    methods: {
        hasChildren(item) {
            return Boolean(item?.has_descendants) || this.getChildrenCount(item) > 0
        },
        getChildrenCount(item) {
            return Number(item?.structural_division_count || 0)
        },
        openNestedDrawer(item) {
            this.nestedOrganization = item
            this.nestedVisible = true
        },
        openOrganization(item) {
            const query = {
                organization_drawer: 'detail',
                organization_id: item.id
            }

            if (item?.parent_expand || this.organization?.id) {
                query.parent_id = item?.parent_expand || this.organization.id
            }

            this.$router.push({ query })
        },
        reload() {
            this.page = 0
            this.next = true
            this.list = []
            this.listEmpty = false
            this.infiniteId += 1
        },
        async getChildrenList($state) {
            if (!this.organization?.id || !this.next || this.loading) {
                $state.complete()
                return
            }

            try {
                this.loading = true
                this.page += 1

                const { data } = await this.$http.get('/users/my_organizations/', {
                    params: {
                        parent: this.organization.id,
                        page: this.page,
                        page_size: this.pageSize
                    }
                })

                const results = data?.results || []
                if (results.length) {
                    this.list = this.list.concat(results)
                }

                this.next = Boolean(data?.next)

                if (this.page === 1 && !results.length) {
                    this.listEmpty = true
                }

                if (this.next) {
                    $state.loaded()
                } else {
                    $state.complete()
                }
            } catch (error) {
                this.$message.error(this.$t('team.error'))
                $state.complete()
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.child_org_card {
    background: #fff;
    border: 1px solid var(--borderColor);
    border-radius: var(--borderRadius);
    padding: 10px;
    margin-bottom: 8px;
    user-select: none;

    &__header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 8px;
        margin-bottom: 8px;
    }

    &__name {
        font-weight: 600;
        line-height: 20px;
        word-break: break-word;
    }

    &__expand {
        flex-shrink: 0;
    }

    &__row {
        display: flex;
        align-items: center;
        gap: 6px;
        min-height: 22px;
        &:not(:last-child) {
            margin-bottom: 4px;
        }
    }

    &__label {
        color: var(--gray);
        flex-shrink: 0;
    }

    &__value {
        min-width: 0;
        word-break: break-word;
    }
}
</style>
