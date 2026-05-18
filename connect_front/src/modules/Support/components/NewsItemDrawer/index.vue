<template>
    <DrawerTemplate
        :width="isMobile ? '100%' : 700"
        class="news_item_drawer"
        v-model="visible"
        :zIndex="10000"
        @afterVisibleChange="afterVisibleChange"
        @close="visible = false">
        <template v-if="news" #title>
            <div class="w-full flex items-center justify-between truncate">
                <h1 class="truncate">
                    <span v-if="news.is_important" class="important">
                        <img src="../../assets/img/fire.svg" />
                    </span>
                    <span class="truncate">{{ news.title }}</span>
                </h1>
                <div class="ml-2 gap-2 flex items-center">
                    <a-button
                        v-if="canEdit"
                        type="ui"
                        ghost
                        v-tippy
                        :content="$t('edit')"
                        icon="fi-rr-edit"
                        shape="circle"
                        flaticon
                        @click="openEditDrawer" />
                    <a-button
                        v-if="canDelete"
                        type="ui"
                        ghost
                        v-tippy
                        :content="$t('remove')"
                        shape="circle"
                        @click="deleteNews">
                        <i class="fi fi-rr-trash"></i>
                    </a-button>
                </div>
            </div>
        </template>
        <div v-if="loading" class="loader_wrap">
            <a-spin class="w-full" />
        </div>
        <template v-else-if="news">
            <CreateDrawer
                ref="editDrawer"
                :resetList="refreshNewsLists"
                :afterSubmit="onNewsUpdated" />
            <div class="news_meta mb-2">
                <div class="created_data">
                    <i class="fi fi-rr-calendar mr-1" /> {{ $moment(news.created_at).format('DD MMM YYYY г.') }}
                </div>
                <div v-if="news.work_groups && news.work_groups.length" class="related_groups">
                    <div
                        v-for="group in news.work_groups"
                        :key="group.id"
                        class="related_groups__item"
                        @click="openRelatedWorkgroup(group)">
                        <a-avatar
                            :size="18"
                            icon="fi-rr-users-alt"
                            flaticon
                            :src="workgroupLogoPath(group)" />
                        <div class="related_groups__name">
                            {{ group.name }}
                        </div>
                    </div>
                </div>
            </div>

            <TextViewer :body="news.content" class="main_text" />

            <div class="flex items-center gap-1 mt-2 like_actions">
                <div class="flex items-center">
                    <a-button
                        type="ui_ghost"
                        flaticon
                        shape="circle"
                        icon="fi-rr-social-network"
                        :class="{ 'blue_color': myVote === 'like'}"
                        @click="vote('like')" />
                    <div v-if="taskVote.likes_count" class="vote_count">
                        {{ taskVote.likes_count }}
                    </div>
                </div>
                <div class="flex items-center">
                    <a-button
                        type="ui_ghost"
                        class="ml-1"
                        flaticon
                        shape="circle"
                        icon="fi-rr-hand"
                        :class="{ 'text_red': myVote === 'dislike'}"
                        @click="vote('dislike')" />
                    <div v-if="taskVote.dislikes_count" class="vote_count">
                        {{ taskVote.dislikes_count }}
                    </div>
                </div>
            </div>

            <div class="comments_block mt-7">
                <h3>{{ $t('support.comments') }}</h3>
                <Comments
                    class="w-full"
                    :related_object="news.id"
                    model="news"
                    :extendDrawerZIndex="1010" />
            </div>
        </template>
        <a-empty v-else />
        <template #footer>
            <a-button type="ui_ghost" size="large" block @click="visible = false">
                {{ $t('close') }}
            </a-button>
        </template>
    </DrawerTemplate>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        DrawerTemplate: () => import('@/components/DrawerTemplate.vue'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        CreateDrawer: () => import('../NewsDrawer/CreateDrawer.vue'),
        Comments: () => import('@apps/vue2CommentsComponent')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        canEdit() {
            return !!this.action?.edit?.availability
        },
        canDelete() {
            return !!this.action?.delete?.availability
        },
        myVote() {
            if(this.taskVote.my_vote === null)
                return null
            if(this.taskVote.my_vote)
                return 'like'
            return 'dislike'
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            voteLoading: false,
            news: null,
            action: null,
            taskVote: {
                likes_count: 0,
                dislikes_count: 0,
                my_vote: null
            },
            loadedNewsId: null
        }
    },
    watch: {
        '$route.query.newsItem': {
            immediate: true,
            handler(val) {
                if(val && !this.visible)
                    this.visible = true
                if(!val && this.visible)
                    this.visible = false
                if(val && this.loadedNewsId !== val)
                    this.fetchNews(val)
            }
        }
    },
    methods: {
        afterVisibleChange(vis) {
            if(!vis) {
                this.loadedNewsId = null
                this.action = null
                const query = {...this.$route.query}
                if(query.newsItem) {
                    delete query.newsItem
                    this.$router.push({ query })
                }
            }
        },
        syncVote() {
            if(!this.news?.id)
                return
            eventBus.$emit('support_news_vote_changed', {
                id: this.news.id,
                vote: {...this.taskVote}
            })
        },
        async fetchNews(id) {
            if(!id)
                return
            try {
                this.loading = true
                this.action = null
                const { data: newsData } = await this.$http.get(`/news/news/${id}/`)
                this.news = newsData
                this.loadedNewsId = id
                this.getNewsActions(id)
                this.getVote(id)
            } catch(error) {
                errorHandler({ error, show: false })
                this.news = null
                this.action = null
                this.loadedNewsId = null
            } finally {
                this.loading = false
            }
        },
        async getNewsActions(id) {
            if(!id)
                return
            try {
                const { data } = await this.$http.get(`/news/news/${id}/action_info/`)
                this.action = data?.actions || null
            } catch(error) {
                this.action = null
                errorHandler({ error, show: false })
            }
        },
        async getVote(id) {
            try {
                this.voteLoading = true
                const { data } = await this.$http.get(`vote/${id}/`)
                this.taskVote = data
                this.syncVote()
            } catch(error) {
                errorHandler({ error, show: false })
            } finally {
                this.voteLoading = false
            }
        },
        refreshNewsLists() {
            eventBus.$emit('support_news_list_reload')
        },
        onNewsUpdated(news = null) {
            this.refreshNewsLists()
            if(news?.id) {
                this.fetchNews(news.id)
            } else if(this.news?.id) {
                this.fetchNews(this.news.id)
            }
        },
        openEditDrawer() {
            if(!this.news?.id)
                return
            this.$nextTick(() => {
                this.$refs.editDrawer.openDrawer(this.news)
            })
        },
        openRelatedWorkgroup(group) {
            if(!group?.id)
                return
            const query = { ...this.$route.query }
            delete query.newsItem
            delete query.viewProject
            delete query.viewGroup
            if(group.is_project)
                query.viewProject = group.id
            else
                query.viewGroup = group.id
            this.$router.push({ query })
        },
        workgroupLogoPath(group) {
            return group?.workgroup_logo?.path || undefined
        },
        deleteNewsRequest(id) {
            return this.$http.post('/table_actions/update_is_active/', [{ id, is_active: false }])
        },
        deleteNews() {
            if(!this.news?.id)
                return
            this.$confirm({
                title: this.$t('support.warning'),
                content: this.$t('support.confirmDeleteNews'),
                zIndex: 1200,
                cancelText: this.$t('cancel'),
                okText: this.$t('delete'),
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.deleteNewsRequest(this.news.id)
                            .then(() => {
                                this.$message.success(this.$t('support.newsDeleted'))
                                this.refreshNewsLists()
                                eventBus.$emit('read_news_count')
                                this.visible = false
                                resolve()
                            })
                            .catch((error) => {
                                errorHandler({ error })
                                reject()
                            })
                    })
                },
                onCancel() {}
            })
        },
        async vote(choice) {
            if(!this.news?.id)
                return
            let boolChoice,
                fieldToVote,
                oppositeFieldToVote
            if (choice === 'like') {
                fieldToVote = 'likes_count'
                oppositeFieldToVote = 'dislikes_count'
                boolChoice = true
            } else if (choice === 'dislike') {
                fieldToVote = 'dislikes_count'
                oppositeFieldToVote = 'likes_count'
                boolChoice = false
            }

            await this.$http.post(`vote/${this.news.id}/`, { vote: boolChoice })
                .then(() => {
                    if(this.taskVote.my_vote !== null) {
                        if(this.taskVote.my_vote === boolChoice) {
                            this.taskVote[fieldToVote] += -1
                            this.taskVote.my_vote = null
                        } else {
                            this.taskVote[oppositeFieldToVote] += -1
                            this.taskVote[fieldToVote] += 1
                            this.taskVote.my_vote = boolChoice
                        }
                    } else {
                        this.taskVote[fieldToVote] += 1
                        this.taskVote.my_vote = boolChoice
                    }
                    this.syncVote()
                })
                .catch(error => errorHandler({ error }))
        }
    }
}
</script>

<style lang="scss" scoped>
.vote_count{
    color: #888888;
}
.news_meta{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
}
.like_actions{
    &::v-deep{
        .ant-btn{
            border-radius: 50%;
        }
    }
}
h1{
    font-weight: 600;
    font-size: 16px;
    margin-bottom: 0px;
    line-height: 22px;
    display: flex;
    align-items: center;
    word-break: break-word;
    .important{
        margin-right: 6px;
        min-width: 15px;
        @media (min-width: 768px) {
            min-width: 20px;
        }
        img{
            max-width: 15px;
            @media (min-width: 768px) {
                max-width: 20px;
            }
        }
    }
}
.main_text{
    &::v-deep{
        font-size: 15px;
        line-height: 24px;
        color: var(--text);
        p{
            span{
                background: transparent !important;
            }
        }
    }
}
.comments_block{
    width: 100%;
    h3{
        font-size: 16px;
        line-height: 20px;
        font-weight: 500;
        margin-bottom: 12px;
    }
}
.created_data{
    opacity: 0.6;
    white-space: nowrap;
}
.related_groups{
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    &__item{
        display: flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        max-width: 220px;
        min-width: 0;
    }
    &__name{
        font-size: 14px;
        line-height: 20px;
        color: var(--blue);
        min-width: 0;
        max-width: 190px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
}
</style>
