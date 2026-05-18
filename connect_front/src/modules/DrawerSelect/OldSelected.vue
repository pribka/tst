<template>
    <div 
        v-if="oldSelected.length"
        class="old_selected">
        <div 
            v-if="showLabel" 
            class="lable mb-2 flex items-center justify-between">
            {{ labelText }}
        </div>

        <div 
            class="scroll_wrap"
            @mouseenter="hovered = true"
            @mouseleave="hovered = false">
            <a-button
                v-if="showLeftArrow"
                class="scroll_arrow left"
                shape="circle"
                size="small"
                type="flat_primary"
                flaticon
                icon="fi-rr-angle-small-left"
                @click="scrollLeft" />

            <div
                ref="scrollRef"
                class="flex items-center overflow-x-auto pb-3 -mb-3 scroller"
                @scroll="onScroll">
                <template v-if="isMobile">
                    <div 
                        v-for="item in oldSelected" 
                        :key="item.id"
                        :title="item[titleField]"
                        class="item_sel cursor-pointer shrink-0"
                        @click="itemSelect(item, true)">
                        <a-avatar
                            v-if="avatarFieldAsRootField"
                            :icon="avatarIcon"
                            :size="avatarSize"
                            :src="item[avatarField] || null"/>
                        <a-avatar
                            v-else-if="customAvatarPath"
                            :icon="avatarIcon"
                            :size="avatarSize"
                            :src="item[avatarField] && item[avatarField][avatarSubpath] && item[avatarField][avatarSubpath][avatarPathField] ? item[avatarField][avatarSubpath][avatarPathField] : null" />
                        <a-avatar
                            v-else
                            :icon="avatarIcon"
                            :size="avatarSize"
                            :src="item[avatarField] && item[avatarField][avatarPathField] ? item[avatarField][avatarPathField] : null" />
                        <div 
                            v-if="checkSelected(item)" 
                            class="check_user">
                            <a-icon type="check" />
                        </div>
                    </div>
                </template>

                <template v-else>
                    <a-tooltip 
                        v-for="item in oldSelected" 
                        :key="item.id"
                        destroyTooltipOnHide
                        :getPopupContainer="bodyContainer">
                        <template slot="title">
                            {{ item[titleField] }}
                        </template>
                        <div 
                            class="item_sel cursor-pointer shrink-0"
                            @click="itemSelect(item, true)">
                            <a-avatar
                                v-if="avatarFieldAsRootField"
                                :icon="avatarIcon"
                                :size="avatarSize"
                                :src="item[avatarField] || null"/>
                            <a-avatar
                                v-else-if="customAvatarPath"
                                :icon="avatarIcon"
                                :size="avatarSize"
                                :src="item[avatarField] && item[avatarField][avatarSubpath] && item[avatarField][avatarSubpath][avatarPathField] ? item[avatarField][avatarSubpath][avatarPathField] : null" />
                            <a-avatar
                                v-else
                                :icon="avatarIcon"
                                :size="avatarSize"
                                :src="item[avatarField] && item[avatarField][avatarPathField] ? item[avatarField][avatarPathField] : null" />
                            <div 
                                v-if="checkSelected(item)" 
                                class="check_user">
                                <a-icon type="check" />
                            </div>
                        </div>
                    </a-tooltip>
                </template>
            </div>
            <a-button
                v-if="showRightArrow"
                class="scroll_arrow right"
                shape="circle"
                size="small"
                type="flat_primary"
                flaticon
                icon="fi-rr-angle-small-right"
                @click="scrollRight" />
        </div>
    </div>
</template>

<script>
export default {
    props: {
        multiple: {
            type: Boolean,
            default: false
        },
        checkSelected: {
            type: Function,
            default: () => {}
        },
        titleField: {
            type: String,
            default: 'full_name'
        },
        itemSelect: {
            type: Function,
            default: () => {}
        },
        getPopupContainer: {
            type: Function,
            default: () => document.body
        },
        avatarField: {
            type: String,
            default: 'avatar'
        },
        avatarPathField: {
            type: String,
            default: 'path'
        },
        labelText: {
            type: String,
            default: 'Ранее выбранные'
        },
        showLabel: {
            type: Boolean,
            default: true
        },
        avatarIcon: {
            type: String,
            default: 'user'
        },
        avatarSize: {
            type: Number,
            default: 35
        },
        listMaxLength: {
            type: Number,
            default: 30
        },
        customAvatarPath: {
            type: Boolean,
            default: false
        },
        avatarSubpath: {
            type: String,
            default: 'avatar'
        },
        avatarFieldAsRootField: {
            type: Boolean,
            default: false
        },
        bodyContainer: {
            type: Function,
            default: () => document.body
        }
    },
    data() {
        return {
            hovered: false,
            canScrollLeft: false,
            canScrollRight: false
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        oldSelected() {
            const list = this.$store.getters['recentUsers/list'] || []
            return list.slice(0, this.listMaxLength)
        },
        showLeftArrow() {
            return !this.isMobile && this.hovered && this.canScrollLeft
        },
        showRightArrow() {
            return !this.isMobile && this.hovered && this.canScrollRight
        }
    },
    watch: {
        oldSelected() {
            this.$nextTick(() => this.updateArrows())
        },
        isMobile() {
            this.$nextTick(() => this.updateArrows())
        }
    },
    mounted() {
        this.$nextTick(() => this.updateArrows())
        window.addEventListener('resize', this.updateArrows)
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.updateArrows)
    },
    methods: {
        onScroll() {
            this.updateArrows()
        },
        getEl() {
            return this.$refs.scrollRef
        },
        updateArrows() {
            const el = this.getEl()
            if (!el || this.isMobile) {
                this.canScrollLeft = false
                this.canScrollRight = false
                return
            }

            const max = el.scrollWidth - el.clientWidth
            if (max <= 0) {
                this.canScrollLeft = false
                this.canScrollRight = false
                return
            }

            const left = el.scrollLeft
            const eps = 1

            this.canScrollLeft = left > eps
            this.canScrollRight = left < max - eps
        },
        scrollBy(delta) {
            const el = this.getEl()
            if (!el) return

            const step = Math.max(el.clientWidth * 0.7, 180)
            const next = el.scrollLeft + delta * step

            el.scrollTo({ left: next, behavior: 'smooth' })
        },
        scrollLeft() {
            this.scrollBy(-1)
        },
        scrollRight() {
            this.scrollBy(1)
        }
    }
}
</script>

<style lang="scss" scoped>
.old_selected{
    .check_user{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 5;
        background: rgba(0, 0, 0, 0.2);
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .lable{
        font-weight: 300;
        font-size: 13px;
    }
    .item_sel{
        position: relative;
        overflow: hidden;
        width: 35px;
        height: 35px;
        border-radius: 50%;
        &:not(:last-child){
            margin-right: 3px;
        }
    }
}

.scroll_wrap{
    position: relative;
    min-width: 0;
}

.scroller{
    scroll-behavior: smooth;
}

.scroll_arrow{
    position: absolute;
    margin-top: -5px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;
    &.left{
        left: -10px;
    }
    &.right{
        right: -10px;
    }
}
</style>