<template>
    <div>
        <a-button v-if="inputType === 'button'" type="flat" class="sel_p_btn" :title="value ? value.name : placeholder" @click="openSelect">
            <div v-if="value" class="flex items-center gap-2 truncate">
                <span class="truncate"><template v-if="value.number">#{{ value.number }} </template>{{ value.name }}</span>
                <div v-if="showClear" class="ml-1" @click.stop="clear()">
                    <i class="fi fi-rr-cross-small flex" />
                </div>
            </div>
            <div v-else class="flex items-center">
                {{ placeholder }}
            </div>
        </a-button>

        <div v-if="inputType === 'input'" class="ant-input ant-input-ghost select-none cursor-pointer" :title="value ? value.name : placeholder" @click="openSelect">
            <div v-if="value" class="flex items-center justify-between truncate">
                <span class="truncate"><template v-if="value.number">#{{ value.number }} </template>{{ value.name }}</span>
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
                <div class="flex items-center justify-between">
                    <div>
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
            :title="value ? `${$t('project_label')}: ${value.name}` : placeholder"
            @click="openSelect">
            <a-tag
                v-if="value"
                :title="value.name"
                color="blue"
                class="tag_block truncate mr-2">
                <div class="flex items-center truncate">
                    <template v-if="value.number">#{{ value.number }} </template>{{value.name}}
                </div>
            </a-tag>

            <a-button type="link" :icon="!value && 'plus'" class="px-0">
                {{value ? $t('task.change') : $t('task.select')}}
            </a-button>

            <a-button v-if="value" @click.stop="clear()" type="link" icon="close-circle" class="px-0 text-current remove_brn" />
        </div>

        <div v-else-if="inputType === 'icon'" class="ticket_icon_trigger" :title="ticketTitle" @click="openSelect">
            <template v-if="value">
                <div class="ticket_icon_trigger__selected">
                    <span class="ticket_number">#{{ value.number || value.id }}</span>
                    <i class="fi fi-rr-angle-small-down ml-1" />
                </div>
            </template>
            <template v-else>
                <div v-tippy="{ inertia : true }" :content="$t('helpdesk.ticket_select')" class="ticket_icon_trigger__empty">
                    <i class="fi fi-rr-comment-alt-dots" />
                </div>
            </template>
        </div>

        <DrawerTemplate
            v-model="visible"
            :width="windowWidth"
            :wrapClassName="drawerWrapClass"
            :title="placeholder || $t('helpdesk.ticket_select')"
            @close="visible = false">
            <div class="drawer_content">
                <a-input-search
                    class="mb-2 search_input"
                    :loading="searchLoading"
                    v-model="search"
                    ref="searchInput"
                    @input="onSearch"
                    :placeholder="$t('wgr.search')" />

                <div class="drawer_list">
                    <div
                        v-for="(ticket, index) in list"
                        :key="ticket.id || index"
                        :title="`#${ticket.number} ${ticket.name}`"
                        :class="checkSelected(ticket)"
                        class="cursor-pointer project_item py-2 truncate"
                        @click="selectItem(ticket)">
                        #{{ ticket.number }} {{ ticket.name }}
                    </div>

                    <div v-if="page === 1 && loading" class="flex justify-center mt-2">
                        <a-spin size="small" />
                    </div>

                    <infinite-loading
                        ref="userInfinite"
                        :identifier="infiniteId"
                        :force-use-infinite-wrapper="infiniteWrapperSelector"
                        @infinite="getList"
                        v-bind:distance="10">
                        <div slot="spinner"><a-spin v-if="page !== 1" size="small" /></div>
                        <div slot="no-more"></div>
                        <div slot="no-results"></div>
                    </infinite-loading>
                </div>
            </div>
            <template #footer>
                <div v-if="inputType === 'icon' && value && showClear" class="footer_actions">
                    <a-button type="ui" size="large" class="footer_btn" @click="clearAndClose()">
                        {{ $t('task.reset') }}
                    </a-button>
                    <a-button type="ui_ghost" size="large" class="footer_btn" @click="visible = false">
                        {{ $t('close') }}
                    </a-button>
                </div>
                <a-button v-else type="ui_ghost" size="large" block @click="visible = false">
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
            return `ticket_select_mobile_drawer_${this._uid}`
        },
        infiniteWrapperSelector() {
            return `.${this.drawerWrapClass} .drawer_body`
        }
    }
}
</script>

<style lang="scss" scoped>
.dummy_placeholder{
    color: #888888
}
.drawer_list{
    width: 100%;
}
.drawer_content{
    width: 100%;
}
.footer_actions{
    display: flex;
    gap: 8px;
    width: 100%;
}
.footer_btn{
    flex: 1 1 50%;
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
.ticket_icon_trigger{
    min-height: 28px;
    display: flex;
    align-items: center;
    cursor: pointer;
    &__empty{
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
    &__selected{
        display: flex;
        align-items: center;
        border: 1px solid var(--borderColor);
        border-radius: 16px;
        padding: 2px 8px;
        background: #fff;
    }
    .ticket_number{
        font-size: 12px;
        line-height: 14px;
    }
}
</style>
