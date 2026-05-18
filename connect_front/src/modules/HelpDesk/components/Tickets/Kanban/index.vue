<template>
    <div class="kanban">
        <template  v-if="!isMobile">
            <button 
                v-show="leftActive"
                class="arrow_left arrow"
                @mouseenter="scrollLeft"
                @mouseleave="clear">
                <i class="fi fi-rr-angle-small-left"></i>
            </button>
            <button 
                v-show="rightActive"
                class="arrow_right arrow"
                @mouseenter="scrollRight"
                @mouseleave="clear">
                <i class="fi fi-rr-angle-small-right"></i>
            </button> 
        </template>

        <div class="kanban_container">
            <div 
                class="kanban_wrapper" 
                ref="kanbanWrapper"
                v-scroll="handleScroll">
                <div v-if="statusLoader" />
                <div 
                    v-else 
                    class="kanban-main">
                    <span v-if="useScrollDummy" class="scroll_dummy"></span>
                    <Column 
                        v-for="column in columns" 
                        :key="column.code" 
                        :column="column"
                        :selectElement="selectElement"
                        :setSelectElement="setSelectElement"
                        :taskType="taskType"
                        :page_name="page_name"
                        :queryParams="queryParams"
                        :implementId="implementId"
                        :implementType="implementType" />
                    <span v-if="useScrollDummy" class="scroll_dummy"></span>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapActions, mapState } from 'vuex'
import { vScroll } from '@vueuse/components'
import { useScroll, onKeyStroke } from '@vueuse/core'
export default {
    name: "Tickets-Kanban",
    components: {
        Column: () => import('./Column.vue')
    },
    directives: {
        scroll: vScroll
    },
    props: {
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
            default: 'tickets'
        },
        extendDrawer: {
            type: Boolean,
            default: false
        },
        showAddButton: {
            type: Boolean,
            default: true
        },
        useScrollDummy: {
            type: Boolean,
            default: true
        },
        page_name: {
            type: String,
            default: ""
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            statusList: state => state.tickets.statusList,
            statusLoader: state => state.tickets.statusLoader,
            isMobile: state => state.isMobile
        }),
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
        }
    },
    data() {
        return {
            loading: false,
            oldStatus: "",
            selectElement: null,
            oldQuery: {},
            leftActive: true,
            rightActive: true,
            timer: null
        }
    },
    created(){
        this.getStatus()
        if(this.$route.query.task){
            this.oldQuery = this.$route.query
        }
    },
    watch: {
        '$route.query'(val){
            this.oldQuery = val
        },
    },
    methods: {
        ...mapActions({
            getStatusList: 'tickets/getStatusList'
        }),
        async getTaskActions() {
            try {
                await this.$store.dispatch('tickets/getTaskActions', {
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
        scrollLeft(){
            this.timer = setInterval(() => {
                this.$refs.kanbanWrapper.scrollLeft -= 5
            }, 10)
        },
        scrollRight(){
            this.timer = setInterval(() => {
                this.$refs.kanbanWrapper.scrollLeft += 5
            }, 10)
        },
        clear(){
            clearInterval(this.timer)
        },
        handleScroll(e) {
            this.leftActive = !e.arrivedState.left
            this.rightActive = !e.arrivedState.right
        }
    },
    mounted() {
        this.$nextTick(() => {
            const { arrivedState } = useScroll(this.$refs.kanbanWrapper)
            this.leftActive = !arrivedState.left
            this.rightActive = !arrivedState.right
        })

        onKeyStroke(['a', 'A', 'ArrowLeft'], () => {
            this.$refs.kanbanWrapper.scrollLeft -= 20
        })
        onKeyStroke(['d', 'D', 'ArrowRight'], () => {
            this.$refs.kanbanWrapper.scrollLeft += 20
        }, { dedupe: true })
    }
}
</script>

<style scoped lang="scss">
.arrow{
    @media (max-width: 600px) {
            display: none;
    }

    height: 40px;
    width: 40px;
    border-radius: 50%;
    background: #e8ecfa;
    color: #4777ff;

    position: absolute;
    top: 50%;
    opacity: 0;
    margin-top: -20px;
    z-index: 50;
    outline: none;
    font-size: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    &:hover{
        background: #4777ff;
        color: #fff;
    }
    &.arrow_left{
        left: 15px;
    }
    &.arrow_right_main,
    &.arrow_right{
        &:not(.arrow_right_main) {
            // left: 0;
                right: 15px;
            margin-left: -20px;
        }
    }
    &.arrow_right_main{
        right: 15px;
        margin-top: -25px;
    }
}
.kanban{
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 100%;
    &:hover{
        .arrow{
            opacity: 1;
        }
    }
    .kanban_button{
        padding-left: 30px;
        padding-right: 30px;
        // padding-top: 20px;
    }
    .flip-list-move {
        transition: transform 0.5s;
    }
    .no-move {
        transition: transform 0s;
    }
    .ghost{
        opacity: 0.5;
        background: #c8ebfb;
        &:not(:last-child){
            margin-bottom: 15px;
        }
    }
}

.kanban_wrapper{
    position: relative;
    // padding-bottom: 20px;
    overflow-x: auto;
    overflow-y: hidden;
    display: flex;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior-x: contain;
    flex-direction: column;
    --safe-area-inset-bottom: env(safe-area-inset-bottom);
    height: 100%;
    &::-webkit-scrollbar{
        height: 7px;
    }
    @media(min-width: 981px){
        scroll-padding: 40px;
    }
    @media(max-width: 980px){
        scroll-padding: 20px;
        scroll-snap-type: x mandatory;
    }
}
.kanban_container{
    flex-grow: 1;
    height: 100%;
}
.kanban-main{
    display: flex;
    flex-grow: 1;
    flex-direction: row;
    height: 100%;
    .scroll_dummy{
        min-width: 15px;
    }
}
</style>

<style lang="scss" scoped>
::v-deep {
    .scroll_block{
        .__view{
            height: 100%;
        }
    }
}
</style>
