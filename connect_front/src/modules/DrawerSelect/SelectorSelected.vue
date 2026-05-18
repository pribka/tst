<template>
    <div class="selected-wrapper">
        <div class="top">
            <span class="title">{{ selectedList.length ? $t('selected_users_count', { count: selectedList.length }) : $t('selected_users') }}</span>
            <transition name="slide-fade">
                <i
                    v-if="selectedList && selectedList.length"
                    class="fi fi-rr-trash delete-icon"
                    v-tippy
                    :content="$t('clear')"
                    @click="deselectAll()" />
            </transition>
        </div>
        <div class="list">
            <div v-for="user in selectedList" :key="user.id" class="user-item">
                <div class="user">
                    <a-avatar
                        icon="user"
                        :src="avatarPatch(user)"
                        class="avatar" />
                    <div class="username">
                        <div class="name">
                            {{ user.full_name || user.name }}
                        </div>
                        <div v-if="user?.job_title" class="job_title">
                            {{ user.job_title }} 
                        </div>
                    </div>
                </div>
                <i
                    class="fi fi-rr-remove-user delete-icon"
                    v-tippy
                    :content="$t('remove')"
                    @click="deselectUser(user)" />
            </div>
        </div>
    </div>
</template>
<script>
export default {
    name: 'Selected',
    props: {
        selectedList: {
            type: Array,
            default: () => []
        },
        selectUser: {
            type: Function,
            default: () => {}
        },
        deselectUser: {
            type: Function,
            default: () => {}
        },
        deselectAll: {
            type: Function,
            default: () => {}
        },
        multiple: {
            type: Boolean,
            default: false
        },
    },
    methods: {
        avatarPatch(user) {
            return user?.avatar?.path || user?.image?.path || null
        }
    }
}
</script>

<style lang="scss" scoped>
.slide-fade-enter-active {
  transition: all 0.3s ease;
}
.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1);
}
.slide-fade-enter,
.slide-fade-leave-to {
  transform: translateX(10px);
  opacity: 0;
}
</style>

<style lang="scss">
.selected-wrapper {
    background-color: rgba(240, 241, 247, 1);
    height: 100%;
    min-height: 0;
    border-radius: 16px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    .top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        .title {
            font-weight: 400;
            font-size: 14px;
            line-height: 20px;
        }
    }
    .list {
        flex: 1;
        overflow: auto;
        min-height: 0;
        
        .user-item {
            padding: 8px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-radius: 8px;
            gap: 12px;
            &:hover {
                background-color: rgba(255, 255, 255, 1);
            }
            .user {
                display: flex;
                align-items: center;
                gap: 12px;
                width: 100%;
                &:not(:last-child){
                    margin-bottom: 4px;
                }
                .avatar {
                    min-width: 32px;
        
                }
                .username {
                    display: flex;
                    flex-direction: column;
                    .name {
                        transition: color 0.2s ease;
                        display: -webkit-box;
                        -webkit-line-clamp: 1;
                        -webkit-box-orient: vertical;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        line-height: 1.5;
                        max-height: calc(1 * 1.5em);
                        word-break: break-word;
                    }
                    .job_title {
                        font-size: 12px;
                        line-height: 16px;
                        color: rgba(136, 136, 136, 1);

                        transition: color 0.2s ease;
                        display: -webkit-box;
                        -webkit-line-clamp: 1;
                        -webkit-box-orient: vertical;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        line-height: 1.5;
                        max-height: calc(1 * 1.5em);
                        word-break: break-word;
                    }
                }
            }
        }
    }
    .delete-icon {
        cursor: pointer;
        color: rgba(255, 92, 92, 1);
    }
}
</style>