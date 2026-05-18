<template>
    <div class="m_wrapper" :class="isMobile && 'is_mobile'">
        <div class="m_wrapper__header">
            <div class="h_left">
                <h1 v-if="pageTitle">{{ pageTitle }}</h1>
                <slot name="h_left"></slot>
            </div>
            <div v-if="$slots.h_center" class="h_center">
                <slot name="h_center"></slot>
            </div>
            <div v-if="$slots.h_right" class="h_right">
                <slot name="h_right"></slot>
            </div>
        </div>
        <div 
            v-if="pageRoutes && pageRoutes.length && !isMobile && isHideOneRoute" 
            class="m_wrapper__subheader">
            <a-menu 
                mode="horizontal" 
                :selectedKeys="[$route.name]">
                <a-menu-item 
                    v-for="route in pageRoutes" 
                    :key="route.name" 
                    @click="changePage(route.name)">
                    <div class="flex items-center">
                        <i v-if="route.meta.icon" class="fi mr-2" :class="route.meta.icon" />
                        {{ route.meta.title }}
                    </div>
                </a-menu-item>
            </a-menu>
        </div>
        <div 
            class="m_wrapper__body" 
            :class="[bodyPadding && 'body_pd', bodyOHidden && 'overflow-hidden', !bodyXPadding && 'body_x_no_pd', !isMobile && 'flex flex-col']">
            <slot />
        </div>
    </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
    props: {
        pageTitle: {
            type: String,
            default: ''
        },
        bodyPadding: {
            type: Boolean,
            default: true
        },
        bodyXPadding: {
            type: Boolean,
            default: true
        },
        bodyOHidden: {
            type: Boolean,
            default: false
        },
        pageRoutes: {
            type: Array,
            default: () => []
        },
        hideOneRoute: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        }),
        isHideOneRoute() {
            if(this.hideOneRoute) {
                return this.pageRoutes?.length > 1 ? true : false
            }
            return true
        }
    },
    methods: {
        changePage(name) {
            this.$router.push({ name })
        }
    }
}
</script>

<style lang="scss" scoped>
.m_wrapper{
    &:not(.is_mobile){
        height: 100%;
        overflow: hidden;
        display: flex;
        width: 100%;
        flex-direction: column;
        .m_wrapper__body{
            flex-grow: 1;
            &:not(.overflow-hidden){
                overflow: auto;
            }
        }
    }
    &__header{
        padding: 10px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid var(--border2);
        background: var(--mBg);
        position: relative;
        margin: var(--wrapperMargin);
        h1{
            font-weight: 400;
            font-size: 18px;
            margin-bottom: 0px;
            margin-right: 20px;
            color: #000;
        }
        .h_left{
            display: flex;
            align-items: center;
        }
        .h_right{
            display: flex;
            align-items: center;
        }
        &::v-deep{
            .filter_pop_wrapper{
                .filter_input{
                    border-color: transparent!important;
                }
            }
        }
    }
    &__subheader{
        border-bottom: 1px solid var(--border2);
        background: var(--mBg);
        margin: var(--wrapperMargin);
        &::v-deep{
            .ant-menu{
                border: 0px;
                user-select: none;
                background: var(--mBg);
                &.ant-menu-horizontal{
                    line-height: 38px;
                }
                .ant-menu-item{
                    padding-left: 0px;
                    padding-right: 0px;
                    margin-right: 15px;
                    color: #000;
                    &.ant-menu-item-selected{
                        border-color: #ff9a01;
                        color: #000;
                    }
                    &:not(.ant-menu-item-selected){
                        opacity: 0.6;
                        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                        &:hover{
                            opacity: 1;
                            border-color: transparent;
                        }
                    }
                }
            }
        }
    }
    &__body{
        &.body_pd{
            padding: 15px;
        }
        &.body_x_no_pd{
            padding-left: 0px;
            padding-right: 0px;
        }
    }
    &.is_mobile{
        .m_wrapper__header{
            border-bottom: 0px;
            padding-bottom: 0px;
            padding-top: 15px;
            margin-bottom: 10px;
            h1{
                font-size: 1.4rem;
                line-height: 1.5;
                font-weight: 400;
                margin-bottom: 0px;
                margin-top: 0px;
            }
        }
        .m_wrapper__body{
            padding-top: 0px;
        }
    }
}
</style>