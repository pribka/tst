<template>
    <div class="kanban">
        <template>
            <template v-if="!isMobile" >
                <div class="flex items-center pb-4 kanban_button">
                    <AddButton
                        v-if="addButton"
                        :formParams="formParams"
                        :addButton="addButton"
                        :windowWidth="windowWidth" />
                    <div class="ml-2">
                        <slot />
                    </div>
                </div>
            </template>
            <template v-else>
                <div class="float_add">
                    <div class="filter_slot">
                        <slot />
                    </div>
                    <AddButton
                        v-if="addButton"
                        :formParams="formParams"
                        :addButton="addButton"
                        buttonType="circle"
                        :windowWidth="windowWidth" />
                </div>
            </template>
        </template>

        <div class="kanban_container">
            <div 
                @scroll="onScroll"  
                class="kanban_wrapper" 
                ref="kanbanWrapper">
                <div v-if="statusLoader">

                </div>
                <div 
                    v-else 
                    class="kanban-main overflow-x-scroll">
                    <span class="scroll_dummy"></span>
                    <Column 
                        v-for="column in columns" 
                        :key="column.code" 
                        :column="column"
                        :selectElement="selectElement"
                        :setSelectElement="setSelectElement"
                        :taskType="taskType"
                        :queryParams="queryParams"
                        :implementId="implementId"
                        :implementType="implementType" />
                    <span class="scroll_dummy"></span>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapActions, mapState } from 'vuex'
import config from '../mixins/config.js'
export default {
    name: "KanbanListMobile",
    mixins: [
        config
    ],
    components: {
        AddButton: () => import("../AddButton.vue"),
        Column: () => import('./Column.vue')
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
            default: 'task'
        },
        extendDrawer: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({
            windowWidth: state => state.windowWidth,
            statusList: state => state.task.statusList,
            statusLoader: state => state.task.statusLoader,
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
            timer: null,
            left: false,
            right: false
        }
    },
    created(){
        this.getStatus()
        // this.getTaskActions()
        if(this.$route.query.task){
            this.oldQuery = this.$route.query
        }
        setTimeout(() => {
            this.onScroll()
        }, 500)
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
        onScroll(){
            if(this.$refs.kanbanWrapper.scrollLeft === 0)
            {
                this.right = true
                this.left = false
            }  else {
                this.left = true
            }
            if(this.$refs.kanbanWrapper.scrollLeft === this.$refs.kanbanWrapper.scrollLeftMax){
                this.right = false
            } else {
                this.right = true
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
        }
    }
}
</script>

<style scoped lang="scss">
.arrow{
    @media (max-width: 600px) {
            display: none;
    }
    width: 20px;
    height: 30px;
    position: absolute;
    top: 55%;
    display: block;
    margin-top: -15px;
    z-index: 5;
    opacity: 0.3;
    outline: none;
    &:hover{
        opacity: 0.4;
    }
    &.arrow_left{
        border-radius: 0px 30px 30px 0px;
        background: black url('../../assets/images/left-arrow.svg') no-repeat;
        background-size: 14px;
        background-position: 0px center;
    }
    &.arrow_right_main,
    &.arrow_right{
        &:not(.arrow_right_main) {
            // left: 0;
                right: 0;
            margin-left: -20px;
        }
        border-radius: 30px 0px 0px 30px;
        background: black url('../../assets/images/right-arrow.svg') no-repeat;
        background-size: 14px;
        background-position: 5px;
    }
    &.arrow_right_main{
        right: 15px;
        margin-top: -22px;
    }
}
.kanban{
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 100%;
    .kanban_button{
        padding-left: 30px;
        padding-right: 30px;
        padding-top: 20px;
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
    padding-bottom: 20px;
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
    height: calc(100% - 76px);
}
.kanban-main{
    display: flex;
    flex-grow: 1;
    flex-direction: row;
    height: 100%;
    .scroll_dummy{
        @media(min-width: 981px){
            min-width: 30px;
        }
        @media(max-width: 980px){
            min-width: 15px;
        }
    }
}
</style>

<style lang="scss" scoped>
.scroll_block{
    .__view{
        height: 100%;
    }
}
</style>