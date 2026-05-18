<template>
    <div class="search_block">
        <div class="ico">
            <a-spin v-if="searchLoading" size="small" />
            <i v-else class="fi fi-rr-search"></i>
        </div>
        <a-select
            ref="searchSelect"
            show-search
            :value="searchValue"
            :placeholder="$t('support.companyWikiSearch')"
            style="width: 100%;"
            size="large"
            :default-active-first-option="false"
            :show-arrow="false"
            :filter-option="false"
            :not-found-content="null"
            :getPopupContainer="getPopupContainer"
            @search="searchWiki"
            @change="searchChange">
            <a-select-option
                v-for="sItem in searchList"
                :key="getOptionValue(sItem)"
                :value="getOptionValue(sItem)">
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
        autoFocus: {
            type: Boolean,
            default: false
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
    computed: {
        currentContractorId() {
            return this.$store.state.user.user?.current_contractor?.id || null
        }
    },
    mounted() {
        this.focusSearch()
    },
    methods: {
        focusSearch() {
            if(!this.autoFocus) return

            const applyFocus = () => {
                this.$refs.searchSelect?.focus?.()

                const input = this.$refs.searchSelect?.$el?.querySelector('input')
                if(input) {
                    input.focus()
                }
            }

            this.$nextTick(() => {
                applyFocus()
                setTimeout(() => {
                    applyFocus()
                }, 80)
            })
        },
        getOptionValue(item) {
            return `${item.model || 'item'}:${item.id}`
        },
        getPopupContainer(triggerNode) {
            return triggerNode?.closest('.s_main__content') || document.body
        },
        searchChange(value) {
            if(value && this.searchList.length) {
                const find = this.searchList.find(f => this.getOptionValue(f) === value)
                if(find)
                    this.selectSearchItem(find)
            }
        },
        selectSearchItem(find) {
            if(!find) return

            this.clearActiveLinks()

            let wikiType = ''
            if(find.model === 'wiki.WikiChapterModel')
                wikiType = 'chapters'
            if(find.model === 'wiki.WikiSectionModel')
                wikiType = 'sections'
            if(find.model === 'wiki.WikiPageModel')
                wikiType = 'pages'

            if(!wikiType) return

            this.searchValue = undefined
            this.searchList = []

            this.$router.push({
                name: 'company-wiki',
                params: {
                    wikiType,
                    wikiId: String(find.id)
                },
                query: this.$route.query
            })

            this.setSearch()
        },
        searchWiki(text) {
            clearTimeout(timer)

            timer = setTimeout(async () => {
                try {
                    this.searchLoading = true
                    const { data } = await this.$http.get('/wiki/pages/', {
                        params: {
                            text,
                            contractor: this.currentContractorId
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
    z-index: 15;
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
                    border: 0px;
                    box-shadow: none;
                }
                .ant-select-selection__rendered{
                    line-height: 50px;
                    margin-left: 15px;
                    margin-right: 40px;
                }
            }
        }
        .ant-select-dropdown{
            z-index: 20;
        }
    }
}
</style>
