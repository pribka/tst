<template>
    <div>
        <div
            v-if="inputType === 'input' || inputType === 'bordered_input'"
            class="ant-input select-none cursor-pointer flex items-center justify-between organization_user_trigger"
            :class="[inputType === 'input' && 'ant-input-ghost', size !== 'default' && `ant-input-number-${sizeTypes}`, inputType === 'bordered_input' && 'px-2']"
            @click="openSelect">
            <div v-if="showIcon" class="mr-5">
                <i class="fi fi-rr-user" style="color: #505050;" />
            </div>
            <div v-if="value" class="flex items-center truncate">
                <div class="mr-2">
                    <a-avatar :size="20" icon="team" :key="value.id" :src="value.avatar ? value.avatar.path : null" />
                </div>
                <span class="truncate">{{ value.full_name }}</span>
            </div>
            <div v-else class="dummy_placeholder">
                {{ placeholder }}
            </div>
            <i class="fi fi-rr-angle-small-down mr-2" />
        </div>

        <DrawerTemplate
            v-model="visible"
            :width="windowWidth"
            :wrapClassName="drawerWrapClass"
            :title="$t('team.select_employee')"
            @close="visible = false">
            <div class="drawer_content">
                <a-input-search
                    v-if="showSearch"
                    class="mb-2 search_input"
                    :loading="searchLoading"
                    v-model="search"
                    ref="searchInput"
                    @input="onSearch"
                    :placeholder="$t('employee_full_name')" />

                <div class="drawer_list">
                    <div
                        v-for="work in workList"
                        :key="work.id"
                        :title="work.full_name"
                        :class="checkSelected(work)"
                        class="cursor-pointer project_item py-2 flex items-center truncate"
                        @click="selectWork(work)">
                        <template v-if="$scopedSlots.item">
                            <slot name="item" :work="work"></slot>
                        </template>
                        <template v-else>
                            <div>
                                <a-avatar :size="28" icon="team" :src="work.avatar ? work.avatar.path : null" />
                            </div>
                            <div class="ml-2 truncate">
                                {{ work.full_name }}
                            </div>
                        </template>
                    </div>

                    <div v-if="page === 1 && loading" class="flex justify-center mt-2">
                        <a-spin size="small" />
                    </div>

                    <infinite-loading
                        ref="userInfinite"
                        :identifier="infiniteId"
                        :force-use-infinite-wrapper="infiniteWrapperSelector"
                        @infinite="getWorkList"
                        v-bind:distance="10">
                        <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </div>
            </div>
            <template #footer>
                <a-button type="ui_ghost" size="large" block @click="visible = false">
                    {{ $t('close') }}
                </a-button>
            </template>
        </DrawerTemplate>
    </div>
</template>

<script>
import DrawerTemplate from '@/components/DrawerTemplate.vue'
import mixin from './mixins'

export default {
    components: {
        DrawerTemplate
    },
    mixins: [mixin],
    computed: {
        drawerWrapClass() {
            return `organization_user_mini_select_mobile_drawer_${this._uid}`
        },
        infiniteWrapperSelector() {
            return `.${this.drawerWrapClass} .drawer_body`
        }
    }
}
</script>

<style lang="scss" scoped>
.dummy_placeholder {
    color: #888888;
}

.organization_user_trigger,
.drawer_content,
.drawer_list {
    width: 100%;
}

.project_item {
    border-radius: 8px;
    margin-bottom: 3px;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);

    &:hover,
    &.active {
        background: #f7f9fc;
    }
}

.search_input {
    &::v-deep {
        .ant-input {
            background: #f7f9fc;
            border-color: #f7f9fc;
            box-shadow: initial !important;
            color: var(--text);
            min-height: 36px;

            &::placeholder {
                color: #888888;
            }

            .ant-input-suffix {
                color: var(--text);
            }
        }
    }
}
</style>
