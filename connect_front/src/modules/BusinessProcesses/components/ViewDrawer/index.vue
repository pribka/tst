<template>
    <a-drawer
        :visible="visible"
        class="b_process_show_drawer"
        @close="visible = false"
        destroyOnClose
        :zIndex="1100"
        :width="600"
        placement="right">
        <div class="drawer_header">
            <a-skeleton
                v-if="loading"
                active
                :paragraph="{ rows: 1 }" />
            <div v-else class="title truncate">
                <template v-if="process">
                    {{ process.name }}
                </template>
            </div>
            <div class="drawer_actions flex items-center">
                <div 
                    v-if="process" 
                    class="mr-2">
                    <a-tag :color="statusColor">
                        {{ statusText }}
                    </a-tag>
                </div>
                <a-button
                    @click="visible = false"
                    class="text-current"
                    type="link" 
                    icon="close" />
            </div>
        </div>
        <div class="drawer_body">
            <div class="drawer_tabs">
                <a-tabs v-model="tab">
                    <a-tab-pane 
                        key="1" 
                        tab="Описание" />
                    <a-tab-pane 
                        key="2" 
                        tab="Движение заявки" />
                </a-tabs>
            </div>
            <div class="drawer_content">
                <div 
                    v-if="loading" 
                    class="loader_wrap">
                    <a-skeleton 
                        :paragraph="{ rows: 10 }"
                        active />
                </div>
                <template v-if="process">
                    <a-tabs :activeKey="tab">
                        <a-tab-pane 
                            key="1" 
                            tab="Описание">
                            <div class="body_list">
                                <div 
                                    class="body_item">
                                    <label>Дата создания:</label>
                                    <div class="val">
                                        {{$moment(process.created_at).format('DD.MM.YYYY HH:mm')}}
                                    </div>
                                </div>
                                <div
                                    v-if="process.finished_date"
                                    class="body_item">
                                    <label>Дата закрытия:</label>
                                    <div class="val">
                                        {{$moment(process.finished_date).format('DD.MM.YYYY HH:mm')}}
                                    </div>
                                </div>
                                <div 
                                    class="body_item">
                                    <label>Крайний срок:</label>
                                    <div class="val">
                                        <DeadLine :date="process.dead_line" />
                                    </div>
                                </div>
                                <div 
                                    v-if="process.owner" 
                                    class="body_item">
                                    <label>Автор:</label>
                                    <div class="val">
                                        <Profiler
                                            :avatarSize="22"
                                            nameClass="text-sm"
                                            :user="process.owner" />
                                    </div>
                                </div>
                                <div 
                                    v-if="process.operators && process.operators.length && process.status !== 'rejected' && process.status !== 'approved'" 
                                    class="body_item">
                                    <label>Ответственный на текущем шагу:</label>
                                    <div class="val">
                                        <a-skeleton
                                            v-if="reloadLoading"
                                            active
                                            :paragraph="{ rows: 1 }" />
                                        <div
                                            v-else
                                            class="op_list_item"
                                            v-for="op in process.operators" 
                                            :key="op.id">
                                            <Profiler
                                                :avatarSize="22"
                                                nameClass="text-sm"
                                                :user="op" />
                                        </div>
                                    </div>
                                </div>
                                <div 
                                    v-if="process.itinerary" 
                                    class="body_item">
                                    <label>Тип заявки:</label>
                                    <div class="val">
                                        {{ process.itinerary.name }}
                                    </div>
                                </div>
                                <div 
                                    v-if="process.amount_of_money" 
                                    class="body_item">
                                    <label>Сумма (тг):</label>
                                    <div class="val">
                                        {{ processAmount }}
                                    </div>
                                </div>
                                <div 
                                    v-if="process.attachments && process.attachments.length" 
                                    class="body_item_files">
                                    <label>Файлы:</label>
                                    <div class="val">
                                        <div 
                                            v-for="file in process.attachments" 
                                            :key="file.id"
                                            class="file flex items-center justify-between">
                                            <a 
                                                :href="file.path" 
                                                target="_blank">
                                                {{ file.name }}
                                            </a>
                                            <a-dropdown 
                                                class="ml-2" 
                                                :trigger="['click']">
                                                <a-button 
                                                    icon="more" 
                                                    size="small" />
                                                <a-menu slot="overlay">
                                                    <a-menu-item 
                                                        key="task" 
                                                        @click="createTask(file)">
                                                        Создать задачу
                                                    </a-menu-item>
                                                    <a-menu-item 
                                                        key="share" 
                                                        @click="fileShare(file)">
                                                        Поделиться
                                                    </a-menu-item>
                                                </a-menu>
                                            </a-dropdown>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div 
                                v-if="process.description" 
                                class="desc" 
                                v-html="process.description" />
                        </a-tab-pane>
                        <a-tab-pane 
                            key="2" 
                            tab="Движение заявки">
                            <TimeLine 
                                :process="process" 
                                :reloadLoading="reloadLoading" />
                        </a-tab-pane>
                    </a-tabs>
                </template>
            </div>
        </div>
        <div class="drawer_footer">
            <a-skeleton
                v-if="loading || reloadLoading"
                active
                :paragraph="{ rows: 1 }" />
            <template v-if="process && !reloadLoading">
                <a-button-group>
                    <template v-if="isOperator && process.status !== 'rejected' && process.status !== 'approved'">
                        <a-button 
                            class="btn"
                            icon="check"
                            :loading="approveLoading"
                            @click="approve()">
                            Утвердить
                        </a-button>
                        <a-button 
                            class="btn" 
                            icon="stop"
                            @click="rejectVisible = true">
                            Отклонить
                        </a-button>
                    </template>
                    <a-dropdown :getPopupContainer="getPopupContainer">
                        <a-menu slot="overlay">
                            <a-menu-item 
                                key="1" 
                                @click="share()">
                                Поделиться
                            </a-menu-item>
                            <template v-if="isAuthor">
                                <a-menu-divider />
                                <a-menu-item 
                                    key="3" 
                                    class="text_red"
                                    @click="deleteHandler()">
                                    Удалить
                                </a-menu-item>
                            </template>
                        </a-menu>
                        <a-button icon="more" />
                    </a-dropdown>
                </a-button-group>
            </template>
        </div>
        <a-modal 
            v-model="rejectVisible"
            :zIndex="2000"
            title="Отклонить заявку">
            <div class="mb-2">
                <a-textarea
                    v-model="comment"
                    placeholder="Введите комментарий"
                    :auto-size="{ minRows: 4, maxRows: 8 }"/>
            </div>
            <Upload
                v-model="attachments"
                :defaultList="fileList"
                multiple />
            <template slot="footer">
                <a-button 
                    :loading="rejectLoading" 
                    type="primary"
                    @click="reject()">
                    Отклонить
                </a-button>
            </template>
        </a-modal>
    </a-drawer>
</template>

<script>
import { numberWithSpaces, statusTextSwitch, statusColorSwitch } from '../../utils'
import eventBus from '@/utils/eventBus'
import eventBus2 from '../../utils/eventBus'
import { mapState } from 'vuex'
import DeadLine from '../DeadLine.vue'
import TimeLine from './TimeLine.vue'
import Upload from '@apps/Upload'
export default {
    components: {
        TimeLine,
        Upload,
        DeadLine
    },
    computed: {
        ...mapState({
            user: state => state.user.user
        }),
        isAuthor() {
            if(this.user && this.user.id === this.process.author.id)
                return true
            else
                return false
        },
        isOperator() {
            if(this.user) {
                const find = this.process.operators.find(f => f.id === this.user.id)
                if(find)
                    return true
                else
                    return false
            } else 
                return false
        },
        statusText() {
            return statusTextSwitch(this.process.status)
        },
        statusColor() {
            return statusColorSwitch(this.process.status)
        },
        processAmount() {
            return numberWithSpaces(this.process.amount_of_money)
        }
    },
    data() {
        return {
            visible: false,
            process: null,
            loading: false,
            approveLoading: false,
            rejectLoading: false,
            reloadLoading: false,
            tab: '1',
            rejectVisible: false,
            comment: '',
            attachments: [],
            fileList: []
        }
    },
    watch: {
        '$route.name'() {
            if(this.$route.query?.bprocess)
                this.visible = false
        },
        '$route.query.bprocess'(val) {
            if(val && !this.visible)
                this.openDrawer()
        },
        visible(val) {
            if(val)
                this.getProcess()
            else
                this.close()
        }
    },
    methods: {
        async approve() {
            try {
                this.approveLoading = true
                const { data } = await this.$http.put(`/processes/financial_application/${this.process.id}/approve/`)
                if(data === 'ok') {
                    this.$message.success('Заявка одобрена')
                    this.getReloadProcess()
                }
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка')
            } finally {
                this.approveLoading = false
            }
        },
        async reject() {
            try {
                this.rejectLoading = true
                const { data } = await this.$http.put(`/processes/financial_application/${this.process.id}/reject/`, {
                    comment: this.comment,
                    attachments: this.attachments
                })
                if(data === 'ok') {
                    this.$message.success('Заявка отклонена')
                    this.getReloadProcess()
                    this.rejectVisible = false
                }
            } catch(e) {
                console.log(e)
                this.$message.error('Ошибка')
            } finally {
                this.rejectLoading = false
            }
        },
        getPopupContainer() {
            return document.querySelector('.b_process_show_drawer .drawer_footer')
        },
        deleteHandler() {
            this.$confirm({
                title: 'Предупреждение',
                content: 'Вы действительно хотите удалить заявку?',
                zIndex: 1500,
                cancelText: 'Закрыть',
                okText: 'Удалить',
                okType: 'danger',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', [{ id: this.process.id, is_active: false }])
                            .then(() => {
                                this.$message.success('Заявка удалена')
                                eventBus2.$emit('DELETE_PROCESS', this.process)
                                this.visible = false
                                resolve()
                            })
                            .catch((e) => {
                                console.log(e)
                                reject()
                            })
                    })
                },
                onCancel() {}
            })
        },
        fileShare(file) {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'files',
                shareId: file.id,
                object: file,
                bodySelector: '.task_body_wrap',
                shareUrl: file.path,
                shareTitle: `Файл - ${file.name}`
            })
        },
        share() {
            this.$store.commit('share/SET_SHARE_PARAMS', {
                model: 'files',
                shareId: this.process.id,
                object: this.process,
                bodySelector: '.task_body_wrap',
                shareUrl: `${window.location.origin}/ru/dashboard?bprocess=${this.process.id}`,
                shareTitle: `Заявка - ${this.process.name}`
            })
        },
        async createTask(file) {
            this.$store.commit('task/SET_TASK_DRAWER_ZINDEX', 1300)
            let query = Object.assign({}, this.$route.query)

            if(query && query.task) {
                this.$store.commit('task/CHANGE_TASK_SHOW', false)
                delete query.task
                await this.$router.push({query})
            }

            let form = {
                attachments: [file],
                reason_model: 'files',
                reason_id: file.id
            }
            eventBus.$emit('ADD_WATCH', {type: 'add_task', data: form})
        },
        close() {
            this.process = null
            this.comment = ''
            this.attachments = []
            this.fileList = []
            let query = Object.assign({}, this.$route.query)
            if(query.bprocess) {
                delete query.bprocess
                this.$router.push({query})
            }
        },
        async getReloadProcess() {
            try {
                this.reloadLoading = true
                const { data } = await this.$http.get(`processes/financial_application/${this.$route.query.bprocess}/`)
                if(data) {
                    this.process = data
                    eventBus2.$emit('UPDATE_PROCESS_LIST', data)
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.reloadLoading = false
            }
        },
        async getProcess() {
            try {
                this.loading = true
                const { data } = await this.$http.get(`processes/financial_application/${this.$route.query.bprocess}/`)
                if(data) {
                    this.process = data
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        openDrawer() {
            this.visible = true
        }
    }
}
</script>

<style lang="scss">
.b_process_show_drawer{
    .ant-drawer-header-no-title{
        display: none;
    }
    .ant-drawer-content,
    .ant-drawer-wrapper-body{
        overflow: hidden;
    }
    .ant-drawer-body{
        height: 100%;
        padding: 0px;
    }
    .drawer_header{
        display: flex;
        align-items: center;
        height: 40px;
        border-bottom: 1px solid #e8e8e8;
        padding-left: 20px;
        padding-right: 20px;
        justify-content: space-between;
        .ant-skeleton-title{
            margin: 0px;
        }
        .ant-skeleton-paragraph{
            display: none;
        }
        .title{
            margin: 0;
            color: rgba(0, 0, 0, 0.85);
            font-weight: 500;
            font-size: 16px;
            line-height: 22px;
        }
    }
    .drawer_body{
        height: calc(100% - 80px);
        .drawer_tabs{
            .ant-tabs-bar{
                margin: 0px;
            }
        }
        .drawer_content{
            height: calc(100% - 44px);
            overflow-y: auto;
            overflow-x: hidden;
            .loader_wrap{
                padding: 20px;
            }
            .ant-tabs-tabpane{
                padding: 20px;
            }
            .ant-tabs-bar{
                display: none;
            }
        }
        .desc{
            line-height: 24px;
        }
        .body_list{
            margin-bottom: 30px;
        }
        .body_item_files{
            label{
                font-weight: 600;
                margin-bottom: 5px;
                display: block;
            }
            &:not(:last-child){
                margin-bottom: 15px;
                border-bottom: 1px solid #e8e8e8;
                padding-bottom: 15px;
            }
            .file{
                &:not(:last-child){
                    margin-bottom: 13px;
                }
            }
        }
        .body_item{
            display: flex;
            align-items: center;
            .ant-skeleton{
                width: 350px;
            }
            .ant-skeleton-title{
                margin: 0px;
            }
            .ant-skeleton-paragraph{
                display: none;
            }
            .op_list_item{
                &:not(:last-child){
                    margin-bottom: 10px;
                }
            }
            label{
                font-weight: 600;
                margin-right: 30px;
                display: block;
                width: 150px;
            }
            &:not(:last-child){
                margin-bottom: 15px;
                border-bottom: 1px solid #e8e8e8;
                padding-bottom: 15px;
            }
        }
    }
    .drawer_footer{
        display: flex;
        align-items: center;
        height: 40px;
        border-top: 1px solid #e8e8e8;
        padding-left: 20px;
        padding-right: 20px;
        .btn{
            display: flex;
            align-items: center;
            .anticon-check{
                color: var(--green);
            }
            .anticon-stop{
                color: var(--errorRed);
            }
        }
        .ant-skeleton-title{
            margin: 0px;
        }
        .ant-skeleton-paragraph{
            display: none;
        }
    }
}
</style>