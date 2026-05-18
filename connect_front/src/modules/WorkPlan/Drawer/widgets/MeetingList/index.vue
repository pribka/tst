<template>
    <div class="list_card">
        <div class="mb-3 flex items-center gap-2">
            <a-input 
                v-model="search"
                :placeholder="$t('workplan.search')" 
                size="large" 
                :class="useInject && 'bg_invert'"
                class="tab_search"
                @change="changeSearch()">
                <template #suffix>
                    <transition name="fade-scale" mode="out-in">
                        <a-button 
                            v-if="search.length"
                            type="ui_ghost" 
                            size="small"
                            flaticon
                            shape="circle"
                            icon="fi-rr-cross-small"
                            @click="clearSearch()" />
                        <i v-else class="fi fi-rr-search mr-1" />
                    </transition>
                </template>
            </a-input>
        </div>
        <a-empty v-if="list.empty" class="mt-4" :description="$t('workplan.no_meetings')" />
        <template v-if="list.page === 1 && list.loading">
            <CardLoading v-for="i in 5" :key="i" :useInject="useInject" />
        </template>
        <Card 
            v-for="meeting in list.results" 
            :key="meeting.id" 
            :useInject="useInject"
            :storeKey="storeKey"
            :meeting="meeting" />
        <a-button 
            v-if="list.results.length && list.next" 
            :loading="list.loading" 
            type="flat_primary"
            block
            @click="nextLoading()">
            {{ $t('workplan.load_more') }}
        </a-button>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
const listType = 'meetingList'
let searchTimer;
export default {
    props: {
        storeKey: {
            type: String,
            required: true
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    components: {
        Card: () => import('./Card.vue'),
        CardLoading: () => import('./CardLoading.vue')
    },
    computed: {
        isMobile() { 
            return this.$store.state.isMobile
        },
        list() {
            return this.$store.state.workplan[listType]?.[this.storeKey] || null
        },
        search: {
            get() {
                return this.list?.search || ""
            },
            set(value) {
                this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                    field: 'search', 
                    value: value, 
                    storeKey: this.storeKey, 
                    list: listType
                })
            }
        }
    },
    methods: {
        addMeeting() {
            this.$store.commit('meeting/SET_EDIT_MODAL', { show: true, model: 'main' })
        },
        clearSearch() {
            this.search = ""
            clearTimeout(searchTimer)
            this.reloadList()
        },
        changeSearch() {
            clearTimeout(searchTimer)
            searchTimer = setTimeout(() => {
                this.reloadList()
            }, 700)
        },
        nextLoading() {
            this.$store.commit('workplan/CHANGE_LIST_FIELD', {
                field: 'page', 
                value: this.list.page + 1, 
                storeKey: this.storeKey, 
                list: listType
            })
            this.getList()
        },
        reloadList() {
            this.$store.commit('workplan/CLEAR_LIST', {
                storeKey: this.storeKey,
                list: listType
            })
            this.getList()
        },
        async getList() {
            try {
                await this.$store.dispatch('workplan/getMeetingList', { storeKey: this.storeKey })
            } catch(error) {
                errorHandler({error, show: false})
            }
        }
    },
    mounted() {
        if(!this.list.results?.length && !this.list.empty)
            this.getList()
        if(!this.list.results?.length && this.list.empty)
            this.reloadList()
    },
    beforeDestroy() {
        if(!this.useInject) return
        this.$store.commit('workplan/CLEAR_LIST', {
            storeKey: this.storeKey,
            list: listType
        })
    }
}
</script>

<style lang="scss" scoped>
.tab_search{
    &.bg_invert{
        &::v-deep{
            .ant-input{
                background: #f7f9fc;
            }
        }
    }
}
.fade-scale-enter-active,
.fade-scale-leave-active {
    transition: opacity .15s ease, transform .15s ease
}
.fade-scale-enter,
.fade-scale-leave-to {
    opacity: 0;
    transform: scale(.55)
}
</style>
