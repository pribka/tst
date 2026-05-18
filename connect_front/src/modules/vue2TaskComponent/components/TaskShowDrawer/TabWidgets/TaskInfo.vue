<template>
    <div
        class="task_tab_info"
        :data-guide-id="task && task.task_type === 'interest' ? 'interest-description' : null">
        <div 
            v-if="task.reason" 
            class="mb-4">
            <template v-if="task.reason.model === 'chat_message'">
                {{$t('task.main_task_message')}}
                <router-link :to="{name: 'chat', query:{id: task.reason.chat}}">
                    {{task.reason.chat}}
                </router-link>
            </template>
            <template v-if="task.reason.model === 'comments'">
                {{$t('task.main_task_comment')}}
                {{task.reason.id}}
            </template>
            <template v-if="task.reason.model === 'files'">
                {{$t('task.main_task_files')}}
                {{task.reason.id}}
            </template>
        </div>

        <TaskAside
            v-if="isMobile"
            :task="task" 
            :closeDrawer="closeDrawer"
            :dropActions="dropActions"
            :isMobile="isMobile" />

        <template v-if="task.description">
            <div :class="isMobile && 'py-2 mt-2'">
                <div 
                    v-if="isMobile"
                    class="mb-1 text-sm font-semibold">
                    {{ $t('task.description') }}
                </div>
                <TextViewer 
                    class="body_text" 
                    :body="task.description" />
            </div>
        </template>
        <div 
            v-else
            class="flex items-center justify-center"
            :class="isMobile && 'py-2'">
            <a-empty :description="$t('task.no_description')">
                <a-button 
                    v-if="dropActions && dropActions.edit && dropActions.edit && !task.is_sign_task"
                    type="ui"
                    @click="edit()">
                    {{$t('task.add')}}
                </a-button>
            </a-empty>
        </div>
        
        <!-- Результат -->
        <template v-if="task.result">
            <div class="bg-light-gray rounded mt-4 p-4 text-black">
                <p>{{ $t('Execution result') }}</p>
                <p class="mt-2.5 opacity-60 leading-[1.3]">
                    {{ task.result }}
                </p>
            </div>
        </template>

        <!-- Голосования -->
        <!--<div 
            v-if="task.task_type === 'task'" 
            class="flex justify-end mt-2">
            <template v-if="!taskVoteLoading">
                <div class="text-lg">
                    <span>
                        <i 
                            @click="vote('like')"
                            class="fi fi-rr-social-network transition-colors cursor-pointer"
                            :class="{ 'blue_color': myVote === 'like'}"></i>
                        <span class="ml-1">{{ taskVote.likes_count }}</span>
                    </span>
                    <span class="ml-3">
                        <i 
                            @click="vote('dislike')"
                            class="fi fi-rr-hand transition-colors cursor-pointer"
                            :class="{ 'text_red': myVote === 'dislike'}"></i>
                        <span class="ml-1">{{ taskVote.dislikes_count }}</span>
                    </span>
                </div>
            </template>
            <template v-else>
                <a-spin></a-spin>
            </template>
        </div>-->

        <div 
            v-if="task.parent"
            class="mt-4 parent_task">
            <!-- Основная задача -->
            {{$t('task.main_task')}} 
            <span 
                class="cursor-pointer blue_color text-primary" 
                @click="openTask()">
                {{task.parent.name}}
            </span>
        </div>

        <template v-if="!isMobile">
            <!-- Таблица подзадач -->
            <template v-if="task.children_count > 0">
                <TaskList
                    class="border_gray_top"
                    :class="isMobile || 'pt-4 mt-4'"
                    :hash="false"
                    :showChildren="false"
                    :showAddButton="false"
                    :showPager="false"
                    tableType="subtasks"
                    autoHeight
                    :showHeader="false"
                    :reloadTask="reloadTask"
                    :queryParams="{ parent: task.id, task_type: 'task,stage,milestone'}"
                    :scrollWrapper="{x: 1300, y: 300}"
                    size="small"
                    :pageName="`page_list_task_${task.id}.TaskModel`"
                    :taskType="task.task_type"
                    :showFilter="false"
                    :showActionButton="false"
                    hideActionColumn

                    :name="`fltask_${task.id}`" >
                    <template v-slot:header>
                        <h4 class="mb-3 text-lg font-semibold">
                            {{$t('task.subtask')}}
                        </h4>
                    </template>
                </TaskList>
            </template>
    
            <!-- Комментарии -->
            <div class="mt-5">
                <div class="mb-1 font-semibold">
                    {{ $t('task.comments') }}
                </div>
                <vue2CommentsComponent
                    bodySelector=".task_body_wrap"
                    :related_object="task.id"
                    initScroll
                    :mentionsData="taskUsers"
                    model="tasks" />
            </div>
        </template>
        <template v-else>
            <div class="task_info_collapse mt-4">
                <a-collapse 
                    :bordered="false" 
                    v-model="expanded" >
                    <!-- Таблица подзадач -->
                    <a-collapse-panel
                        v-if="task.children_count > 0"
                        key="subtasks"
                        :header="$t('task.subtask')">
                        <TaskList
                            class="border_gray_top"
                            :class="isMobile || 'pt-4 mt-4'"
                            :hash="false"
                            :showHeader="false"
                            :showChildren="false"
                            :showAddButton="false"
                            :showPager="false"
                            tableType="subtasks"
                            :reloadTask="reloadTask"
                            :queryParams="{ parent: task.id, task_type: 'task,stage,milestone'}"
                            :scrollWrapper="{x: 1000, y: 300}"
                            size="small"
                            :pageName="`page_list_task_${task.id}.TaskModel`"
                            :taskType="task.task_type"
                            :showFilter="false"
                            :showActionButton="false"
                            hideActionColumn
                            :name="`fltask_${task.id}`" >
                            <template v-slot:header>
                                <h4 class="mb-3 text-lg font-semibold">
                                    {{$t('task.subtask')}}
                                </h4>
                            </template>
                        </TaskList>
                    </a-collapse-panel>
                    
                    <!-- Комментарии -->
                    <a-collapse-panel
                        key="comments"
                        :header="$t('task.comments')">
                        <vue2CommentsComponent
                            bodySelector=".task_body_wrap"
                            :related_object="task.id"
                            injectContainer
                            initScroll
                            :mentionsData="taskUsers"
                            :injectContainerSelector="bodyWrap"
                            model="tasks" />
                    </a-collapse-panel>
                </a-collapse>
            </div>
        </template>
    </div>
</template>

<script>
import { priorityList } from '../../../utils'
import taskHandler from '../../mixins/taskHandler.js'
import { errorHandler } from '@/utils/index.js'
export default {
    mixins: [taskHandler],
    components: {
        TaskList: () => import('../../TaskList/TaskList'),
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        TaskAside: () => import('../TaskAside.vue')
    },
    props: {
        task: {
            type: Object,
            default: () => null
        },
        reloadTask: {
            type: Function,
            default: () => {}
        },
        myTask: {
            type: Boolean,
            default: false
        },
        edit: {
            type: Function,
            default: () => {}
        },
        openTask: {
            type: Function,
            default: () => {}
        },
        dropActions: {
            type: Object,
            default: () => null
        },
        isMobile: {
            type: Boolean,
            default: false
        },
        closeDrawer: {
            type: Function,
            default: () => {}
        },
        bodyWrap: {
            type: Function,
            default: () => {}
        }
    },
    data() {
        return {
            priorityList,
            expanded: 'comments',
            taskVote: {},
            taskVoteLoading: false
        }
    },
    computed: {
        taskUsers() {
            const list = []

            const pushUser = user => {
                if (user && user.id) list.push(user)
            }

            pushUser(this.task?.author)
            pushUser(this.task?.operator)
            pushUser(this.task?.owner)

            if (Array.isArray(this.task?.visors)) {
                this.task.visors.forEach(pushUser)
            }

            if (Array.isArray(this.task?.cooperators)) {
                this.task.cooperators.forEach(item => {
                    if (item?.user) pushUser(item.user)
                    else pushUser(item)
                })
            }

            const uniq = new Map()
            list.forEach(u => {
                const key = String(u.id)
                if (!uniq.has(key)) uniq.set(key, u)
            })

            const currentUserId = this.user?.id

            return Array
                .from(uniq.values())
                .filter(u => String(u.id) !== String(currentUserId))
        },
        sprintOpen() {
            const query = this.$route.query
            if(query?.sprint)
                return true
            return false
        },
        groupOpen() {
            const query = this.$route.query
            if(query?.viewGroup || query?.sprint) {
                return true
            }
            return false
        },
        projectOpen() {
            const query = this.$route.query
            if(query?.viewProject || query?.sprint) {
                return true
            }
            return false
        },
        asideSetting() {
            return this.task.aside_settings ? this.task.aside_settings : null 
        },
        priorityCheck() {
            const find = this.priorityList.find(item => item.value === this.task.priority)
            if(find)
                return find
            else
                return null
        },
        user() {
            return this.$store.state.user.user
        },
        myVote() {
            if(this.taskVote.my_vote === null)
                return null
            if(this.taskVote.my_vote)
                return 'like'
            return 'dislike'
            
        }
    },
    created() {
        this.taskVoteLoading = true
        this.$http(`vote/${this.task.id}/`)
            .then(({ data }) => {
                this.taskVote = data
            })
            .catch(error => {
                console.error(error)
            })
            .finally(() => {
                this.taskVoteLoading = false
            }) 
    },
    methods: {
        openSprint(id) {
            if(!this.sprintOpen) {
                this.closeDrawer({sprint: id})
            }
        },
        openProject(type, item) {
            if(!this.projectOpen)
                this.closeDrawer({[type]: item.id})
        },
        openWorkgroup(type, item) {
            if(!this.groupOpen)
                this.closeDrawer({[type]: item.id})
        },

        /** @param {string} choice принимает 'like' или 'dislike' */
        async vote(choice) {
            let boolChoice,
                fieldToVote,
                oppositeFieldToVote
            if (choice === 'like') {
                fieldToVote = 'likes_count'
                oppositeFieldToVote = 'dislikes_count'
                boolChoice = true
            } else if (choice === 'dislike') {
                fieldToVote = 'dislikes_count'
                oppositeFieldToVote = 'likes_count'
                boolChoice = false
            }
            const payload = {
                vote: boolChoice
            }

            await this.$http.post(`vote/${this.task.id}/`, payload)
                .then(() => {
                    if(this.taskVote.my_vote !== null) {
                        if(this.taskVote.my_vote === boolChoice) {
                            this.taskVote[fieldToVote] += -1
                            this.taskVote.my_vote = null
                        } else {
                            this.taskVote[oppositeFieldToVote] += -1
                            this.taskVote[fieldToVote] += 1
                            this.taskVote.my_vote = boolChoice
                        }
                    } else {
                        this.taskVote[fieldToVote] += 1
                        this.taskVote.my_vote = boolChoice
                    }
                })
                .catch(error => {
                    errorHandler({error})
                })
        },
        workgroupLogoPath(workgroup) {
            return workgroup?.workgroup_logo?.path || ''
        },
    },

}
</script>

<style lang="scss" scoped>
.task_info_collapse {
    margin-left: -15px;
    margin-right: -15px;
    ::v-deep {
        .ant-collapse-header {
            font-weight: 500;
        }
        .ant-collapse-borderless{
            background: #F8F9FD;
        }
    }
    
}
.bg-light-gray {
    background-color: #EFF2F5;
}
</style>
