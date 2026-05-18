<template>
    <a-popover
        :placement="placement"
        :trigger="disabled ? 'none' : 'click'"
        v-model="visible"
        transitionName=""
        :disabled="disabled"
        :destroyTooltipOnHide="true"
        overlayClassName="contract_select_popover"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">
        <a-button v-if="inputType === 'button'" type="flat" class="sel_p_btn select-none" :title="valueTitle">
            <div v-if="currentValue" class="flex items-center gap-2 truncate">
                <div class="clamp_1">{{ getItemLabel(currentValue) }}</div>
                <div v-if="showClear" class="ml-1" @click.stop="clear()">
                    <i class="fi fi-rr-cross-small flex" />
                </div>
            </div>
            <div v-else class="flex items-center">
                <i v-if="showIcon" class="fi mr-2" :class="iconClass" />
                {{ placeholder }}
            </div>
        </a-button>
        <div
            v-else-if="inputType === 'input' || inputType === 'ghost' || inputType === 'bordered_input'"
            class="ant-input select-none cursor-pointer flex items-center justify-between"
            :class="[(inputType === 'input' || inputType === 'ghost') && 'ant-input-ghost', size !== 'default' && `ant-input-number-${sizeTypes}`, inputType === 'bordered_input' && 'px-2']"
            :title="valueTitle">
            <div v-if="showIcon" class="mr-5">
                <i class="fi" :class="iconClass" style="color: #505050;" />
            </div>
            <div v-if="currentValue" class="flex items-center contract_value_wrap">
                <span class="clamp_1">{{ getItemLabel(currentValue) }}</span>
            </div>
            <div v-else class="dummy_placeholder">
                {{ placeholder }}
            </div>
            <div class="flex items-center ml-2">
                <a-button
                    v-if="currentValue && showClear"
                    class="mr-1"
                    flaticon
                    size="small"
                    icon="fi-rr-cross-small"
                    shape="circle"
                    style="max-height: 20px;"
                    type="ui_ghost"
                    @click.stop="clear()" />
                <i v-if="showArrow" class="fi fi-rr-angle-small-down mr-2" />
            </div>
        </div>
        <div
            v-else-if="inputType === 'defaultInput'"
            class="popover_input ant-input flex items-center relative ant-input-lg truncate"
            :title="valueTitle">
            <a-tag
                v-if="currentValue"
                :title="getItemLabel(currentValue)"
                color="blue"
                class="tag_block truncate mr-2">
                {{ getItemLabel(currentValue) }}
            </a-tag>
            <a-button
                type="link"
                :icon="!currentValue && 'plus'"
                class="px-0 truncate">
                {{ currentValue ? $t('task.change') : $t('task.select') }}
            </a-button>
            <a-button
                v-if="currentValue && showClear"
                @click.stop="clear()"
                type="link"
                icon="close-circle"
                class="px-0 text-current remove_brn" />
        </div>

        <template #content>
            <a-input-search
                v-if="showSearch"
                class="mb-2 search_input"
                :loading="searchLoading"
                v-model="search"
                ref="searchInput"
                @input="onSearch"
                :placeholder="resolvedSearchPlaceholder" />
            <div v-if="showRecent && recentList.length" class="pb-2 px-2 old_select">
                <div class="block_title">{{ $t('old_selected') }}</div>
                <div class="old_select_list">
                    <div
                        v-for="oldSelect in recentList"
                        :key="getItemId(oldSelect)"
                        :title="getItemLabel(oldSelect)"
                        class="cursor-pointer old_list_item"
                        :class="checkSelected(oldSelect)"
                        @click="selectWork(oldSelect)">
                        <div class="clamp_4">
                            {{ getItemLabel(oldSelect) }}
                        </div>
                    </div>
                </div>
            </div>
            <div class="popover_list">
                <div
                    v-for="work in displayedWorkList"
                    :key="getItemId(work)"
                    :title="getItemLabel(work)"
                    :class="checkSelected(work)"
                    class="cursor-pointer project_item p-2 flex items-center"
                    @click="selectWork(work)">
                    <template v-if="$scopedSlots.item">
                        <slot name="item" :work="work"></slot>
                    </template>
                    <template v-else>
                        <div class="clamp_4">
                            {{ getItemLabel(work) }}
                        </div>
                    </template>
                </div>
                <div v-if="page === 1 && loading" class="flex justify-center">
                    <a-spin size="small" />
                </div>
                <div
                    v-else-if="!displayedWorkList.length"
                    class="empty_state">
                    {{ $t('chat.empty') }}
                </div>
                <infinite-loading :identifier="infiniteId" ref="userInfinite" @infinite="getWorkList" v-bind:distance="10">
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
.dummy_placeholder{
    color: #888888;
}
.contract_value_wrap{
    min-width: 0;
    flex: 1;
}
.clamp_1{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
}
.clamp_4{
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 4;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: normal;
    word-break: break-word;
    line-height: 1.35;
    max-width: 100%;
}
.block_title{
    color: #888888;
    font-size: 12px;
    line-height: 12px;
    margin-bottom: 5px;
}
.old_select_list{
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.old_list_item{
    padding: 6px 8px;
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover,
    &.active{
        background: #f7f9fc;
    }
}
.popover_list{
    max-height: 220px;
    overflow-y: auto;
    max-width: 320px;
    min-width: 320px;
    width: 320px;
}
.project_item{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    border-radius: 8px;
    margin-bottom: 3px;
    &:hover,
    &.active{
        background: #f7f9fc;
    }
}
.empty_state{
    padding: 16px 8px;
    text-align: center;
    color: #888888;
    line-height: 1.4;
}
.search_input{
    &::v-deep{
        .ant-input{
            background: #f7f9fc;
            border-color: #f7f9fc;
            box-shadow: initial!important;
            min-height: 36px;
            color: var(--text);
            &::placeholder{
                color: #888888;
            }
            .ant-input-suffix{
                color: var(--text);
            }
        }
    }
}
.sel_p_btn{
    max-width: 320px;
}
</style>

<style lang="scss">
.contract_select_popover{
    z-index: 999999;
    max-width: 352px;
    .ant-popover-arrow{
        display: none;
    }
    .ant-popover-inner-content{
        width: 352px;
        max-width: 352px;
        box-sizing: border-box;
    }
    &.ant-popover-placement-bottom,
    &.ant-popover-placement-bottomLeft,
    &.ant-popover-placement-bottomRight{
        padding-top: 0px;
    }
    &.ant-popover-placement-top,
    &.ant-popover-placement-topLeft,
    &.ant-popover-placement-topRight{
        padding-bottom: 0px;
    }
}
</style>
