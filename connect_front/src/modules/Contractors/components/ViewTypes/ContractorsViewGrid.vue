<template>
    <div class="overflow-hidden flex flex-col">
        <div 
            class="overflow-y-scroll"
            ref="refContractorsList">
            <div class="grid 2xl:grid-cols-4 lg:grid-cols-3 gap-2">
                <ContractorsViewGridCard
                    v-for="contractor in contractorsList"
                    :key="contractor.id"
                    :contractor="contractor"
                    :cart="true"
                    :edit="true" />
            </div>
            <InfiniteLoading
                :key="contractorsType"
                ref="infiniteLoading"
                @infinite="getContractors"
                :identifier="infiniteId"
                :distance="10">
                <div 
                    slot="spinner"
                    class="mt-4 flex items-center justify-center inf_spinner">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </InfiniteLoading>
            <div 
                v-if="isEmpty" 
                class="flex justify-center">
                <a-empty />
            </div>
        </div>
    </div>
</template>
  
<script>
import InfiniteLoading from 'vue-infinite-loading'
import ContractorsViewGridCard from './ContractorsViewGridCard.vue'
import eventBus from '@/utils/eventBus.js'
import { mapState, mapActions } from 'vuex'

let timer

export default {
    name: 'ContractorsGrid',
    components: {
        ContractorsViewGridCard,
        InfiniteLoading
    },
    props: {
        pageName: {
            type: String,
            required: true
        },
    },
    data() {
        return {
            infiniteId: new Date(),

            contractorListLoading: false,
            searchText: '',
            curator: {},
            orderForm: null,
            paginatorNext: true,
            paginatorPageNumber: 1,
            isEmpty: false,
        }
    },
    computed: {
        ...mapState({
            models: state => state.contractors.models,
            contractors: state => state.contractors.contractors,
            contractorsListNext: state => state.contractors.contractorsListNext,
            contractorsType: state => state.contractors.contractorsType,
        }),
        model() {
            return this.models[this.contractorsType]
        },
        currentContractors() {
            return this.contractors?.[this.contractorsType]
        },
        contractorsList() {
            return this.currentContractors?.results
        },
        currentNext() {
            if(this.currentContractors?.next === null)
                return null
            return true
        },
        nextPage() {
            const defaultPage = 1
            const currentPage = this.currentContractors?.page
            return currentPage ? (currentPage + 1) : defaultPage

        }
    },
    methods: {
        ...mapActions({
            getContractorList: 'contractors/getContractorInfiniteList'
        }),
        reloadList() {
            this.$store.commit('dashboard/CLEAR_CONTRACTORS_LIST')
            this.paginatorNext = true
            this.paginatorPageNumber = 1
        },

        reload() {
            this.currentContractors.page = 0
            this.currentContractors.results.splice(0)
            this.currentContractors.next = true
            
            this.$nextTick(()=>{
                if(this.$refs.infiniteLoading){
                    this.$refs.infiniteLoading.stateChanger.reset(); 
                }
            })
        },
        async getContractors($state) {
            if(!this.contractorListLoading) {
                if(this.currentNext) {
                    const params = {
                        page_size: 15,
                        page: this.nextPage,
                        page_name: this.pageName
                    }
                    this.contractorListLoading = true
                    try {
                        await this.getContractorList({
                            contractorsType: this.contractorsType,
                            params: params
                        })
                        if(this.currentNext)
                            $state.loaded()
                        else
                            $state.complete()
                    } catch(error) {
                        console.error(error)
                    } finally {
                        this.contractorListLoading = false
                    }
                } else {
                    $state.complete()
                }
            }
        },
    },

    mounted() {
        for(let modelKey in this.models) {
            eventBus.$on(`update_filter_${this.models[modelKey]}`, () => this.reload())
        }
    },
    beforeDestroy() {
        for(let modelKey in this.models) {
            eventBus.$off(`update_filter_${this.models[modelKey]}`)
        }
    }
}
</script>
  
<style lang="scss" scoped>
.contractor_list_wrap {
    max-height: 68vh;
    padding: 15px;
    padding-top: 0;
    overflow-y: scroll;
}

.contractors_list {
    padding: 0 !important;
    &::v-deep{
        .filter_pop_wrapper{
            min-width: 100%;
        }
    }
}
::v-deep{
    .ant-popover-placement-bottomRight .ant-popover-inner-content{
        padding: 12px 16px;
    }
}
</style>