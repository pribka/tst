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

            <div>
                <a-button v-if="isMobile" type="primary" style="min-width: auto;" shape="circle" size="large" flaticon icon="fi-rr-plus" @click="addEvent()" />
                <a-button v-else type="primary" style="min-width: auto;" size="large" flaticon icon="fi-rr-plus" @click="addEvent()">
                    {{ $t('workplan.add_event') }}
                </a-button>
            </div>
        </div>
        <a-empty v-if="list.empty" class="mt-4" :description="$t('workplan.no_events')" />
        <template v-if="list.page === 1 && list.loading">
            <CardLoading v-for="i in 5" :key="i" :useInject="useInject" />
        </template>
        <Card 
            v-for="event in list.results" 
            :key="event.id" 
            :useInject="useInject"
            :storeKey="storeKey"
            :event="event" />
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
import eventBus from '@/utils/eventBus'
const listType = 'eventList'
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
        addEvent() {
            eventBus.$emit('open_event_form', 
                null, 
                null, 
                null, 
                null, 
                'default')
        },
        reloadList() {
            this.$store.commit('workplan/CLEAR_LIST', {
                storeKey: this.storeKey,
                list: listType
            })
            this.getList()
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
        async getList() {
            try {
                await this.$store.dispatch('workplan/getEventList', { storeKey: this.storeKey })
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
.fade-scale-enter-active,
.fade-scale-leave-active {
    transition: opacity .15s ease, transform .15s ease
}
.fade-scale-enter,
.fade-scale-leave-to {
    opacity: 0;
    transform: scale(.55)
}
.tab_search{
    &.bg_invert{
        &::v-deep{
            .ant-input{
                background: #f7f9fc;
            }
        }
    }
}
</style>
