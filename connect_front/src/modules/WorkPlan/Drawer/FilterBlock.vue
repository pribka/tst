<template>
    <div :class="[!vertical && isMobile && 'm_scroll', vertical && 'block_filter mb-3 rounded-lg select-none', useInject && 'bg_invert']">
        <h3 v-if="vertical">{{ $t('workplan.filter') }}</h3>
        <div :class="[!vertical && isMobile && 'm_scroll__wrapper', vertical ? 'flex gap-1 flex-col' : 'flex items-center gap-2 mb-3']">
            <div class="filter_item">
                <div v-if="vertical" class="filter_item__label">
                    {{ $t('workplan.filter_user') }}
                </div>
                <UserDrawer
                    v-model="user"
                    multiple
                    class="user_select"
                    :id="defaultUserSelectId"
                    buttonNew
                    clearButtonRight
                    :selectedShowButtonText="!vertical"
                    showClear
                    :buttonText="$t('workplan.filter_user_all')"
                    buttonIcon="fi-rr-user"
                    :title="$t('workplan.filter_user')"
                    @change="userChange"/>
            </div>
            <div class="filter_item">
                <div v-if="vertical" class="filter_item__label">
                    {{ $t('workplan.filter_project') }}
                </div>
                <ProjectSelect 
                    v-model="project"
                    class="crc_btn"
                    :placeholder="$t('workplan.filter_project_all')"
                    :inputType="!vertical ? 'button' : 'input'"
                    :showArrow="vertical"
                    useInputIcon
                    usePopupContainer
                    :customPopupContainer="popupContainer"
                    @change="filterChange" />
            </div>
            <div class="filter_item">
                <div v-if="vertical" class="filter_item__label">
                    {{ $t('workplan.filter_team') }}
                </div>
                <GroupSelect 
                    class="crc_btn"
                    v-model="workgroup"
                    usePopupContainer
                    :inputType="!vertical ? 'button' : 'input'"
                    :showArrow="vertical"
                    useInputIcon
                    :placeholder="$t('workplan.filter_team_all')"
                    :customPopupContainer="popupContainer"
                    @change="filterChange" />
            </div>
            <transition v-if="!isMobile" name="slowfade" appear :duration="{ enter: 600, leave: 300 }">
                <a-button 
                    v-if="user.length || project || workgroup" 
                    type="ui_ghost mt-2"
                    @click="clearFilter()">
                    {{ $t('workplan.filter_clear') }}
                </a-button>
            </transition>
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    components: {
        UserDrawer: () => import("@apps/DrawerSelect/index.vue"),
        ProjectSelect: () => import("@apps/DrawerSelect/ProjectSelect.vue"),
        GroupSelect: () => import("@apps/DrawerSelect/GroupSelect.vue")
    },
    props: {
        storeKey: {
            type: String,
            required: true
        },
        popupContainer: {
            type: Function,
            default: () => document.body
        },
        clearFilter: {
            type: Function,
            default: () => {}
        },
        userChange: {
            type: Function,
            default: () => {}
        },
        filterChange: {
            type: Function,
            default: () => {}
        },
        vertical: {
            type: Boolean,
            default: false
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({ 
            isMobile: state => state.isMobile
        }),
        project: {
            get() {
                return this.$store.state.workplan.project?.[this.storeKey] || null
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'project',
                    storeKey: this.storeKey
                })
            }
        },
        workgroup: {
            get() {
                return this.$store.state.workplan.workgroup?.[this.storeKey] || null
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'workgroup',
                    storeKey: this.storeKey
                })
            }
        },
        user: {
            get() {
                return this.$store.state.workplan.user?.[this.storeKey] || null
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_FIELD', {
                    value,
                    field: 'user',
                    storeKey: this.storeKey
                })
            }
        },
    },
    data() {
        return {
            defaultUserSelectId: 'workplan',
        }
    }
}
</script>

<style lang="scss" scoped>
.filter_item{
    &__label{
        margin-bottom: 6px;
    }
}
.user_select{
    &::v-deep{
        .ant-btn{
            &.ant-btn-flat{
                background-color: #fff;
                border-color: #fff;
            }
        }
    }
}
.crc_btn{
    background: #fff;
    border-color: #fff;
}
.block_filter{
    background: #fff;
    padding: 15px;
    h3{
        font-size: 18px;
        font-weight: 600;
        color: #000;
        margin-bottom: 15px;
    }
    .crc_btn{
        background: #f7f9fc;
        padding: 8px 15px;
        height: 40px;
    }
    .user_select{
        &::v-deep{
            .ant-btn{
                &.ant-btn-flat{
                    background-color: #f7f9fc;
                    border-color: #f7f9fc;
                    min-height: 40px;
                    display: block;
                    box-shadow: initial;
                    width: 100%;
                    text-align: left;
                    padding: 8px 15px;
                    color: #888888;
                }
            }
        }
    }
}
.slowfade-enter-active,
.slowfade-leave-active {
    transition: opacity .4s ease, transform .4s ease;
}
.slowfade-enter,
.slowfade-leave-to {
    opacity: 0;
    transform: translateX(8px);
}
.m_scroll{
    display: -webkit-box;
    margin-bottom: 0;
    overflow-x: scroll;
    width: 100%;
    margin-left: -15px;
    margin-right: -15px;
    -ms-overflow-style: none;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
    &__wrapper{
        padding-left: 15px;
        padding-right: 15px;
    }
}
.bg_invert{
    .user_select{
        &::v-deep{
            .ant-btn{
                &.ant-btn-flat{
                    background-color: #f7f9fc;
                    border-color: #f7f9fc;
                }
            }
        }
    }
    .crc_btn{
        background: #f7f9fc;
        border-color: #f7f9fc;
    }
    &.block_filter{
        background: #f7f9fc;
        .crc_btn{
            background: #fff;
        }
        .user_select{
            &::v-deep{
                .ant-btn{
                    &.ant-btn-flat{
                        background-color: #fff;
                        border-color: #fff;
                    }
                }
            }
        }
    }
}
</style>
