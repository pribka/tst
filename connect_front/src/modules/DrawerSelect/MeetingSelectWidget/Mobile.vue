<template>
    <div>
        <!-- Trigger -->
        <div
            class="meeting_select_input ant-input ant-input-lg flex items-center cursor-pointer"
            :title="value ? value.string_view : placeholder"
            @click="openSelect">
            <span v-if="value" class="meeting_select_input__value truncate flex-1">{{ value.string_view || $t('calendar.meeting_attached') }}</span>
            <span v-else class="meeting_select_input__placeholder flex-1">{{ placeholder }}</span>
            <i
                v-if="value && showClear"
                class="fi fi-rr-cross-small meeting_select_input__clear flex-shrink-0"
                @click.stop="clear()" />
            <i v-else class="fi fi-rr-video-camera meeting_select_input__icon flex-shrink-0" />
        </div>

        <!-- Drawer -->
        <DrawerTemplate
            v-model="visible"
            :width="windowWidth"
            :wrapClassName="drawerWrapClass"
            :title="$t('calendar.select_meeting')"
            @close="visible = false">
            <div class="drawer_content">
                <a-input-search
                    class="mb-2 search_input"
                    :loading="searchLoading"
                    v-model="search"
                    ref="searchInput"
                    @input="onSearch"
                    :placeholder="$t('calendar.search_meeting_placeholder')" />

                <div class="drawer_list">
                    <div
                        v-for="item in meetingList"
                        :key="item.id"
                        :class="checkSelected(item)"
                        class="cursor-pointer meeting_item py-2 px-1 flex items-center"
                        @click="selectItem(item)">
                        <div class="truncate meeting_item__name flex-1">{{ item.string_view }}</div>
                        <i v-if="checkSelected(item) === 'active'" class="fi fi-rr-check ml-2 flex-shrink-0 check_icon" />
                    </div>

                    <div v-if="page === 1 && loading" class="flex justify-center mt-3">
                        <a-spin size="small" />
                    </div>

                    <div v-if="!loading && !meetingList.length" class="empty_text">
                        {{ $t('calendar.no_data') }}
                    </div>

                    <infinite-loading
                        ref="infiniteLoader"
                        :identifier="infiniteId"
                        :force-use-infinite-wrapper="infiniteWrapperSelector"
                        @infinite="getMeetingList"
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
    components: { DrawerTemplate },
    mixins: [mixin],
    computed: {
        drawerWrapClass() {
            return `meeting_select_mobile_drawer_${this._uid}`
        },
        infiniteWrapperSelector() {
            return `.${this.drawerWrapClass} .drawer_body`
        }
    }
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
.drawer_content {
    width: 100%;
}
.drawer_list {
    width: 100%;
}
.meeting_item {
    border-radius: 8px;
    margin-bottom: 3px;
    transition: background 0.2s;
    &:hover,
    &.active {
        background: #f7f9fc;
    }
    &__icon {
        color: #888888;
        font-size: 15px;
    }
    &__name {
        font-size: 14px;
    }
    &.active .meeting_item__name {
        color: var(--blue);
        font-weight: 500;
    }
}
.check_icon {
    color: var(--blue);
    font-size: 14px;
}
.empty_text {
    text-align: center;
    color: #888888;
    padding: 20px 0;
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
