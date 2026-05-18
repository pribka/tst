<template>
    <div>
        <h1 v-if="pageH1Title" class="m_page_title">
            {{ pageH1Title }}
        </h1>

        <div 
            class="float_add"
            v-if="$slots.connectButton || $slots.pageFilter">
            <div v-if="$slots.pageFilter" class="filter_slot">
                <slot name="pageFilter" />
            </div>
            <div class="" v-if="$slots.connectButton">
                <slot name="connectButton" />
            </div>
        </div>
        
        <div>
            <ViewListItem
                class="mb-2 last:mb-0"
                v-for="ticket in ticketList"
                :key="ticket.id"
                :ticket="ticket" />
            
            <infinite-loading 
                key="ticketsInfiniteLoading"
                ref="infiniteLoading"
                @infinite="getTickets"
                :identifier="infiniteId"
                :distance="10">
                <div 
                    slot="spinner"
                    class="flex items-center justify-center inf_spinner">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
    </div>
</template>

<script>

import ViewListItem from './ViewListItem'
import InfiniteLoading from 'vue-infinite-loading'
import { mapActions, mapState } from 'vuex'
import eventBus from '@/utils/eventBus'
export default {
    name: 'MyBasesList',
    components: {
        ViewListItem,
        InfiniteLoading
    },
    props: {
        model: {
            type: String,
            default: 'tickets.TicketModel'
        },
        pageName: {
            type: String,
            default: 'IncomingServiceTicketModel'
        }
    },
    data() {
        return {
            infiniteId: new Date(),
            page: 0,
            isListLoading: false,
        }
    },
    computed: {
        ...mapState({
            ticketList: state => state.mybases.ticketList,
            ticketNext: state => state.mybases.ticketNext,
        }),
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        }
    },
    // async created() {
    // },
    mounted() {
        eventBus.$on(`update_filter_${this.model}`, () => {
            this.page = 0
            this.$store.commit('mybases/CLEAR_TICKET_LIST')
            this.$nextTick(()=>{
                if(this.$refs.infiniteLoading){
                    this.$refs.infiniteLoading.stateChanger.reset(); 
                }
            })
        })
        
        
    },
    beforeDestroy() {
        eventBus.$off(`update_filter_${this.model}`)
    },
    methods: {
        ...mapActions({
            getTicketList: 'mybases/getTicketList'
        }),
        
        async getTickets($state) {
            if(!this.ticketNext) {
                $state.complete()
                return
            }   
            if(!this.isListLoading) {
                this.isListLoading = true
                const params = {
                    page_name: this.pageName,
                    page_size: 5,
                    page: this.page + 1
                }
                try {
                    const data = await this.getTicketList(params)
                    if(data.next) {
                        this.page += 1
                        $state.loaded()
                    } else {
                        $state.complete()
                    }
                } catch(error) {
                    console.error(error)
                }
                this.isListLoading = false
            }
        }
    }
}
</script>

