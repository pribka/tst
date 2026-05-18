<template>
    <div class="s_content h-full">
        <div class="drawer_body">
            <div
                v-if="isMobile"
                class="aside_fixed_menu"
                :class="asideVisible && 'active'">
                <div class="aside_fixed_menu__overlay" @click="asideVisible = false" />
                <div class="aside_fixed_menu__content">
                    <div class="menu_header truncate">
                        <h2 class="truncate">{{ $t('support.sections') }}</h2>
                        <a-button
                            type="ui"
                            ghost
                            flaticon
                            shape="circle"
                            icon="fi-rr-cross"
                            @click="asideVisible = false" />
                    </div>
                    <AsideMenu
                        ref="asideMenu"
                        :disabledSearch="disabledSearch"
                        :isSearch="isSearch" />
                    <div class="menu_footer">
                        <a-button
                            type="ui_ghost"
                            size="large"
                            block
                            @click="asideVisible = false">
                            {{ $t('close') }}
                        </a-button>
                    </div>
                </div>
            </div>
            <AsideMenu
                v-else
                ref="asideMenu"
                :disabledSearch="disabledSearch"
                :isSearch="isSearch" />
            <div class="s_main">
                <div class="s_main__content">
                    <div class="mb-5">
                        <SearchBlock
                            :setSearch="setSearch"
                            :clearActiveLinks="clearActiveLinks" />
                    </div>
                    <div v-if="loading" class="flex justify-center">
                        <a-spin />
                    </div>
                    <div v-if="!loading && empty" class="mt-10">
                        <a-empty :description="$t('support.pageNotFound')" />
                    </div>
                    <template v-if="!loading && activePage">
                        <Breadcrumb
                            :activePage="activePage"
                            :clearActiveLinks="clearActiveLinks"
                            :pageType="pageType" />
                        <div class="s_main__head">
                            <a-alert
                                v-if="activePage.has_kk === false"
                                class="mb-2"
                                :message="$t('support.content_doesnt_exist_on_kk')"
                                banner />
                            <h2>{{ activePage.name }}</h2>
                            <div v-if="activePage.updated_at" class="update_date flex items-center">
                                <div v-if="!activePage.is_active" class="mr-2">
                                    <a-tag color="orange">
                                        {{ $t('support.archive') }}
                                    </a-tag>
                                </div>
                                {{ $t('support.lastUpdate') }}: {{ $moment(activePage.updated_at).format('DD MMM YYYY г.') }}
                            </div>
                            <template v-if="canUpdate || canDelete">
                                <div
                                    v-if="pageType === 'chapters' || pageType === 'pages' || pageType === 'sections'"
                                    :class="!isMobile && 'flex items-center'"
                                    class="mt-3">
                                    <a-button v-if="canUpdate" type="flat_primary" :block="isMobile" icon="fi-rr-edit" flaticon @click="editCurrent()">
                                        {{ $t('edit') }}
                                    </a-button>
                                    <a-button v-if="canDelete" type="flat_danger" :block="isMobile" icon="fi-rr-trash" flaticon :class="isMobile ? 'mt-1' : 'ml-2'" @click="deleteCurrent()">
                                        {{ $t('remove') }}
                                    </a-button>
                                    <a-tag :class="isMobile ? 'mt-1' : 'ml-2'" size="large" :block="isMobile" color="green">
                                        {{ activePage.show_on_main_page ? $t('support.displayOnMain') : $t('support.notDisplayedOnMain') }}
                                    </a-tag>
                                </div>
                            </template>
                        </div>
                        <TextViewer :body="activePage.random_html" class="main_text" />
                        <div class="actions_buttons" :class="isMobile && 'w-full'">
                            <div :class="isMobile ? 'grid gap-2 grid-cols-2 w-full' : 'flex items-center'">
                                <a-spin v-if="voteLoading" size="small" />
                                <template v-else>
                                    <a-button
                                        type="green"
                                        :loading="likeLoader"
                                        :block="isMobile"
                                        flaticon
                                        icon="fi-rr-social-network"
                                        @click="setVote('like')">
                                        {{ $t('support.thankYouHelped') }} <template v-if="votes.likes_count && votes.likes_count > 0">({{ votes.likes_count }})</template>
                                    </a-button>
                                    <a-button
                                        type="flat_danger"
                                        flaticon
                                        :block="isMobile"
                                        :loading="dislikeLoader"
                                        icon="fi-rr-hand"
                                        @click="setVote('dislike')">
                                        {{ $t('support.didNotHelp') }} <template v-if="votes.dislikes_count && votes.dislikes_count > 0">({{ votes.dislikes_count }})</template>
                                    </a-button>
                                </template>
                            </div>
                        </div>
                        <div v-if="childChapters.length" class="other_s">
                            <h3>{{ $t('support.otherEntries') }}</h3>
                            <router-link
                                v-for="item in childChapters"
                                :key="item.id"
                                tag="div"
                                :to="getRoutePayload(item.type, item.id)"
                                class="other_s__item"
                                @click.native="openLinkOther(item)">
                                <i class="fi fi-rr-angle-circle-right"></i>
                                {{ item.name }}
                            </router-link>
                        </div>
                        <div class="mt-7 comment_block">
                            <h3>{{ $t('support.comments') }}</h3>
                            <vue2CommentsComponent
                                :related_object="activePage.id"
                                :showFileUpload="false"
                                :showEmoji="false"
                                :showUsers="false"
                                :addTaskCheck="false"
                                :shareCheck="false"
                                model="wiki" />
                        </div>
                    </template>
                </div>
            </div>
        </div>
        <template v-if="user && user.is_staff">
            <AddChapters :fUpdChapterList="fUpdChapterList" />
            <AddSection :fUpdChapterList="fUpdChapterList" />
            <AddPage :fUpdChapterList="fUpdChapterList" />
        </template>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'

export default {
    components: {
        AsideMenu: () => import('./AsideMenu/index.vue'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        Breadcrumb: () => import('./Breadcrumb.vue'),
        SearchBlock: () => import('./SearchBlock.vue'),
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent'),
        AddChapters: () => import('./AddChapters.vue'),
        AddSection: () => import('./AddSection.vue'),
        AddPage: () => import('./AddPage.vue')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        user() {
            return this.$store.state.user.user
        },
        canUpdate() {
            return this.$store.getters['supportWiki/canUpdate']
        },
        canDelete() {
            return this.$store.getters['supportWiki/canDelete']
        },
        routeKey() {
            return `${this.$route.params?.wikiType || ''}:${this.$route.params?.wikiId || ''}`
        },
        routeWikiType() {
            return this.$route.params?.wikiType || ''
        },
        routeWikiId() {
            return this.$route.params?.wikiId || ''
        }
    },
    data() {
        return {
            asideVisible: false,
            loading: false,
            activePage: null,
            pageType: '',
            childChapters: [],
            voteLoading: false,
            votes: {},
            pageInit: false,
            isSearch: false,
            likeLoader: false,
            dislikeLoader: false,
            empty: false
        }
    },
    watch: {
        routeKey: {
            handler() {
                if(this.isMobile && this.asideVisible) {
                    this.asideVisible = false
                }
                this.syncByRoute()
            }
        }
    },
    created() {
        eventBus.$on('support_open_mobile_aside', this.openMobileAside)
    },
    mounted() {
        this.syncByRoute()
    },
    beforeDestroy() {
        eventBus.$off('support_open_mobile_aside', this.openMobileAside)
    },
    methods: {
        openMobileAside() {
            this.asideVisible = true
        },
        getRoutePayload(wikiType, wikiId) {
            return {
                name: 'company-wiki',
                params: {
                    wikiType,
                    wikiId: String(wikiId)
                },
                query: this.$route.query
            }
        },
        syncByRoute() {
            if(!this.routeWikiType || !this.routeWikiId)
                return

            if(this.routeWikiType === 'sections') {
                this.getSection()
            }
            if(this.routeWikiType === 'chapters') {
                this.getChapters()
            }
            if(this.routeWikiType === 'pages') {
                this.getPage(true)
            }
        },
        editSection() {
            eventBus.$emit('open_support_page_section_drawer', this.activePage)
        },
        editChapter() {
            eventBus.$emit('open_support_page_chapter_drawer', this.activePage)
        },
        editPage() {
            eventBus.$emit('open_support_page_page_drawer', this.activePage)
        },
        editCurrent() {
            if(this.pageType === 'sections')
                this.editSection()
            if(this.pageType === 'chapters')
                this.editChapter()
            if(this.pageType === 'pages')
                this.editPage()
        },
        deleteCurrent() {
            let title = ''

            if(this.pageType === 'sections')
                title = this.$t('support.removeCategoryConfirm')
            if(this.pageType === 'chapters')
                title = this.$t('support.removeSubsectionConfirm')
            if(this.pageType === 'pages')
                title = this.$t('support.removeArticleConfirm')

            this.$confirm({
                title,
                content: '',
                okText: this.$t('remove'),
                okType: 'danger',
                closable: true,
                maskClosable: true,
                cancelText: this.$t('cancel'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.activePage.id, is_active: false }])
                            .then(() => {
                                if(this.pageType === 'sections')
                                    this.$message.success(this.$t('support.categoryDeleted'))
                                if(this.pageType === 'chapters')
                                    this.$message.success(this.$t('support.subsectionDeleted'))
                                if(this.pageType === 'pages')
                                    this.$message.success(this.$t('support.articleDeleted'))

                                this.$router.push({ name: 'company-wiki', query: this.$route.query })
                                this.fUpdChapterList()
                                resolve()
                            })
                            .catch(error => {
                                errorHandler({error})
                                reject(error)
                            })
                    })
                }
            })
        },
        fUpdChapterList() {
            if(this.pageType === 'chapters') {
                this.getChapters()
            }
            if(this.pageType === 'sections') {
                this.getSection()
            }
            if(this.pageType === 'pages') {
                this.getPage()
            }
            this.$nextTick(() => {
                this.$refs.asideMenu.reloadSections()
            })
        },
        disabledSearch() {
            this.isSearch = false
        },
        setSearch() {
            this.isSearch = true
        },
        async setVote(choice) {
            try {
                let boolChoice,
                    fieldToVote,
                    oppositeFieldToVote
                if (choice === 'like') {
                    fieldToVote = 'likes_count'
                    oppositeFieldToVote = 'dislikes_count'
                    boolChoice = true
                    this.likeLoader = true
                } else if (choice === 'dislike') {
                    fieldToVote = 'dislikes_count'
                    oppositeFieldToVote = 'likes_count'
                    boolChoice = false
                    this.dislikeLoader = true
                }
                const payload = {
                    vote: boolChoice
                }
                await this.$http.post(`/vote/${this.activePage.id}/`, payload)
                if(this.votes.my_vote !== null) {
                    if(this.votes.my_vote === boolChoice) {
                        this.votes[fieldToVote] += -1
                        this.votes.my_vote = null
                    } else {
                        this.votes[oppositeFieldToVote] += -1
                        this.votes[fieldToVote] += 1
                        this.votes.my_vote = boolChoice
                    }
                } else {
                    this.votes[fieldToVote] += 1
                    this.votes.my_vote = boolChoice
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                if (choice === 'like') {
                    this.likeLoader = false
                }
                if (choice === 'dislike') {
                    this.dislikeLoader = false
                }
            }
        },
        async getVotes() {
            try {
                this.voteLoading = true
                const { data } = await this.$http.get(`/vote/${this.activePage.id}/`)
                if(data) {
                    this.votes = data
                }
            } catch(error) {
                errorHandler({error, show: false})
            } finally {
                this.voteLoading = false
            }
        },
        clearActiveLinks() {
            this.$refs.asideMenu.clearActiveLinks()
        },
        checkPageInit(page) {
            this.pageInit = true
            this.$nextTick(() => {
                this.$refs.asideMenu.setPagesList({
                    section: page.section,
                    chapter: page.chapter,
                    pages: this.childChapters
                })
            })
        },
        openLinkOther(page) {
            if(page.type === 'pages') {
                this.checkPageInit(page)
                this.$nextTick(() => {
                    this.$refs.asideMenu.setChaptersListChild({
                        section: page.section
                    })
                })
            }
            if(page.type === 'chapters') {
                this.$nextTick(() => {
                    this.$refs.asideMenu.setChaptersListChild({
                        section: page.section
                    })
                })
            }
            this.clearActiveLinks()
            this.$router.push(this.getRoutePayload(page.type, page.id))
        },
        redirectToWikiHome() {
            this.$router.push({
                name: 'company-wiki',
                query: this.$route.query
            })
        },
        async getSection() {
            try {
                this.empty = false
                this.childChapters = []
                this.loading = true
                const { data } = await this.$http.get(`/wiki/sections/${this.routeWikiId}/`)
                if(data) {
                    this.pageType = 'sections'
                    this.activePage = data
                    this.$refs.asideMenu.setChaptersList({
                        id: data.id,
                        list: data.chapters
                    })
                    this.$refs.asideMenu.cleatAllActiveChapters()
                    this.$refs.asideMenu.setActiveSection(data.id)
                    this.$refs.asideMenu.clearSectionsNotId(data.id)
                    this.childChapters = data.chapters.map(item => {
                        return {
                            ...item,
                            type: 'chapters',
                            section: this.routeWikiId
                        }
                    })
                    this.getVotes()
                }
            } catch(error) {
                errorHandler({error, show: false})
                this.redirectToWikiHome()
            } finally {
                this.loading = false
            }
        },
        async getChapters() {
            try {
                this.empty = false
                this.childChapters = []
                this.loading = true
                const { data } = await this.$http.get(`/wiki/chapters/${this.routeWikiId}/`)
                if(data) {
                    this.pageType = 'chapters'
                    this.activePage = data
                    this.$refs.asideMenu.closeAllPages()
                    this.$refs.asideMenu.setActiveChapters(data.id)

                    this.childChapters = data.pages.map(item => {
                        return {
                            ...item,
                            chapter: data.id,
                            section: data.sections?.length ? data.sections[0].id : null,
                            type: 'pages'
                        }
                    })

                    if(data.sections?.length) {
                        data.sections.forEach(sec => {
                            this.$refs.asideMenu.openChapterSections(sec.id)
                        })
                    }

                    if(data.pages?.length) {
                        this.$refs.asideMenu.setPagesList({
                            section: data.sections?.length ? data.sections[0].id : null,
                            chapter: data.id,
                            pages: data.pages
                        })
                    }
                    this.getVotes()
                }
            } catch(error) {
                errorHandler({error, show: false})
                this.redirectToWikiHome()
            } finally {
                this.loading = false
            }
        },
        async getPage(init = false) {
            try {
                this.empty = false
                this.childChapters = []
                this.loading = true
                const { data } = await this.$http.get(`/wiki/pages/${this.routeWikiId}/`)
                if(data) {
                    this.pageType = 'pages'
                    this.activePage = data

                    if(data.chapter?.length) {
                        this.$refs.asideMenu.setActiveChapters(data.chapter[0].id)
                    }
                    if(data.section?.length) {
                        data.section.forEach(sec => {
                            this.$refs.asideMenu.openChapterSections(sec.id)
                        })
                    }
                    if(this.pageInit || init || this.isSearch) {
                        if(data.chapter?.length) {
                            this.$refs.asideMenu.initPage({
                                chapter: data.chapter[0].id,
                                page: data.id
                            })
                            this.pageInit = false
                        }
                    }
                    this.getVotes()
                }
            } catch(error) {
                errorHandler({error, show: false})
                this.redirectToWikiHome()
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.actions_buttons{
    display: flex;
    align-items: center;
    margin-top: 20px;
    justify-content: space-between;
    &::v-deep{
        .ant-btn{
            border-radius: 20px;
            @media (min-width: 768px) {
                &:not(:last-child){
                    margin-right: 10px;
                }
            }
        }
    }
}
.s_content{
    height: 100%;
}
.drawer_body{
    height: 100%;
    position: relative;
    @media (min-width: 768px) {
        grid-template-columns: 320px 1fr;
        display: grid;
    }
    .float_add{
        --safe-area-inset-bottom: env(safe-area-inset-bottom);
        bottom: calc(20px + var(--safe-area-inset-bottom));
    }
    .s_main{
        height: 100%;
        overflow-y: auto;
        padding: 20px 15px 50px 15px;
        @media (min-width: 768px) {
            padding: 20px 20px 50px 20px;
        }
        &__content{
            max-width: 900px;
            margin: 0 auto;
        }
        .main_text{
            font-size: 16px;
            line-height: 26px;
        }
        .other_s,
        .comment_block{
            h3{
                font-weight: 600;
                margin-bottom: 15px;
                font-size: 18px;
            }
        }
        .other_s{
            margin-top: 30px;
            font-size: 16px;
            &__item{
                color: var(--blue);
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                display: flex;
                align-items: center;
                i{
                    margin-right: 8px;
                }
                &:not(:last-child){
                    margin-bottom: 10px;
                }
                &:hover{
                    opacity: 0.6;
                }
            }
        }
        .s_main__head{
            border-bottom: 1px solid var(--border2);
            margin-bottom: 20px;
            padding-bottom: 20px;
            h2{
                font-size: 22px;
                font-weight: 600;
                margin: 0px;
                word-break: break-word;
                @media (min-width: 768px) {
                    font-size: 28px;
                }
            }
            .update_date{
                margin-top: 5px;
                color: var(--gray);
                font-weight: 300;
            }
        }
    }
    .aside_fixed_menu{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        width: 100%;
        height: 100%;
        z-index: 999999;
        display: none;
        .menu_header{
            border-bottom: 1px solid var(--border2);
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 15px;
            h2{
                font-weight: 600;
                font-size: 16px;
            }
        }
        .menu_footer{
            border-top: 1px solid var(--border2);
            min-height: 72px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 12px 15px;
        }
        &.active{
            display: block;
        }
        &__overlay{
            background: #000000;
            position: absolute;
            top: 0;
            right: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
            z-index: 90;
            opacity: 0.5;
        }
        &__content{
            position: fixed;
            top: 0px;
            right: 0;
            width: 100%;
            left: 0;
            height: 100%;
            z-index: 110;
            display: flex;
            flex-direction: column;
            background: #ffffff;
            &::v-deep{
                .aside_menu{
                    flex-grow: 1;
                    background: #ffffff;
                }
            }
        }
    }
}
</style>
