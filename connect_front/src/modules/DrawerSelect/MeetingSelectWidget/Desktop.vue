<template>
    <a-popover
        placement="bottomLeft"
        trigger="click"
        v-model="visible"
        transitionName=""
        :destroyTooltipOnHide="true"
        overlayClassName="meeting_select_popover"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">

        <!-- Trigger: defaultInput -->
        <div
            class="meeting_select_input ant-input ant-input-lg flex items-center cursor-pointer"
            :title="value ? value.string_view : placeholder">
            <span v-if="value" class="meeting_select_input__value truncate flex-1">{{ value.string_view || $t('calendar.meeting_attached') }}</span>
            <span v-else class="meeting_select_input__placeholder flex-1">{{ placeholder }}</span>
            <i
                v-if="value && showClear"
                class="fi fi-rr-cross-small meeting_select_input__clear flex-shrink-0"
                @click.stop="clear()" />
            <i v-else class="fi fi-rr-video-camera meeting_select_input__icon flex-shrink-0" />
        </div>

        <template #content>
            <a-input-search
                class="mb-2 search_input"
                :loading="searchLoading"
                v-model="search"
                ref="searchInput"
                @input="onSearch"
                :placeholder="$t('calendar.search_meeting_placeholder')" />

            <div class="popover_list">
                <div
                    v-for="item in meetingList"
                    :key="item.id"
                    :class="checkSelected(item)"
                    class="cursor-pointer meeting_item p-2 flex items-center"
                    @click="selectItem(item)">
                    <div class="truncate meeting_item__name">{{ item.string_view }}</div>
                    <i v-if="checkSelected(item) === 'active'" class="fi fi-rr-check ml-auto flex-shrink-0 check_icon" />
                </div>

                <div v-if="page === 1 && loading" class="flex justify-center py-2">
                    <a-spin size="small" />
                </div>

                <div v-if="!loading && !meetingList.length" class="empty_text">
                    {{ $t('calendar.no_data') }}
                </div>

                <infinite-loading
                    :identifier="infiniteId"
                    ref="infiniteLoader"
                    @infinite="getMeetingList"
                    v-bind:distance="10">
                    <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                    <div slot="no-more"></div>
                    <div slot="no-results"></div>
                </infinite-loading>
            </div>

            <div class="pt-1">
                <a-button type="ui_ghost" block size="small" @click="visible = false">
                    {{ $t('close') }}
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
.meeting_select_input {
    min-height: 40px;
    height: auto;
    gap: 6px;
    &__value {
        overflow: hidden;
        text-overflow: ellipsis;
    }
    &__placeholder {
        color: #bfbfbf;
    }
    &__icon {
        color: #bfbfbf;
        font-size: 14px;
    }
    &__clear {
        color: #bfbfbf;
        font-size: 16px;
        transition: color 0.2s;
        &:hover {
            color: #ff4d4f;
        }
    }
}
.popover_list {
    max-height: 200px;
    overflow-y: auto;
    min-width: 260px;
    max-width: 320px;
}
.meeting_item {
    border-radius: 8px;
    margin-bottom: 2px;
    transition: background 0.2s;
    &:hover,
    &.active {
        background: #f7f9fc;
    }
    &__icon {
        color: #888888;
        font-size: 13px;
    }
    &__name {
        font-size: 13px;
    }
    &.active .meeting_item__name {
        color: var(--blue);
        font-weight: 500;
    }
}
.check_icon {
    color: var(--blue);
    font-size: 13px;
}
.empty_text {
    text-align: center;
    color: #888888;
    padding: 12px 0;
    font-size: 13px;
}
.search_input {
    &::v-deep {
        .ant-input {
            background: #f7f9fc;
            border-color: #f7f9fc;
            box-shadow: initial !important;
            min-height: 36px;
            color: var(--text);
            &::placeholder {
                color: #888888;
            }
        }
    }
}
</style>

<style lang="scss">
.meeting_select_popover {
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
