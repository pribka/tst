<template>
    <div class="b_init">
        <div class="content_header">
            <div class="wrap">
                <h1>{{ $t('support.centerTitle', { app_name: appName }) }}</h1>
                <SearchBlock />
            </div>
            <div class="close_header" @click="drawerClose()">
                <i class="fi fi-rr-cross-small" />
            </div>
        </div>
        <div class="content_body">
            <div v-if="user && user.is_staff" class="flex items-center justify-center mb-5">
                <a-button type="ui" class="mr-2" @click="addSection()">
                    {{ $t('support.addSection') }}
                </a-button>
                <a-button type="ui" class="mr-2" @click="addChapter()">
                    {{ $t('support.addChapter') }}
                </a-button>
                <a-button type="ui" @click="addPage()">
                    {{ $t('support.addPage') }}
                </a-button>
            </div>
            <div class="wrap">
                <div v-for="item in list.results" :key="item.id" class="b_item">
                    <h2 @click="openSections(item.id)">{{ item.name }}</h2>
                    <div class="chapters_list">
                        <div 
                            v-for="character in item.chapters" 
                            :key="character.id"
                            class="chapters_list__item"
                            @click="openChapters(character.id)">
                            <div class="ico"><i class="fi fi-rr-document"></i></div> {{ character.name }}
                        </div>
                    </div>
                    <div 
                        v-if="item.has_more"
                        class="more"
                        @click="openSections(item.id)">
                        <div class="ico"></div>
                        {{ $t('support.viewAllPages') }}
                    </div>
                </div>
            </div>
            <infinite-loading 
                ref="support_infinity"
                @infinite="getSections"
                v-bind:distance="10">
                <div 
                    slot="spinner"
                    class="flex justify-center">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
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
        InfiniteLoading: () => import('vue-infinite-loading'),
        SearchBlock: () => import('./SearchBlock.vue'),
        AddChapters: () => import('./AddChapters.vue'),
        AddSection: () => import('./AddSection.vue'),
        AddPage: () => import('./AddPage.vue')
    },
    props: {
        drawerClose: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        user() {
            return this.$store.state.user.user
        }
    },
    data() {
        return {
            appName: process.env.VUE_APP_NAME || 'Gos24.КОННЕКТ',
            page: 0,
            visible: false,
            loading: false,
            empty: false,
            list: {
                results: [],
                next: true
            }
        }
    },
    methods: {
        fUpdChapterList() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true
                }
                this.$refs['support_infinity'].stateChanger.reset()
            })
        },
        addSection() {
            eventBus.$emit('open_section_drawer')
        },
        addChapter() {
            eventBus.$emit('open_chapter_drawer')
        },
        addPage() {
            eventBus.$emit('open_page_drawer')
        },
        openSections(id) {
            const query = {...this.$route.query}
            query.sections = id
            if(query.chapters)
                delete query.chapters
            if(query.pages)
                delete query.pages
            this.$router.push({ query })
        },
        openChapters(id) {
            const query = {...this.$route.query}
            query.chapters = id
            if(query.sections)
                delete query.sections
            if(query.pages)
                delete query.pages
            this.$router.push({ query })
        },
        async getSections($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/wiki/sections/', {
                        params: {
                            page: this.page,
                            page_size: 15
                        }
                    })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data?.results?.length)
                        this.list.results = this.list.results.concat(data.results)

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }
                        
                    if(this.list.next)
                        $state.loaded()
                    else
                        $state.complete()
                } catch(error) {
                    errorHandler({error, show: false})
                } finally {
                    this.loading = false
                }
            }
        }
    },
    created() {
        this.visible = true
    },
    beforeDestroy() {
        this.visible = false
    }
}
</script>

<style lang="scss" scoped>
.b_item{
    .more{
        color: var(--gray);
        margin-top: 15px;
        display: flex;
        align-items: center;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover{
            color: var(--blue);
        }
        .ico{
            margin-right: 10px;
            width: 19px;
            height: 19px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
    }
    h2{
        font-weight: bold;
        font-size: 22px;
        cursor: pointer;
        margin-bottom: 10px;
        color: #000000;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover{
            color: var(--blue);
        }
    }
    .chapters_list{
        &__item{
            font-size: 16px;
            display: flex;
            align-items: center;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            &:hover{
                color: var(--blue);
            }
            .ico{
                margin-right: 10px;
                width: 19px;
                height: 19px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--gray);
            }
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
    }
}
.b_init{
    height: 100%;
    display: flex;
    flex-direction: column;
}
.content_header{
    background: var(--blue);
    padding: 50px 15px 20px 15px;
    position: relative;
    background-image: url('../../assets/img/wiki_bg.png');
    background-position: center;
    background-repeat: no-repeat;
    background-size: cover;
    @media (min-width: 768px) {
        padding: 40px 15px;
    }
    .close_header{
        position: absolute;
        top: 15px;
        right: 15px;
        color: #ffffff;
        font-size: 20px;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        &:hover{
            opacity: 0.6;
        }
    }
    .wrap{
        max-width: 800px;
        margin: 0 auto;
        h1{
            font-size: 18px;
            margin-bottom: 10px;
            color: #ffffff;
            font-weight: bold;
            @media (min-width: 768px) {
                font-size: 28px;
                margin-left: 10px;
            }
        }
    }
}
.content_body{
    flex-grow: 1;
    padding: 30px 15px;
    @media (min-width: 768px) {
        overflow-y: auto;
        padding: 40px 15px;
    }
    .b_item{
        @media (max-width: 768px) {
            &:not(:last-child){
                margin-bottom: 20px;
            }
        }
    }
    .wrap{
        @media (min-width: 768px) {
            max-width: 800px;
            margin: 0 auto;
            display: grid;
            gap: 40px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
    }
}
</style>