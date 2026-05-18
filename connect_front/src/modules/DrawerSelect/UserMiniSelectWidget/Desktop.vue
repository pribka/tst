<template>
    <a-popover
        :placement="placement"
        :trigger="disabled ? 'none' : 'click'"
        v-model="visible"
        transitionName=""
        :disabled="disabled"
        :destroyTooltipOnHide="true"
        overlayClassName="user_mini_popover"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">
        <a-button v-if="inputType === 'button'" type="flat" class="sel_p_btn select-none" :title="value ? `${$t('table.user')}: ${value.full_name}` : $t('table.user')">
            <div v-if="value" class="flex items-center gap-2 truncate">
                {{ $t('table.user') }}:
                <div class="flex items-center truncate">
                    <div class="mr-2">
                        <a-avatar :size="20" icon="team" :key="value.id" :src="value.avatar ? value.avatar.path : null" />
                    </div>
                    <span class="truncate">{{value.full_name}}</span>
                </div>
                <i class="fi fi-rr-angle-small-down mr-2"/>
            </div>
            <div v-else class="flex items-center">
                <i class="fi fi-rr-folder mr-2" />
                {{ $t('table.user') }}
                <i class="fi fi-rr-angle-small-down mr-2" />
            </div>
        </a-button>
        <div
            v-if="inputType === 'input' || inputType === 'bordered_input'"
            class="ant-input select-none cursor-pointer flex items-center justify-between"
            :class="[inputType === 'input' && 'ant-input-ghost', size !== 'default' && `ant-input-number-${sizeTypes}`, inputType === 'bordered_input' && 'px-2']"
            :title="value ? `${$t('table.user')}: ${value.full_name}` : placeholder">
            <div v-if="showIcon" class="mr-5">
                <i class="fi fi-rr-user" style="color: #505050;" />
            </div>
            <div v-if="value" class="flex items-center truncate">
                <div class="mr-2">
                    <a-avatar :size="20" icon="team" :key="value.id" :src="value.avatar ? value.avatar.path : null" />
                </div>
                <span class="truncate">{{value.full_name}}</span>
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
            <div v-if="showRecent && recentList.length" class="pb-2 px-2 old_select">
                <div class="block_title">{{ $t('old_selected') }}</div>
                <div class="flex items-center gap-1">
                    <div
                        v-for="oldSelect in recentList"
                        :key="oldSelect.id"
                        :title="oldSelect.full_name"
                        class="cursor-pointer old_card"
                        :class="checkSelected(oldSelect)"
                        @click="selectWork(oldSelect)">
                        <div v-if="checkSelected(oldSelect) === 'active'" class="old_active">
                            <i class="fi fi-rr-check" />
                        </div>
                        <a-avatar :size="20" icon="team" :src="oldSelect.avatar ? oldSelect.avatar.path : null" />
                    </div>
                </div>
            </div>
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
.old_active{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    z-index: 10;
    color: #fff;
    background: rgba(0, 0, 0, 0.5);
}
.old_card{
    position: relative;
    overflow: hidden;
    border-radius: 50%;
    user-select: none;
}
.block_title{
    color: #888888;
    font-size: 12px;
    line-height: 12px;
    margin-bottom: 5px;
}
.popover_list{
    max-height: 160px;
    overflow-y: auto;
    max-width: 250px;
    min-width: 250px;
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
    max-width: 250px;
}
</style>

<style lang="scss">
.user_mini_popover{
    z-index: 999999;
    .ant-popover-arrow{
        display: none;
    }
    &.ant-popover-placement-bottom,
    &.ant-popover-placement-bottomLeft,
    &.ant-popover-placement-bottomRight{
        padding-top: 0px;
    }
    &.ant-popover-placement-top, &.ant-popover-placement-topLeft, &.ant-popover-placement-topRight{
        padding-bottom: 0px;
    }
}
</style>
