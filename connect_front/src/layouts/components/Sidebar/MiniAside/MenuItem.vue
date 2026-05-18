<template>
    <router-link 
        :to="{ name: item.name }"
        :title="item.title"
        class="menu_item m_d"
        :class="[{ hidden_item: !item.isShow }, { manage_mode: disableNavigation }]"
        @click="handleLinkClick">
        <div 
            class="menu_item__wrapper relative" 
            @mouseenter="itemHover()">
            <div class="menu_item__content truncate">
                <div class="icon">
                    <i class="fi" :class="item.icon" />
                </div>
                <div v-if="isHovered" class="name truncate pr-2">{{ item.title }}</div>
            </div>
            <div class="menu_item__right">
                <transition v-if="isHovered" name="menu-add-fade-slide">
                    <div 
                        v-if="isAdd && !disableNavigation"
                        class="menu_add_btn" 
                        :title="$t('Add')"
                        @click.stop.prevent="handleAddClick">
                        <i class="fi fi-rr-plus-small" />
                    </div>
                </transition>
                <div v-if="item.badge && !disableNavigation" class="flex gap-2 items-center">
                    <button
                        v-if="isChatMenuItem && isHovered"
                        type="button"
                        class="menu_window_btn"
                        v-tippy
                        :content="$t('open_new_window')"
                        @click.stop.prevent="openEmptyChatWindow">
                        <i class="fi fi-rr-arrow-up-right-from-square" />
                    </button>
                    <transition name="badge-pop">
                        <a-badge 
                            v-if="getCounter && getCounter.count" 
                            :count="getCounter.count"
                            :class="!isHovered && 'a_badge'"
                            :number-style="{
                                boxShadow: '0 0 0 0',
                                backgroundColor: primaryColor
                            }"/>
                    </transition>
                    <transition name="badge-pop">
                        <div v-if="isHovered && getCounter && getCounter.mention_count"  class="mentions_badge">
                            @
                            <a-badge 
                                :count="getCounter.mention_count"
                                style="margin-left: 4px;"
                                :number-style="{
                                    color: 'var(--blue)',
                                    boxShadow: '0 0 0 0',
                                    backgroundColor: 'transparent'
                                }"/>
                        </div>
                    </transition>
                </div>
            </div>
        </div>
        <component ref="loadCompRef" :is="asyncLoadComp" contractorSelect :eventsEnabled="false" />
    </router-link>
</template>

<script>
import itemMixins from '../itemMixins.js'
export default {
    mixins: [itemMixins]
}
</script>

<style lang="scss" scoped>
.badge-pop-enter-active,
.badge-pop-leave-active{
    transition: transform 0.2s ease, opacity 0.2s ease;
    transform-origin: center;
}
.badge-pop-enter,
.badge-pop-leave-to{
    transform: scale(0);
    opacity: 0;
}
.badge-pop-enter-to,
.badge-pop-leave{
    transform: scale(1);
    opacity: 1;
}
.a_badge{
    position: absolute;
    z-index: 5;
    top: 3px;
    right: 3px;
}
.menu-add-fade-slide-enter-active, .menu-add-fade-slide-leave-active {
    transition: all 0.3s ease
}
.menu-add-fade-slide-enter, .menu-add-fade-slide-leave-to {
    opacity: 0
}
.mentions_badge{
    min-width: 20px;
    height: 20px;
    min-height: 20px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    color: var(--blue);
    background-color: #e8ecfa;
    padding: 0 5px;
    font-size: 12px;
    &::v-deep{
        .ant-badge-count{
            padding: 0px;
            min-width: auto;
        }
    }
}
.menu_add_btn{
    width: 20px;
    height: 20px;
    border-radius: 50%;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: #fff;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    opacity: 0;
    &:hover{
        opacity: 1!important;
    }
}
.menu_window_btn{
    width: 20px;
    height: 20px;
    border: 0;
    padding: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    color: var(--blue);
    cursor: pointer;

    i{
        font-size: 14px;
    }

    &:hover,
    &:focus{
        background: transparent;
        color: var(--blue);
        outline: none;
    }
}
.menu_item{
    padding: 2px 12px 2px 12px;
    display: block;
    user-select: none;
    color: #fff;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &__wrapper{
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-radius: var(--borderRadius);
        /**padding: 9px 10px;     padding: 10px 14px; */
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    .menu_item__content{
        display: flex;
        align-items: center;
        min-width: 20px;
        .icon{
            margin-right: 8px;
            width: 20px;
            height: 20px;
            line-height: 20px;
            font-size: 14px;
        }
    }
    &:hover{
        .menu_add_btn{
            opacity: 0.6;
        }
    }
    &.hidden_item{
        opacity: 0.6;
    }
    &.manage_mode{
        .menu_item__wrapper{
            padding-right: 56px;
        }
    }
    &:hover,
    &.router-link-active{
        .menu_item__wrapper{
            background: rgba(223, 237, 255, 0.1);
        }
    }
}
</style>
