<template>
    <div class="chapters_list__item" :class="actChapters === item.id && 'active'">
        <div class="wrap">
            <div class="ico">
                <a-button 
                    v-if="item.pages_num > 0"
                    type="ui"
                    ghost
                    shape="circle"
                    size="small"
                    :loading="loading"
                    flaticon 
                    :icon="show ? 'fi-rr-angle-small-down' : 'fi fi-rr-angle-small-right'"
                    @click="openPagesLoc()" />
            </div>
            <div class="item_name_wrapper" @click="openChaptersLoc(item.id)">
                <div class="item_name">
                    {{ item.name }}
                </div>
            </div>
        </div>
        <div 
            v-if="show && item.pages && item.pages.length" 
            class="pages_list">
            <div 
                v-for="page in item.pages" 
                :key="page.id" 
                class="pages_list__item" 
                :class="actPages === page.id && 'active'"
                @click="openPages(page.id)">
                {{ page.name }}
            </div>
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        openChapters: {
            type: Function,
            default: () => {}
        },
        actChapters: {
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
    watch: {
        initPageAct(val) {
            if(this.isSearch && val && this.item.id === val) {
                this.disabledSearch()
                this.openPagesLoc()
            }
        }
    },
    created() {
        if(this.item.id === this.initPageAct) {
            this.openPagesLoc()
        }
    },
    methods: {
        hideShow() {
            this.btnShow = false
        },
        async openChaptersLoc(id) {
            this.openChapters(id)
            if(this.actChapters === id) {
                if(!this.btnShow && !this.item.show) {
                    try {
                        this.loading = true
                        const { data } = await this.$http.get(`/wiki/chapters/${this.item.id}/`)
                        if(data) {
                            this.checkActiveChapters({
                                section: data.sections?.length ? data.sections[0].id : null, 
                                chapter: this.item.id, 
                            })
                            this.setPagesListLoc({
                                section: data.sections?.length ? data.sections[0].id : null, 
                                chapter: this.item.id, 
                                pages: data.pages
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
        async openPagesLoc() {
            if(!this.item.show)
                this.btnShow = !this.btnShow

            if(this.btnShow && !this.item.show) {
                try {
                    this.loading = true
                    const { data } = await this.$http.get(`/wiki/chapters/${this.item.id}/`)
                    if(data) {
                        this.setPagesListLoc({
                            section: data.sections?.length ? data.sections[0].id : null, 
                            chapter: this.item.id, 
                            pages: data.pages
                        })
                    }
                } catch(error) {
                    errorHandler({ error, show: false })
                } finally {
                    this.loading = false
                }
            } else {
                this.btnShow = false

                if(this.item.show)
                    this.closeChapter({
                        section: this.item.sections?.length ? this.item.sections[0].id : null, 
                        chapter: this.item.id
                    })

                this.setPagesListLoc({
                    section: this.item.sections?.length ? this.item.sections[0].id : null, 
                    chapter: this.item.id, 
                    pages: []
                })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.pages_list{
    padding-left: 50px;
    &__item{
        cursor: pointer;
        padding: 5px 0;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover{
            color: var(--blue);
        }
        &.active{
            color: var(--blue);
        }
    }
}
.chapters_list__item{
    cursor: pointer;
    padding: 5px 0;
    .wrap{
        display: flex;
        align-items: center;
    }
    &.active{
        .item_name{
            color: var(--blue);
        }
    }
    .item_name{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover{
            color: var(--blue);
        }
    }
    &:last-child{
        padding-bottom: 0px;
    }
    .ico{
        margin-right: 8px;
        color: var(--gray);
        width: 24px;
        height: 24px;
    }
}
</style>
