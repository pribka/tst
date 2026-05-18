<template>
    <div class="b_init">
        <div class="content_header">
            <div class="search_wrap">
                <SearchBlock autoFocus />
                <div class="search_subtitle">
                    <span>{{ $t('support.companyWikiSubtitleWithOrganization') }}:</span>
                    <a-spin size="small" :spinning="orgLoading">
                        <SupportOrgSelect
                            v-model="selectedOrg"
                            :selectProject="selectOrg">
                            <template #default="{ value, open }">
                                <button
                                    type="button"
                                    class="org_switcher"
                                    :title="value ? value.name : $t('Organization')"
                                    @click="handleOrgSwitcherClick(open, $event)">
                                    <a-avatar
                                        :size="24"
                                        icon="team"
                                        :src="orgLogoPath(value)" />
                                    <span class="org_switcher__name">
                                        {{ value?.name || $t('Organization') }}
                                    </span>
                                </button>
                            </template>
                        </SupportOrgSelect>
                    </a-spin>
                </div>
            </div>
        </div>
        <div class="content_body">
            <div class="wrap">
                <div v-for="item in list.results" :key="item.id" class="b_item cursor-pointer" @click="openSection(item.id)">
                    <div class="item_head">
                        <h2>
                            {{ item.name }}
                        </h2>
                        <a-tag v-if="item.public === false" color="orange" class="private_tag">
                            <i class="fi fi-rr-lock" />
                            {{ $t('support.private') }}
                        </a-tag>
                    </div>
                    <div class="chapters_list">
                        <router-link
                            v-for="character in item.chapters"
                            :key="character.id"
                            tag="div"
                            :to="getRouteParams('chapters', character.id)"
                            class="chapters_list__item"
                            @click.native.stop>
                            <div class="ico"><i class="fi fi-rr-document"></i></div> {{ character.name }}
                        </router-link>
                    </div>
                    <router-link
                        v-if="item.has_more"
                        tag="div"
                        :to="getRouteParams('sections', item.id)"
                        class="more"
                        @click.native.stop>
                        <div class="ico"></div>
                        {{ $t('support.viewAllPages') }}
                    </router-link>
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
        SupportOrgSelect: () => import('./SupportOrgSelect.vue'),
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
        currentContractorId() {
            return this.user?.current_contractor?.id || null
        }
    },
    data() {
        return {
            page: 0,
            orgLoading: false,
            loading: false,
            empty: false,
            selectedOrg: null,
            list: {
                results: [],
                next: true
            }
        }
    },
    created() {
        this.getMyOrganization()
        eventBus.$on('support_wiki_force_reload', this.fUpdChapterList)
    },
    beforeDestroy() {
        eventBus.$off('support_wiki_force_reload', this.fUpdChapterList)
    },
    methods: {
        orgLogoPath(org) {
            return org?.logo || org?.workgroup_logo?.path || ''
        },
        getRouteParams(type, id) {
            return {
                name: 'company-wiki',
                params: {
                    wikiType: type,
                    wikiId: String(id)
                },
                query: this.$route.query
            }
        },
        openSection(id) {
            this.$router.push(this.getRouteParams('sections', id))
        },
        handleOrgSwitcherClick(open, event) {
            if(this.isMobile) {
                event.preventDefault()
                open()
            }
        },
        async selectOrg(work) {
            try {
                this.orgLoading = true
                await this.$http.post('/users/current_contractor/change/', {
                    id: work.id
                })

                this.$store.commit('user/CHANGE_USER_ORG', work)
                this.selectedOrg = work

                this.$nextTick(() => {
                    eventBus.$emit('support_current_contractor_changed', {
                        contractorId: work?.id || null
                    })
                })
            } catch(error) {
                errorHandler({error})
                this.selectedOrg = this.user?.current_contractor || null
            } finally {
                this.orgLoading = false
            }
        },
        async getMyOrganization() {
            try {
                this.orgLoading = true
                const { data } = await this.$http.get('/users/current_contractor/detail/')

                if(data) {
                    this.selectedOrg = data
                    this.$store.commit('user/CHANGE_USER_ORG', data)
                } else {
                    this.selectedOrg = this.user?.current_contractor || null
                }
            } catch(error) {
                this.selectedOrg = this.user?.current_contractor || null
            } finally {
                this.orgLoading = false
            }
        },
        fUpdChapterList() {
            this.$nextTick(() => {
                this.page = 0
                this.empty = false
                this.list = {
                    results: [],
                    next: true
                }
                this.$refs.support_infinity.stateChanger.reset()
            })
        },
        async getSections($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const { data } = await this.$http.get('/wiki/sections/', {
                        params: {
                            page: this.page,
                            page_size: 15,
                            contractor: this.currentContractorId
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
    }
}
</script>

<style lang="scss" scoped>
.b_item{
    background: #ffffff;
    border-radius: 20px;
    padding: 28px 24px;
    min-height: 100%;
    transition: box-shadow 0.3s cubic-bezier(0.645, 0.045, 0.355, 1), transform 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
        transform: translateY(-2px);
    }
    .item_head{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 10px;
    }
    .private_tag{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 0;
        flex-shrink: 0;
        line-height: 24px;
        padding: 0 8px;
        font-size: 12px;
    }
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
        font-size: 16px;
        line-height: 1.2;
        cursor: pointer;
        margin-bottom: 0;
        color: #000000;
        word-break: break-word;
        white-space: normal;
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
    min-height: 100%;
    position: relative;
    &::before{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 250px;
        background:
            radial-gradient(circle at 28% 26%, rgba(90, 225, 193, 0.14) 0%, rgba(90, 225, 193, 0) 36%),
            radial-gradient(circle at 72% 24%, rgba(137, 92, 255, 0.14) 0%, rgba(137, 92, 255, 0) 36%),
            linear-gradient(90deg, rgba(227, 246, 245, 0.72) 0%, rgba(240, 235, 255, 0.72) 100%);
        mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.95) 0%, rgba(0, 0, 0, 0.88) 48%, rgba(0, 0, 0, 0.42) 78%, rgba(0, 0, 0, 0.12) 92%, rgba(0, 0, 0, 0) 100%);
        -webkit-mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.95) 0%, rgba(0, 0, 0, 0.88) 48%, rgba(0, 0, 0, 0.42) 78%, rgba(0, 0, 0, 0.12) 92%, rgba(0, 0, 0, 0) 100%);
        pointer-events: none;
        z-index: 0;
    }
    > * {
        position: relative;
        z-index: 1;
    }
}
.content_header{
    padding: 24px 15px 10px 15px;
    @media (min-width: 768px) {
        padding: 32px 20px 12px 20px;
    }
    .search_wrap{
        max-width: 1150px;
        margin: 0 auto;
    }
    .search_subtitle{
        margin-top: 6px;
        font-size: 16px;
        line-height: 1.5;
        color: rgba(31, 31, 31, 0.68);
    }
}
.content_body{
    padding: 10px 15px 40px 15px;
    @media (min-width: 768px) {
        padding: 14px 20px 60px 20px;
    }
    .wrap{
        max-width: 1150px;
        margin: 0 auto;
        display: grid;
        gap: 16px;
        grid-template-columns: repeat(1, minmax(0, 1fr));
        @media (min-width: 768px) {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        @media (min-width: 992px) {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
    }
}

.search_subtitle{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;

    &__dash{
        color: #8c8c8c;
    }
}

.org_switcher{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 0;
    border: 0;
    background: transparent;
    cursor: pointer;
    max-width: 100%;
}

.org_switcher__name{
    color: var(--blue);
    border-bottom: 1px dashed var(--blue);
    line-height: 1.2;
}
</style>
