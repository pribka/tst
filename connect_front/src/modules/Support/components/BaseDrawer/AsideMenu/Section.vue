<template>
    <div 
        class="aside_menu__item" 
        :class="actSection === item.id && 'active'">
        <div class="name_wrapper">
            <div class="name" @click="openSectionsLoc(item.id)">
                <div class="ico"><i class="fi fi-rr-document"></i></div> {{ item.name }}
            </div>
            <a-button 
                v-if="item.chapters && item.chapters.length"
                type="ui"
                ghost
                shape="circle"
                :loading="loading"
                size="small"
                flaticon 
                :icon="show ? 'fi-rr-angle-small-up' : 'fi-rr-angle-small-down'"
                @click="openChaptersLoc()" />
        </div>
        <div 
            v-if="show && item.chapters_list" 
            class="chapters_list">
            <Chapter 
                v-for="chapter in item.chapters_list" 
                ref="chapter"
                :key="chapter.id"
                :actPages="actPages"
                :initPageAct="initPageAct"
                :disabledSearch="disabledSearch"
                :checkActiveChapters="checkActiveChapters"
                :isSearch="isSearch"
                :closeChapter="closeChapter"
                :setPagesListLoc="setPagesListLoc"
                :openPages="openPages"
                :actChapters="actChapters"
                :openChapters="openChapters"
                :item="chapter" />
        </div>
    </div>
</template>

<script>
import Chapter from './Chapter.vue'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        Chapter
    },
    props: {
        item: {
            type: Object,
            required: true
        },
        openSections: {
            type: Function,
            default: () => {}
        },
        setChaptersList: {
            type: Function,
            default: () => {}
        },
        closeSection: {
            type: Function,
            default: () => {}
        },
        actSection: {
            type: [Object, String],
            default: () => null
        },
        openChapters: {
            type: Function,
            default: () => {}
        },
        actChapters: {
            type: [Object, String],
            default: () => null
        },
        asyncSection: {
            type: [Object, String],
            default: () => null
        },
        openPages: {
            type: Function,
            default: () => {}
        },
        actPages: {
            type: [Object, String],
            default: () => null
        },
        setPagesListLoc: {
            type: Function,
            default: () => {}
        },
        initPageAct: {
            type: [Object, String],
            default: () => null
        },
        openChapterSectionsLoc: {
            type: Function,
            default: () => {}
        },
        closeChapter: {
            type: Function,
            default: () => {}
        },
        isSearch: {
            type: Boolean,
            default: false
        },
        disabledSearch: {
            type: Function,
            default: () => {}
        },
        checkActiveChapters: {
            type: Function,
            default: () => {}
        },
        opnSection: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        show() {
            return this.btnShow || this.item.show
        }
    },
    data() {
        return {
            btnShow: false,
            loading: false
        }
    },
    created() {
        if(this.asyncSection === this.item.id) {
            this.openChaptersLoc()
        }
    },
    watch: {
        actSection(val) {
            if(val && val === this.item.id && this.item.show && !this.item.chapters_list?.length) {
                this.openHandler()
            }
        }
    },
    methods: {
        hideShow() {
            this.btnShow = false
        },
        async openHandler() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`/wiki/sections/${this.item.id}/`)
                if(data) {
                    this.setChaptersList({
                        id: this.item.id,
                        list: data.chapters
                    })
                }
            } catch(error) {
                errorHandler({ error, show: false })
            } finally {
                this.loading = false
            }
        },
        async openSectionsLoc(id) {
            this.openSections(id)
            if(this.actSection === id) {
                if(!this.btnShow && this.item.show) {
                    try {
                        this.loading = true
                        const { data } = await this.$http.get(`/wiki/sections/${this.item.id}/`)
                        if(data) {
                            this.opnSection(this.item.id)
                            this.setChaptersList({
                                id: this.item.id,
                                list: data.chapters
                            })
                        }
                    } catch(error) {
                        errorHandler({ error, show: false })
                    } finally {
                        this.loading = false
                    }
                }
            }
        },
        clearShowChapters() {
            this.$nextTick(() => {
                if(this.$refs.chapter?.length) {
                    this.$refs.chapter.forEach(chp => {
                        if(chp.btnShow)
                            chp.hideShow()
                    })
                }
            })
        },
        async openChaptersLoc() {
            if(!this.item.show)
                this.btnShow = !this.btnShow

            if(this.btnShow && !this.item.show) {
                this.openHandler()
            } else {
                this.btnShow = false
                if(this.item.show)
                    this.closeSection(this.item.id)

                this.setChaptersList({
                    id: this.item.id,
                    list: []
                })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.aside_menu__item{
    padding: 7px 0;
    &.active{
        .name{
            color: var(--blue);
        }
    }
    .name_wrapper{
        display: flex;
        align-items: center;
        justify-content: space-between;
        cursor: pointer;
    }
    .name{
        display: flex;
        align-items: center;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        .ico{
            margin-right: 8px;
            color: var(--gray);
            width: 16px;
            height: 24px;
        }
        &:hover{
            color: var(--blue);
        }
    }
}
.chapters_list{
    margin-left: -5px;
}
</style>
