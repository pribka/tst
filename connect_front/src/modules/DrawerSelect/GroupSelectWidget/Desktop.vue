<template>
    <a-popover
        placement="topLeft"
        trigger="click"
        v-model="visible"
        transitionName=""
        :destroyTooltipOnHide="true"
        overlayClassName="project_popover"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">
        <a-button v-if="inputType === 'button'" type="flat" class="sel_p_btn" :title="value ? `${$t('wgr.team')}: ${value.name}` : $t('wgr.team')">
            <div v-if="value" class="flex items-center gap-2 truncate">
                {{ $t('wgr.team') }}:
                <div class="flex items-center truncate">
                    <div class="mr-2">
                        <a-avatar :size="20" icon="team" :key="value.id" :src="workgroupLogoPath(value)" />
                    </div>
                    <span class="truncate">{{value.name}}</span>
                </div>
                <div v-if="showClear" class="ml-1" @click.stop="clear()">
                    <i class="fi fi-rr-cross-small flex" />
                </div>
            </div>
            <div v-else class="flex items-center">
                <i class="fi fi-rr-users-alt mr-2" />
                {{ $t('wgr.team') }}
            </div>
        </a-button>
        <div v-if="inputType === 'input'" class="ant-input ant-input-ghost select-none cursor-pointer" :title="value ? `${$t('project_label')}: ${value.name}` : placeholder">
            <div v-if="value" class="flex items-center justify-between truncate">
                <div class="flex items-center truncate">
                    <div class="mr-2">
                        <a-avatar :size="20" icon="team" :key="value.id" :src="workgroupLogoPath(value)" />
                    </div>
                    <span class="truncate">{{value.name}}</span>
                </div>
                <a-button
                    v-if="showClear"
                    class="ml-2"
                    flaticon
                    size="small"
                    icon="fi-rr-cross-small"
                    shape="circle"
                    style="max-height: 20px;"
                    type="ui_ghost"
                    @click.stop="clear()" />
            </div>
            <div v-else class="dummy_placeholder">
                <span v-if="candidates?.length" class="blue_color">
                    Уточните какую команду вы имели в виду <i class="fi fi-rr-arrow-up-right ml-1" style="font-size: 10px;" />
                </span>
                <div v-else :class="useInputIcon && 'flex items-center'" class="justify-between">
                    <div :class="useInputIcon && 'flex items-center'">
                        <i v-if="useInputIcon" class="fi fi-rr-users-alt mr-2" />
                        {{ placeholder }}
                    </div>
                    <a-button
                        v-if="showArrow"
                        class="ml-2"
                        flaticon
                        size="small"
                        icon="fi-rr-angle-small-down"
                        shape="circle"
                        style="max-height: 20px;max-width: 20px;min-width: 20px;"
                        type="ui_ghost" />
                </div>
            </div>
        </div>
        <div
            v-else-if="inputType === 'defaultInput'"
            class="popover_input ant-input flex items-center relative ant-input-lg truncate"
            :title="value ? `${$t('project_label')}: ${value.name}` : placeholder">

            <a-tag
                v-if="value"
                :title="value.name"
                color="blue"
                class="tag_block truncate mr-2">
                <div class="flex items-center truncate">
                    <div class="mr-1">
                        <a-avatar :size="15" icon="team" :key="value.id" :src="workgroupLogoPath(value)" />
                    </div>
                    {{value.name}}
                </div>
            </a-tag>
            <a-button type="link" :icon="!value && 'plus'" class="px-0 truncate">
                {{value ? $t('task.change') : $t('task.select')}}
            </a-button>
            <a-button v-if="value" @click.stop="clear()" type="link" icon="close-circle" class="px-0 text-current remove_brn" />
        </div>
        <div
            v-else-if="inputType === 'avatar'"
            class="avatar_trigger"
            :title="value ? `${$t('wgr.team')}: ${value.name}` : $t('wgr.team')">
            <a-avatar v-if="value" :size="28" icon="team" :key="value.id" :src="workgroupLogoPath(value)" />
            <div v-else v-tippy :content="$t('select_group')" class="avatar_icon">
                <i class="fi fi-rr-users-alt" />
            </div>
        </div>


        <template #content>
            <a-input-search
                class="mb-2 search_input"
                :loading="searchLoading"
                v-model="search"
                ref="searchInput"
                @input="onSearch"
                :placeholder="$t('wgr.search')" />

            <div v-if="recentList.length" class="pb-2 px-2 old_select">
                <div class="block_title">{{ $t('old_selected') }}</div>
                <div class="flex items-center gap-1">
                    <div
                        v-for="oldItem in recentList"
                        :key="oldItem.id"
                        :title="oldItem.name"
                        class="cursor-pointer old_card"
                        :class="checkSelected(oldItem)"
                        @click="selectWork(oldItem)">
                        <div v-if="checkSelected(oldItem) === 'active'" class="old_active">
                            <i class="fi fi-rr-check" />
                        </div>
                        <a-avatar :size="20" icon="team" :src="workgroupLogoPath(oldItem)" />
                    </div>
                </div>
            </div>

            <div class="popover_list">
                <template v-if="candidates && candidates?.length">
                    <div class="block_title px-2 mt-1">Предлагаю</div>
                    <div
                        v-for="work in candidates"
                        :key="`${work.id}_candidates`"
                        :title="work.name"
                        :class="checkSelected(work)"
                        class="cursor-pointer project_item p-2 flex items-center truncate"
                        @click="selectWork(work)">
                        <div>
                            <a-avatar :size="20" icon="team" :src="workgroupLogoPath(work)" />
                        </div>
                        <div class="ml-2 truncate">{{work.name}}</div>
                    </div>
                    <div class="block_title px-2 mt-2 mb-1">Весь список</div>
                </template>
                <div
                    v-for="(work, index) in workList"
                    :key="index"
                    :title="work.name"
                    :class="checkSelected(work)"
                    class="cursor-pointer project_item p-2 flex items-center truncate"
                    @click="selectWork(work)">
                    <div>
                        <a-avatar :size="20" icon="team" :src="workgroupLogoPath(work)" />
                    </div>
                    <div class="ml-2 truncate">{{work.name}}</div>
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
            <div v-if="inputType === 'avatar' && value && showClear" class="pt-1 mb-1">
                <a-button type="ui_ghost" block size="small" @click="clearAndClose()">
                    {{ $t('task.reset') }}
                </a-button>
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
.old_card{
    position: relative;
    overflow: hidden;
    border-radius: 50%;
    user-select: none;
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
    background: rgba(0, 0, 0, 0.5)
}
.block_title{
    color: #888888;
    font-size: 12px;
    line-height: 12px;
    margin-bottom: 5px;
}
.old_select{
    &__label{
        color: #888888;
        font-size: 12px;
        line-height: 12px;
        margin-bottom: 5px
    }
}
.popover_list{
    max-height: 160px;
    overflow-y: auto;
    max-width: 250px;
    min-width: 250px
}
.project_item{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    border-radius: 8px;
    margin-bottom: 3px;
    &:hover,
    &.active{
        background: #f7f9fc
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
                color: #888888
            }
            .ant-input-suffix{
                color: var(--text)
            }
        }
    }
}
.sel_p_btn{
    max-width: 250px
}
.avatar_trigger{
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    .avatar_icon{
        width: 28px;
        height: 28px;
        border-radius: 50%;
        border: 1px solid var(--borderColor);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #888888;
        background: #fff;
    }
}
</style>

<style lang="scss">
.project_popover{
    .ant-popover-arrow{
        display: none
    }
    &.ant-popover-placement-bottom,
    &.ant-popover-placement-bottomLeft,
    &.ant-popover-placement-bottomRight{
        padding-top: 0px
    }
    &.ant-popover-placement-top, &.ant-popover-placement-topLeft, &.ant-popover-placement-topRight{
        padding-bottom: 0px;
    }
}
</style>
