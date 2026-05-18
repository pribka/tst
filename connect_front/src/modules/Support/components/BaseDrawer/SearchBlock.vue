<template>
    <div class="search_block" ref="searchBlock">
        <div class="ico">
            <a-spin v-if="searchLoading" size="small" />
            <i v-else class="fi fi-rr-search"></i>
        </div>
        <a-select
            show-search
            :value="searchValue"
            :placeholder="$t('support.base_search')"
            style="width: 100%;"
            size="large"
            :default-active-first-option="false"
            :show-arrow="false"
            :filter-option="false"
            :not-found-content="null"
            :getPopupContainer="getPopupContainer"
            @search="searchWiki"
            @change="searchChange">
            <a-select-option v-for="sItem in searchList" :key="sItem.id">
                {{ sItem.name }}
            </a-select-option>
        </a-select>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

let timer;
export default {
    props: {
        checkPageInit: {
            type: Function,
            default: () => {}
        },
        clearActiveLinks: {
            type: Function,
            default: () => {}
        },
        setSearch: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            searchLoading: false,
            searchList: [],
            searchValue: undefined,
        }
    },
    methods: {
        getPopupContainer() {
            return this.$refs.searchBlock
        },
        searchChange(value) {
            if(value && this.searchList.length) {
                const find = this.searchList.find(f => f.id === value)
                if(find) {
                    this.clearActiveLinks()

                    let type = ''
                    if(find.model === 'wiki.WikiChapterModel')
                        type = 'chapters'
                    if(find.model === 'wiki.WikiSectionModel')
                        type = 'sections'
                    if(find.model === 'wiki.WikiPageModel')
                        type = 'pages'

                    const query = {...this.$route.query}
                    if(query.chapters)
                        delete query.chapters
                    if(query.sections)
                        delete query.sections
                    if(query.pages)
                        delete query.pages

                    query[type] = find.id
                    this.$router.push({ query })

                    this.setSearch()
                }
            }
        },
        searchWiki(text) {
            clearTimeout(timer)

            timer = setTimeout(async () => {
                try {
                    this.searchLoading = true
                    const { data } = await this.$http.get('/wiki/pages/', {
                        params: {
                            text
                        }
                    })
                    if(data?.results?.length) {
                        this.searchList = data.results
                    } else {
                        this.searchList = []
                    }
                } catch(error) {
                    errorHandler({ error, show: false })
                } finally {
                    this.searchLoading = false
                }
            }, 500)
        },
    }
}
</script>

<style lang="scss" scoped>
.search_block{
    position: relative;
    .ico{
        position: absolute;
        height: 50px;
        right: 15px;
        top: 0px;
        z-index: 5;
        display: flex;
        align-items: center;
        font-size: 18px;
        color: var(--gray);
    }
    &::v-deep{
        .ant-select{
            &.ant-select-lg{
                .ant-select-selection--single{
                    height: 50px;
                }
                .ant-select-selection__rendered{
                    line-height: 50px;
                    margin-left: 15px;
                    margin-right: 40px;
                }
            }
        }
    }
}
</style>
