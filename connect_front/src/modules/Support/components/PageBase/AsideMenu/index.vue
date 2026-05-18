<template>
    <div class="aside_menu">
        <div v-if="loading" class="flex justify-center">
            <a-spin />
        </div>
        <div
            class="aside_menu_home"
            :class="{ active: isInitPage }"
            @click="goToWikiHome">
            <span>{{ $t('support.backToWikiHome') }}</span>
            <i class="fi fi-rr-angle-small-right"></i>
        </div>
        <Section
            v-for="item in list"
            :key="item.id"
            :ref="`section_${item.id}`"
            :item="item"
            :setChaptersList="setChaptersList"
            :actSection="actSection"
            :actChapters="actChapters"
            :openChapters="openChapters"
            :openPages="openPages"
            :initPageAct="initPageAct"
            :actPages="actPages"
            :closeChapter="closeChapter"
            :setPagesListLoc="setPagesListLoc"
            :opnSection="opnSection"
            :checkActiveChapters="checkActiveChapters"
            :openChapterSectionsLoc="openChapterSectionsLoc"
            :asyncSection="asyncSection"
            :disabledSearch="disabledSearch"
            :isSearch="isSearch"
            :closeSection="closeSection"
            :openSections="openSections" />
    </div>
</template>

<script>
import Section from './Section.vue'
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    components: {
        Section
    },
    computed: {
        contractorId() {
            return this.$store.state.user.user?.current_contractor?.id || null
        },
        isInitPage() {
            return !this.$route.params?.wikiType || !this.$route.params?.wikiId
        }
    },
    props: {
        isSearch: {
            type: Boolean,
            default: false
        },
        disabledSearch: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            loading: false,
            list: [],
            actSection: null,
            actChapters: null,
            asyncChaptersList: null,
            asyncSection: null,
            asyncPagesList: null,
            actPages: null,
            initPageAct: null,
            searchAsyncChaptersList: null
        }
    },
    created() {
        this.getSections()
        eventBus.$on('support_wiki_force_reload', this.reloadSections)
    },
    beforeDestroy() {
        eventBus.$off('support_wiki_force_reload', this.reloadSections)
    },
    methods: {
        goToWikiHome() {
            this.$router.push({
                name: 'company-wiki',
                query: this.$route.query
            })
        },
        reloadSections() {
            this.list = []
            this.actSection = null
            this.actChapters = null
            this.asyncChaptersList = null
            this.asyncSection = null
            this.asyncPagesList = null
            this.actPages = null
            this.initPageAct = null
            this.searchAsyncChaptersList = null
            this.getSections()
        },
        setAsyncChaptersList(list) {
            this.searchAsyncChaptersList = list
        },
        cleatAllActiveChapters() {
            this.list.forEach((item, index) => {
                if(item.chapters_list?.length) {
                    item.chapters_list.forEach((ch, cindex) => {
                        if(ch.show) {
                            this.list[index].chapters_list[cindex].show = false
                        }
                    })
                }
                this.$nextTick(() => {
                    if(this.$refs[`section_${item.id}`]?.[0])
                        this.$refs[`section_${item.id}`][0].clearShowChapters()
                })
            })
        },
        checkActiveChapters({ section, chapter }) {
            this.list.forEach((item, index) => {
                if(item.id === section && item.chapters_list?.length) {
                    item.chapters_list.forEach((ch, cindex) => {
                        if(ch.id === chapter && !ch.show) {
                            this.list[index].chapters_list[cindex].show = true
                        }
                    })
                }
            })
        },
        initPage({ chapter, page }) {
            this.initPageAct = chapter
            this.actPages = page
        },
        setActivePage({ page }) {
            this.actPages = page
        },
        closeChapter({ section, chapter }) {
            this.list.forEach((item, index) => {
                if(item.id === section && item.chapters_list?.length) {
                    item.chapters_list.forEach((ch, cindex) => {
                        if(ch.id === chapter && ch.show) {
                            this.list[index].chapters_list[cindex].show = false
                        }
                    })
                }
            })
        },
        closeAllPages() {
            this.actPages = null
            this.list.forEach((item, index) => {
                if(item.chapters_list?.length) {
                    item.chapters_list.forEach((ch, cindex) => {
                        if(ch.show) {
                            this.list[index].chapters_list[cindex].show = false
                            this.list[index].chapters_list[cindex].pages = []
                        }
                    })
                }
            })
        },
        setPagesListLoc({ section, chapter, pages }) {
            const index = this.list.findIndex(f => f.id === section)
            if(index !== -1) {
                if(this.list[index].chapters_list?.length) {
                    const cIndex = this.list[index].chapters_list.findIndex(f => f.id === chapter)
                    if(cIndex !== -1) {
                        this.list[index].chapters_list[cIndex].pages = pages
                    }
                }
            }
        },
        setPagesList({ section, chapter, pages }) {
            this.asyncPagesList = {
                section,
                chapter,
                pages
            }
            const index = this.list.findIndex(f => f.id === section)
            if(index !== -1) {
                if(this.list[index].chapters_list?.length) {
                    const cIndex = this.list[index].chapters_list.findIndex(f => f.id === chapter)
                    if(cIndex !== -1 && !this.list[index].chapters_list[cIndex].show) {
                        this.list[index].chapters_list[cIndex].show = true
                        this.list[index].chapters_list[cIndex].pages = pages
                    }
                }
            }
        },
        setChaptersListChild({ section }) {
            const index = this.list.findIndex(f => f.id === section)
            if(index !== -1) {
                if(!this.list[index].chapters_list?.length) {
                    this.list[index].show = true
                    this.$nextTick(() => {
                        if(this.$refs[`section_${section}`]?.[0])
                            this.$refs[`section_${section}`][0].openHandler()
                    })
                }
            }
        },
        clearActiveLinks() {
            this.actChapters = null
            this.asyncChaptersList = null
            this.asyncSection = null
            this.actPages = null
            this.initPageAct = null
            this.asyncPagesList = null
            this.searchAsyncChaptersList = null
        },
        openChapterSectionsLoc(id) {
            this.$nextTick(() => {
                const index = this.list.findIndex(f => f.id === id)
                if(index !== -1) {
                    this.list[index].show = true
                }
                if(!this.actSection || this.actSection !== id)
                    this.actSection = id
            })
        },
        openChapterSections(id) {
            this.$nextTick(() => {
                const index = this.list.findIndex(f => f.id === id)
                if(index !== -1) {
                    this.list[index].show = true
                }
                this.actSection = id
                this.asyncSection = id
            })
        },
        setActiveSection(id) {
            if(!this.actSection || this.actSection !== id)
                this.actSection = id
        },
        setActiveChapters(id) {
            if(!this.actChapters || this.actChapters !== id)
                this.actChapters = id
        },
        closeSection(id) {
            const index = this.list.findIndex(f => f.id === id)
            if(index !== -1) {
                this.list[index].show = false
            }
        },
        opnSection(id) {
            const index = this.list.findIndex(f => f.id === id)
            if(index !== -1) {
                this.list[index].show = true
            }
        },
        setChaptersList({ id, list }) {
            let cList = []

            if(list.length) {
                cList = list.map(item => {
                    return {
                        ...item,
                        show: this.asyncPagesList?.chapter === item.id,
                        pages: this.asyncPagesList?.chapter === item.id ? this.asyncPagesList.pages : [],
                        sections: [{id}]
                    }
                })
            }

            this.asyncChaptersList = {
                id,
                list: cList
            }
            const index = this.list.findIndex(f => f.id === id)
            if(index !== -1) {
                this.list[index].chapters_list = cList
            }
        },
        clearSectionsNotId(id) {
            this.list.forEach((item, index) => {
                if(item.show && item.id !== id) {
                    this.list[index].show = false
                    this.list[index].chapters_list = []
                }
                if(item.id !== id) {
                    this.$nextTick(() => {
                        if(this.$refs[`section_${item.id}`]?.[0]?.btnShow) {
                            this.$refs[`section_${item.id}`][0].hideShow()
                        }
                    })
                }
            })
        },
        openPages(id) {
            this.actPages = id
            this.asyncChaptersList = null
            this.asyncSection = null
            this.asyncPagesList = null
            this.initPageAct = null
            this.searchAsyncChaptersList = null
        },
        openChapters(id) {
            this.actChapters = id
            this.asyncChaptersList = null
            this.asyncSection = null
            this.initPageAct = null
            this.actPages = null
            this.searchAsyncChaptersList = null
        },
        openSections(id) {
            this.actChapters = null
            this.actSection = id
            this.asyncChaptersList = null
            this.asyncSection = null
            this.initPageAct = null
            this.actPages = null
            this.searchAsyncChaptersList = null

            const index = this.list.findIndex(f => f.id === id)
            if(index !== -1) {
                this.list[index].show = true
            }
        },
        async getSections() {
            try {
                this.loading = true
                const { data } = await this.$http.get('/wiki/sections/', {
                    params: {
                        page_size: 'all',
                        contractor: this.contractorId
                    }
                })
                if(data?.results?.length) {
                    this.list = data.results.map(item => {
                        return {
                            ...item,
                            show: this.asyncChaptersList?.id === item.id,
                            chapters_list: this.asyncChaptersList?.id === item.id ? this.asyncChaptersList.list : []
                        }
                    })
                }
            } catch(error) {
                errorHandler({ error, show: false })
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.aside_menu{
    border-right: 1px solid var(--border2);
    height: 100%;
    overflow-y: auto;
    padding: 15px;
    @media (min-width: 768px) {
        padding: 14px 20px;
    }
}

.aside_menu_home{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 0 14px;
    margin-bottom: 6px;
    cursor: pointer;
    font-weight: 600;
    border-bottom: 1px solid var(--border2);
    transition: color 0.2s ease;
    &:hover,
    &.active{
        color: var(--blue);
    }
    i{
        font-size: 18px;
        color: var(--gray);
    }
}
</style>
