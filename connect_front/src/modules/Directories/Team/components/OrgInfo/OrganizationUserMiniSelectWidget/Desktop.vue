<template>
    <a-popover
        :placement="placement"
        :trigger="disabled ? 'none' : 'click'"
        v-model="visible"
        transitionName=""
        :disabled="disabled"
        :destroyTooltipOnHide="true"
        overlayClassName="user_mini_popover"
        :getPopupContainer="popupContainer"
        @visibleChange="visibleChange">
        <div
            v-if="inputType === 'input' || inputType === 'bordered_input'"
            class="ant-input select-none cursor-pointer flex items-center justify-between organization_user_trigger"
            :class="[inputType === 'input' && 'ant-input-ghost', size !== 'default' && `ant-input-number-${sizeTypes}`, inputType === 'bordered_input' && 'px-2']">
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
        <template #content>
            <a-input-search
                v-if="showSearch"
                class="mb-2 search_input"
                :loading="searchLoading"
                v-model="search"
                ref="searchInput"
                @input="onSearch"
                :placeholder="$t('employee_full_name')" />
            <div class="popover_list">
                <div
                    v-for="work in workList"
                    :key="work.id"
                    :title="work.full_name"
                    :class="checkSelected(work)"
                    class="cursor-pointer project_item p-2 flex items-center truncate"
                    @click="selectWork(work)">
                    <template v-if="$scopedSlots.item">
                        <slot name="item" :work="work"></slot>
                    </template>
                    <template v-else>
                        <div>
                            <a-avatar :size="20" icon="team" :src="work.avatar ? work.avatar.path : null" />
                        </div>
                        <div class="ml-2 truncate">
                            {{ work.full_name }}
                        </div>
                    </template>
                </div>
                <div v-if="page === 1 && loading" class="flex justify-center">
                    <a-spin size="small" />
                </div>
                <infinite-loading
                    :identifier="infiniteId"
                    ref="userInfinite"
                    @infinite="getWorkList"
                    v-bind:distance="10">
                    <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>
            <div class="pt-1">
                <a-button type="ui_ghost" block size="small" @click="visible = false">
                    {{ $t('Close') }}
                </a-button>
            </div>
        </template>
    </a-popover>
</template>

<script>
import mixin from './mixins'

export default {
    mixins: [mixin]
}
</script>

<style lang="scss" scoped>
.dummy_placeholder {
    color: #888888;
}

.organization_user_trigger {
    width: 100%;
}

.popover_list {
    max-height: 240px;
    max-width: 100%;
    min-width: 420px;
    overflow-y: auto;
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

<style lang="scss">
.user_mini_popover {
    z-index: 999999;

    .ant-popover-arrow {
        display: none;
    }

    &.ant-popover-placement-bottom,
    &.ant-popover-placement-bottomLeft,
    &.ant-popover-placement-bottomRight {
        padding-top: 0;
    }

    &.ant-popover-placement-top,
    &.ant-popover-placement-topLeft,
    &.ant-popover-placement-topRight {
        padding-bottom: 0;
    }
}
</style>
