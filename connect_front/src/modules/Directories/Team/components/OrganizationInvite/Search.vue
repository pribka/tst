<template>
    <div>
        <div class="drawer_search">
            <a-input-search 
                :loading="loading"
                v-model="search"
                @input="onSearch"
                :placeholder="$t('team.search_by_identifier')" />
        </div>
        <div class="drawer_list">
            <a-empty v-if="empty && !loading" class="mt-6 mb-2">
                <span slot="description">{{ $t('team.search_organization_help') }}</span>
            </a-empty>
            <a-radio-group :value="selected" class="w-full">
                <div class="org_list">
                    <div v-for="item in list" :key="item.id" class="item flex items-center justify-between" @click="selectItem(item.id)">
                        <div class="flex items-center">
                            <div :key="item.logo" class="pr-2">
                                <a-avatar 
                                    :size="30"
                                    :src="item.logo"
                                    icon="picture" />
                            </div>
                            <span>{{ item.name }}</span>
                        </div>
                        <div>
                            <a-radio :value="item.id" />
                        </div>
                    </div>
                </div>
            </a-radio-group>
            <infinite-loading ref="userInfinite" @infinite="getList" v-bind:distance="10">
                <div slot="spinner"><a-spin /></div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
    </div>
</template>

<script>
let timer;
export default {
    name: "OrganizationInviteSearchDrawer",
    props: {
        setSelected: {
            type: Function,
            default: () => {}
        },
        selected: {
            type: [String, Number],
            default: ''
        }
    },
    components: {
        InfiniteLoading: () => import('vue-infinite-loading')
    },
    data() {
        return {
            loading: false,
            page: 0,
            search: '',
            list: [],
            scrollStatus: true,
            empty: true
        }
    },
    methods: {
        clearSearch() {
            this.search = ''
        },
        clearList() {
            this.scrollStatus = true
            this.page = 0
            this.list = []
            this.empty = true
            this.setSelected('')
        },
        selectItem(id) {
            if(this.selected === id)
                this.setSelected('')
            else
                this.setSelected(id)
        },
        onSearch() {
            clearTimeout(timer)
            timer = setTimeout(() => {
                this.clearList()
                this.getList()
            }, 800)
        },
        async getList($state = null) {
            if(!this.loading && this.scrollStatus && this.search.length) {
                try {
                    this.loading = true
                    this.page = this.page+1
                    let params = {
                        page_size: 15,
                        page: this.page,
                        id: this.search
                    }

                    const { data } = await this.$http.get('/catalogs/contractors/get_by_id/', { params })
                    if(data && data.results.length) {
                        this.empty = false
                        this.list = this.list.concat(data.results)
                    } else {
                        this.empty = true
                    }
                    if(!data.next) {
                        if($state)
                            $state.complete()
                        this.scrollStatus = false
                    } else {
                        if($state)
                            $state.loaded()
                    }
                } catch(e) {
                    console.log(e)
                } finally {
                    this.loading = false
                }
            } else {
                if($state)
                    $state.complete()
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.org_list{
    .item{
        cursor: pointer;
        padding: 10px;
        &:not(:last-child){
            border-bottom: 1px solid #e8e8e8;
        }
    }
}
.drawer_search{
    &::v-deep{
        .ant-input-search{
            .ant-input{
                border-radius: 0px;
                border-left: 0px;
                border-right: 0px;
                border-top: 0px;
                height: 40px;
            }
        }
    }
}
</style>