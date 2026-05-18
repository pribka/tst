<template>
    <div class="w-full nd_item relative">
        <div v-if="!bell" class="flex items-center justify-between w-full">
            <div class="flex w-full">
                <div v-if="!isMobile" class="shrink-0 mr-2">
                    <a-avatar
                        class="noty_avatar"
                        :class="isMobile && 'mob_a'"
                        :style="`color: ${getColor(item.color)};backgroundColor: ${getBackground(item.color)}`"
                        :icon="getAvatarIcon(item.icon)"
                        :size="30">
                        <i v-if="getIconClass(item.icon)" :class="getIconClass(item.icon)" />
                    </a-avatar>
                </div>
                <div>
                    <div class="flex items-center" :class="isMobile && 'mb-1'">
                        <span class="notify_title flex items-center"
                              :class="{'mob-text-base':isMobile}">
                            <div v-if="isMobile" class="shrink-0" :class="notificationTitle && 'mr-2'">
                                <a-avatar
                                    class="noty_avatar"
                                    :class="isMobile && 'mob_a'"
                                    :style="`color: ${getColor(item.color)};backgroundColor: ${getBackground(item.color)}`"
                                    :size="24"
                                    :icon="getAvatarIcon(item.icon)">
                                    <i v-if="getIconClass(item.icon)" :class="getIconClass(item.icon)" />
                                </a-avatar>
                            </div>
                            {{ notificationTitle }}
                        </span>
                        <a-tag v-if="!item.is_read && !isMobile" color="red">
                            {{ $t('noty.unread') }}
                        </a-tag>
                        <a-badge v-if="!item.is_read && isMobile" 
                                 status="error" 
                                 class="ml-1" />
                        <span class="ml-2 font-light" 
                              :class="{'mob-text-sm':isMobile}">{{ date }}</span>
                    </div>
                    <div class="flex w-full">
                        <div class="text-sm break-words"
                             :class="{'mob-text-base':isMobile}">
                            <Messsage :item="item" @read="read()" /> 
                        </div>
                    </div>
                </div>
            </div>
            <div v-if="isMobile" class="read_b ml-2">
                <transition name="slide-fade">
                    <a-button 
                        v-if="!item.is_read"
                        shape="circle"
                        icon="fi-rr-check"
                        flaticon
                        @click="read" 
                        class="mobile_read_btn flex items-center justify-center text-xs lg:text-sm" />
                </transition>
            </div>
            <transition name="slide-fade">
                <div v-if="!item.is_read && !isMobile">
                    <a-checkbox @change="read" class="whitespace-nowrap">
                        {{ $t('noty.read') }}
                    </a-checkbox>
                </div>
            </transition>
        </div>
        <div v-else class="flex items-center justify-between truncate">
            <div class="flex truncate">
                <div class="mr-3" @click="pushRoute">
                    <a-avatar
                        class="noty_avatar"
                        :style="`color: ${getColor(item.color)};
                backgroundColor: ${getBackground(item.color)}`"
                        :icon="getAvatarIcon(item.icon)"
                        size="default">
                        <i v-if="getIconClass(item.icon)" :class="getIconClass(item.icon)" />
                    </a-avatar>
                </div>
                <div class="text-sm truncate">
                    <Messsage :item="item" @read="read()"/>
                    <div class="notify_date text-sm">
                        {{ date }}
                    </div>
                </div>
            </div>
            <div class="read_btn absolute cursor-pointer z-10 items-center justify-center">
                <a-icon @click="read" type="close"  />
            </div>
        </div>
    </div>
</template>


<script>
import {getColor, getBackground, getNotificationIconClass} from '../utils'
export default {
    name: "NotificationMessageItem",
    components: {
        Messsage: () => import('./Message')
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        bell: {
            type: Boolean,
            default: false
        }
    },
   
    computed: {
        date() { 
            let current = this.$moment(),
                createdAt = this.$moment(this.item.created_at),
                days = createdAt.diff(current, 'days')

            if (createdAt.isAfter(current))
                return current.fromNow()

            if(days < -2)
                return createdAt.format('DD.MM.YYYY HH:mm')
            else {
                return createdAt.fromNow()
            }
        },
        isMobile() {
            return this.$store.state.isMobile
        },
        notificationTitle() {
            return this.item?.icon_name || this.$t('noty.defaultTitle')
        }
    },
    methods: {
        getColor,
        getBackground,
        getIconClass: getNotificationIconClass,
        getAvatarIcon(icon) {
            return this.getIconClass(icon) ? null : icon
        },
        read(){
            this.$emit('read', this.item)
        },
        pushRoute(){
            if(this.$route.name !=='notifications')
                this.$router.push({name: 'notifications'})
            this.$emit('close')   
        }
    }
}
</script>

<style lang="scss" scoped>
.notify_title{
    color: #30323a;
    font-size: 15px;
    font-weight: 600;
}
.slide-fade-enter-active {
  transition: all .3s ease;
}
.slide-fade-leave-active {
  transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter, .slide-fade-leave-to{
  transform: translateX(10px);
  opacity: 0;
}
.read_b{
    align-self: flex-start;
    min-width: 32px;
    margin-top: 2px;
}
.mobile_read_btn{
    min-width: 32px;
    max-width: 32px;
    width: 32px;
    min-height: 32px;
    max-height: 32px;
    height: 32px;
    padding: 0!important;
    line-height: 32px!important;
    flex-shrink: 0;
}
.read_btn {
  background: #fff;
  width: 31px;
  height: 31px;
  top: 2px;
  right: 1px;
  border-radius: 50%;
  display: none;
}
.mob_a{
    width: 35px;
    height: 35px;
    line-height: 35px;
    font-size: 20px;
}
.nd_item {
  &:hover {
    .read_btn {
      display: flex;
    }
  }
    &::v-deep{
    .noty_avatar{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        .ant-avatar-string{
            position: static;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            line-height: 1!important;
            transform: none!important;
        }
        .fi{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            line-height: 1;
        }
    }
    .ant-tag{
        font-size: 11px;
        line-height: 20px;
        padding: 0 6px;
        margin-left: 6px;
    }
  }
}

.mob-text-sm {
    font-size: 0.8rem;
    line-height: 1.5;
}
.mob-text-base {
    font-size: 1rem;
    line-height: 1.5;

}
</style>
