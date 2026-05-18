<template>
    <div 
        class="flex flex-col relative overflow-hidden content_height"
        :class="main && 'page_padding'">
        <h1 v-if="showPageTitle && pageH1Title" class="m_page_title">
            {{ pageH1Title }}
        </h1>

        <div v-if="showHeader" class="float_add">
            <a-button 
                flaticon
                class="fixed_button"
                shape="circle"
                size="large"
                icon="fi-rr-list"
                @click="toTaskView" />
            
            <div class="filter_slot">
                <slot />
            </div>
            <a-button 
                v-if="addButton"
                flaticon
                shape="circle"
                size="large"
                type="primary"
                icon="fi-rr-plus"
                @click="addTaskDrawer()" />
        </div>
        <div class="flex-grow w-full min-h-0">
            <swiper 
                ref="swiper"
                class="h-full"
                @slideChange="slideChange"
                :options="swiperOption">
                <swiper-slide
                    v-for="(column, index) in columns" 
                    :key="column.code" >
                    <KanbanMobileColumn 
                        :column="column"
                        :slideIndex="index"
                        :selectElement="selectElement"
                        :setSelectElement="setSelectElement"
                        :taskType="taskType"
                        :pageName="pageName"
                        :queryParams="queryParams"
                        :implementId="implementId"
                        :implementType="implementType" />
                </swiper-slide>
                <!-- <div class="swiper-button-prev" slot="button-prev"></div>
                <div class="swiper-button-next" slot="button-next"></div> -->
            </swiper>
        </div>
    </div>
</template>

<script>
import { mapActions, mapState } from 'vuex'

import config from '../mixins/config.js'
import { Swiper, SwiperSlide } from 'vue-awesome-swiper'
import 'swiper/css/swiper.css'

export default {
    name: "Kanban",
    mixins: [
        config
    ],
    components: {
        KanbanMobileColumn: () => import('./KanbanMobileColumn.vue'),
        Swiper,
        SwiperSlide
    },
    props: {
        main: { 
            type: Boolean,
            default: false
        },
        showPageTitle: {
            type: Boolean,
            default: false
        },
        implementId: {
            type: [String, Number],
            default: null
        },
        implementType: {
            type: String,
            default: ''
        },
        formParams: { // Заполнитель данных в форме по умолчанию
            type: Object,
            default: () => {}
        },
        queryParams: {
            type: Object,
            default: () => null
        },
        taskType: {
            type: String,
            default: 'task'
        },
        pageName: {
            type: String,
            default: ''
        },
        showHeader: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            statusList: state => state.task.statusList,
            statusLoader: state => state.task.statusLoader,
            isMobile: state => state.isMobile,
            mobileSlideIndex: state => state.task.mobileSlideIndex
        }),
        pageH1Title() {
            return this.$route?.meta?.title ? this.$route.meta.title : null
        },

        columns() {
            if(this.statusList?.[this.taskType]?.length)
                return this.statusList[this.taskType]
            else
                return []
        },
        filters() {
            if(this.implementId)
                return {
                    [this.implementType]: this.implementId
                }
            else
                return null
        },
    },
    data() {
        return {
            loading: false,
            oldStatus: "",
            selectElement: null,
            oldQuery: {},
            left: false,
            right: false,

            swiperOption: {
                slidesPerView: 3,
                spaceBetween: 20,
                slidesPerView: 'auto',
                // navigation: {
                //     nextEl: '.swiper-button-next',
                //     prevEl: '.swiper-button-prev'
                // }
            }
        }
    },
    created(){
        this.getStatus()
        // this.getTaskActions()
        if(this.$route.query.task){
            this.oldQuery = this.$route.query
        }

        this.$store.commit('task/INIT_MOBILE_SLIDE_INDEX', this.pageName)      
        // setTimeout(() => {
        //     this.onScroll()
        // }, 500)
    },
    mounted() {
        // initialSlide
        const initialSlide = this.mobileSlideIndex[this.pageName] || 0
        this.$refs.swiper.$swiper.slideTo(initialSlide, 0)
    },
    watch: {
        '$route.query'(val){
            // if(!val.hasOwnProperty('task') && !this.oldQuery.hasOwnProperty('task'))

            // delete val['status']
            // delete val['page']

            this.oldQuery = val
        },
    },
    methods: {
        ...mapActions({
            getStatusList: 'task/getStatusList'
        }),
        toTaskView() {
            if(this.taskType === 'interest') {
                return this.$router.push('interest')
            }
            return this.$router.push('tasks')
        },
        async getTaskActions() {
            try {
                await this.$store.dispatch('task/getTaskActions', {
                    task_type: this.taskType
                })
            } catch(e) {
                this.$message.error(this.$t('error'))
            }
        },
        setSelectElement(item) {
            this.selectElement = item
        },
        async getStatus() {
            try {
                await this.getStatusList({ task_type: this.taskType })
            } catch(e) {
                console.log(e)
            }
        },
        slideChange() {
            const slideIndex = this.$refs.swiper.$swiper.realIndex
            this.$store.commit('task/SET_MOBILE_SLIDE_INDEX', {
                slideIndex: slideIndex,
                pageName: this.pageName
            })            
        }
    }
}
</script>

<style scoped lang="scss">
.p-\[15px\] {
    padding: 15px;
}

$y-paddings: 30px;
.content_height {
    height: calc(var(--vh, 1vh) * 100 - var(--headerHeight) - var(--footerHeight));
}
.page_padding {
    padding: 15px;
}
</style>
