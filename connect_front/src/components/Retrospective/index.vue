<template>
    <div ref="wrapper" :class="wrapperClass">
        <div class="retrospective">
            <div class="item_card">
                <div class="item_card__header py-2 flex justify-between items-center item-title">
                    <div class="card_label">{{ plusesBlockLabel }}</div>
                    <a-button 
                        type="link" 
                        flaticon 
                        size="small"
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        content="Добавить"
                        shape="circle"
                        icon="fi-rr-add"
                        @click="addHandler('pluses')" />
                </div>
                <div class="item_card__wrapper">
                    <a-spin :spinning="listLoading.pluses" class="w-full" size="small">
                        <div class="item_scroll_wrap">
                            <div v-if="empty.pluses" class="flex justify-center">
                                <a-button type="flat_primary" class="mt-3 mb-1 px-8" @click="addHandler('pluses')">
                                    Добавить
                                </a-button>
                            </div>
                            <div v-for="item in list['pluses']" :key="item.id" class="r_card">
                                <div class="r_card__header">
                                    <Profiler 
                                        :avatarSize="22"
                                        nameClass="text-sm"
                                        hideSupportTag
                                        :user="item.author" />
                                    <div v-if="item.author && user && user.id === item.author.id" class="flex items-center pl-2">
                                        <a-button 
                                            type="ui" 
                                            size="small" 
                                            ghost
                                            v-tippy="{ inertia : true, duration : '[600,300]'}"
                                            content="Редактировать"
                                            flaticon
                                            shape="circle"
                                            icon="fi-rr-edit"
                                            @click="editHandler(item)" />
                                        <a-dropdown :getPopupContainer="getPopupContainer">
                                            <a-button 
                                                type="ui" 
                                                size="small" 
                                                ghost
                                                flaticon
                                                class="ml-1"
                                                shape="circle"
                                                icon="fi-rr-menu-dots-vertical" />
                                            <a-menu slot="overlay">
                                                <a-menu-item class="text_red" @click="deleteItem(item)">
                                                    Удалить
                                                </a-menu-item>
                                            </a-menu>
                                        </a-dropdown>
                                    </div>
                                </div>
                                <div class="r_card__body">
                                    <p class="card_text">{{ expandedItems[item.id] ? item.content : truncateText(item.content, maxLength) }}</p>
                                    <a-button 
                                        v-if="item.content.length > maxLength" 
                                        type="link"
                                        size="small" 
                                        class="mt-1 px-0 py-0"
                                        @click="toggleExpand(item.id)">
                                        {{ expandedItems[item.id] ? 'Скрыть' : 'Подробнее' }}
                                    </a-button>
                                    <div class="date mt-2">{{ $moment(item.created_at).format('DD.MM.YYYY HH:mm') }}</div>
                                </div>
                            </div>
                        </div>
                    </a-spin>
                </div>
            </div>
            <div class="item_card">
                <div class="item_card__header py-2 flex justify-between items-center item-title">
                    <div class="card_label">{{ minusesBlockLabel }}</div>
                    <a-button 
                        type="link" 
                        flaticon 
                        size="small"
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        content="Добавить"
                        shape="circle"
                        icon="fi-rr-add"
                        @click="addHandler('minuses')" />
                </div>
                <div class="item_card__wrapper">
                    <a-spin :spinning="listLoading.minuses" class="w-full" size="small">
                        <div class="item_scroll_wrap">
                            <div v-if="empty.minuses" class="flex justify-center">
                                <a-button type="flat_primary" class="mt-3 mb-1 px-8" @click="addHandler('minuses')">
                                    Добавить
                                </a-button>
                            </div>
                            <div v-for="item in list['minuses']" :key="item.id" class="r_card">
                                <div class="r_card__header">
                                    <Profiler 
                                        :avatarSize="22"
                                        nameClass="text-sm"
                                        hideSupportTag
                                        :user="item.author" />
                                    <div v-if="item.author && user && user.id === item.author.id" class="flex items-center pl-2">
                                        <a-button 
                                            type="ui" 
                                            size="small" 
                                            ghost
                                            v-tippy="{ inertia : true, duration : '[600,300]'}"
                                            content="Редактировать"
                                            flaticon
                                            shape="circle"
                                            icon="fi-rr-edit"
                                            @click="editHandler(item)" />
                                        <a-dropdown :getPopupContainer="getPopupContainer">
                                            <a-button 
                                                type="ui" 
                                                size="small" 
                                                ghost
                                                flaticon
                                                class="ml-1"
                                                shape="circle"
                                                icon="fi-rr-menu-dots-vertical" />
                                            <a-menu slot="overlay">
                                                <a-menu-item class="text_red" @click="deleteItem(item)">
                                                    Удалить
                                                </a-menu-item>
                                            </a-menu>
                                        </a-dropdown>
                                    </div>
                                </div>
                                <div class="r_card__body">
                                    <p class="card_text">{{ expandedItems[item.id] ? item.content : truncateText(item.content, maxLength) }}</p>
                                    <a-button 
                                        v-if="item.content.length > maxLength" 
                                        type="link"
                                        size="small" 
                                        class="mt-1 px-0 py-0"
                                        @click="toggleExpand(item.id)">
                                        {{ expandedItems[item.id] ? 'Скрыть' : 'Подробнее' }}
                                    </a-button>
                                    <div class="date mt-2">{{ $moment(item.created_at).format('DD.MM.YYYY HH:mm') }}</div>
                                </div>
                            </div>
                        </div>
                    </a-spin>
                </div>
            </div>
            <div class="item_card">
                <div class="item_card__header py-2 flex justify-between items-center item-title">
                    <div class="card_label">{{ ideasBlockLabel }}</div>
                    <a-button 
                        type="link" 
                        flaticon 
                        size="small"
                        v-tippy="{ inertia : true, duration : '[600,300]'}"
                        content="Добавить"
                        shape="circle"
                        icon="fi-rr-add"
                        @click="addHandler('ideas')" />
                </div>
                <div class="item_card__wrapper">
                    <a-spin :spinning="listLoading.ideas" class="w-full" size="small">
                        <div class="item_scroll_wrap">
                            <div v-if="empty.ideas" class="flex justify-center">
                                <a-button type="flat_primary" class="mt-3 mb-1 px-8" @click="addHandler('ideas')">
                                    Добавить
                                </a-button>
                            </div>
                            <div v-for="item in list['ideas']" :key="item.id" class="r_card">
                                <div class="r_card__header">
                                    <Profiler 
                                        :avatarSize="22"
                                        nameClass="text-sm"
                                        hideSupportTag
                                        :user="item.author" />
                                    <div v-if="item.author && user && user.id === item.author.id" class="flex items-center pl-2">
                                        <a-button 
                                            type="ui" 
                                            size="small" 
                                            ghost
                                            v-tippy="{ inertia : true, duration : '[600,300]'}"
                                            content="Редактировать"
                                            flaticon
                                            shape="circle"
                                            icon="fi-rr-edit"
                                            @click="editHandler(item)" />
                                        <a-dropdown :getPopupContainer="getPopupContainer">
                                            <a-button 
                                                type="ui" 
                                                size="small" 
                                                ghost
                                                flaticon
                                                class="ml-1"
                                                shape="circle"
                                                icon="fi-rr-menu-dots-vertical" />
                                            <a-menu slot="overlay">
                                                <a-menu-item class="text_red" @click="deleteItem(item)">
                                                    Удалить
                                                </a-menu-item>
                                            </a-menu>
                                        </a-dropdown>
                                    </div>
                                </div>
                                <div class="r_card__body">
                                    <p class="card_text">{{ expandedItems[item.id] ? item.content : truncateText(item.content, maxLength) }}</p>
                                    <a-button 
                                        v-if="item.content.length > maxLength" 
                                        type="link"
                                        size="small" 
                                        class="mt-1 px-0 py-0"
                                        @click="toggleExpand(item.id)">
                                        {{ expandedItems[item.id] ? 'Скрыть' : 'Подробнее' }}
                                    </a-button>
                                    <div class="date mt-2">{{ $moment(item.created_at).format('DD.MM.YYYY HH:mm') }}</div>
                                </div>
                            </div>
                        </div>
                    </a-spin>
                </div>
            </div>
        </div>
        <a-modal
            :title="edit ? 'Редактировать ретроспективу' : 'Добавить ретроспективу'"
            :footer="false"
            :afterClose="afterClose"
            :visible="visible"
            @cancel="visible = false">
            <a-form-model
                ref="ruleForm"
                :model="form"
                :rules="rules">
                <a-form-model-item ref="content" prop="content">
                    <template v-if="!edit" #label>
                        <template v-if="form.retrospective_type === 'pluses'">
                            {{ plusesBlockLabel }}
                        </template>
                        <template v-if="form.retrospective_type === 'minuses'">
                            {{ minusesBlockLabel }}
                        </template>
                        <template v-if="form.retrospective_type === 'ideas'">
                            {{ ideasBlockLabel }}
                        </template>
                    </template>
                    <a-textarea
                        v-model="form.content"
                        placeholder="Введите текст"
                        :auto-size="{ minRows: 4, maxRows: 10 }"
                        @change="handleBodyChange" />
                    <div class="body_length flex justify-end" style="opacity: 0.6;">
                        {{form.content.length}}/{{ bodyMaxCount }}
                    </div>
                </a-form-model-item>
                <a-button type="primary" :loading="loading" size="large" block @click="formSubmit()">
                    Сохранить
                </a-button>
            </a-form-model>
        </a-modal>
    </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
    name: 'Retrospective',
    computed: {
        ...mapState({
            user: state => state.user.user,
        })
    },
    props: {
        related_object: {
            type: Object,
            required: true
        },
        wrapperClass: {
            type: String,
            default: ''
        },
        plusesBlockLabel : {
            type:String,
            default: 'Плюсы. Что помогло?'
        },
        minusesBlockLabel : {
            type:String,
            default: 'Минусы. Что мешало?'
        },
        ideasBlockLabel : {
            type:String,
            default: 'Идеи. Как улучшить работу?'
        },
    },
    data() {
        return {
            bodyMaxCount: 1000,
            maxLength: 250,
            visible: false,
            loading: false,
            expandedItems: {},
            list: {
                pluses: [],
                ideas: [],
                minuses: []
            },
            empty: {
                pluses: false,
                ideas: false,
                minuses: false
            },
            listLoading: {
                pluses: false,
                ideas: false,
                minuses: false
            },
            edit: false,
            form: {
                content: "",
                retrospective_type: "pluses",
                related_object: null
            },
            rules: {
                content: [
                    { required: true, message: 'Обязательно для заполнения', trigger: 'blur' }
                ]
            }
        }
    },
    created() {
        this.listLoad()
    },
    methods: {
        handleBodyChange(event) {
            const value = event.target.value.slice(0, this.bodyMaxCount)
            this.$set(this.form, 'content', value)
        },
        toggleExpand(id) {
            this.$set(this.expandedItems, id, !this.expandedItems[id]);
        },
        truncateText(text, length) {
            return text.length > length ? text.substring(0, length) + '...' : text;
        },
        listLoad() {
            this.getRetrospective('pluses')
            this.getRetrospective('ideas')
            this.getRetrospective('minuses')
        },
        afterClose() {
            this.edit = false
            this.form = {
                content: "",
                retrospective_type: "pluses",
                related_object: null
            }
        },
        getPopupContainer() {
            return this.$refs.wrapper
        },
        addHandler(type) {
            this.form.retrospective_type = type
            this.visible = true
        },
        deleteItem(item) {
            this.$confirm({
                title: 'Вы действительно хотите удалить ретроспективу',
                content: '',
                okText: 'Удалить',
                okType: 'danger',
                zIndex: 2000,
                getContainer: this.getPopupContainer,
                closable: true,
                maskClosable: true,
                cancelText: 'Закрыть',
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.post('/table_actions/update_is_active/', {
                            id: item.id,
                            is_active: false
                        })
                            .then(() => {
                                this.$message.success('Ретроспектива успешно удалена')
                                this.listLoad()
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                reject(e)
                            })
                    })
                }
            })
        },
        async getRetrospective(type) {
            try {
                this.listLoading[type] = true
                const { data } = await this.$http.get('/retrospective/', {
                    params: {
                        page_size: 100,
                        retrospective_type: type,
                        related_object: this.related_object.id
                    }
                })
                if(data) {
                    if(data.results.length) {
                        this.empty[type] = false
                    } else {
                        this.empty[type] = true
                    }
                    this.list[type] = data.results
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.listLoading[type] = false
            }
        },
        editHandler(item) {
            this.edit = true
            this.form = {...item}
            this.visible = true
        },
        formSubmit() {
            this.$refs.ruleForm.validate(async valid => {
                if (valid) {
                    const queryData = {...this.form}
                    queryData.related_object = this.related_object.id
                    if(this.edit) {
                        try {
                            this.loading = true
                            const { data } = await this.$http.put(`/retrospective/${queryData.id}/`, queryData)
                            if(data) {
                                this.visible = false
                                this.listLoad()
                                this.$message.success('Ретроспектива успешно обновлена')
                            }
                        } catch(e) {
                            console.log(e)
                        } finally {
                            this.loading = false
                        }
                    } else {
                        try {
                            this.loading = true
                            const { data } = await this.$http.post('/retrospective/', queryData)
                            if(data) {
                                this.visible = false
                                this.listLoad()
                                this.$message.success('Ретроспектива успешно создана')
                            }
                        } catch(e) {
                            console.log(e)
                        } finally {
                            this.loading = false
                        }
                    }
                } else {
                    return false
                }
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.retrospective {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 0.75rem;

    @media (min-width: 768px) {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    @media (min-width: 1400px) {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .r_card{
        box-shadow: 0 1px 0 rgba(9, 30, 66, .15);
        border: 0;
        border-radius: var(--borderRadius);
        background: #fff;
        padding: 10px;
        color: #000;
        &:not(:last-child){
            margin-bottom: 10px;
        }
        &__header{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .card_text{
            opacity: 0.6;
            word-break: break-word;
        }
        .date{
            opacity: 0.6;
        }
    }
    .item_card{
        width: 100%;
        height: 100%;
        scroll-snap-align: start;
        background-color: #eff2f5;
        border-radius: var(--borderRadius);
        padding-bottom: 5px;
        overflow: hidden;
        &:not(:last-child){
            margin-bottom: 0;
        }
        &__header{
            padding-left: 10px;
            padding-right: 10px;
            color: #000;
        }
        &__wrapper{
            height: calc(100% - 40px);
            .item_scroll_wrap{
                padding-left: 7px;
                padding-right: 7px;
                height: 100%;
                overflow-y: auto;
                overflow-x: hidden;
                padding-block: 5px;
            }
        }
    }
}
</style>
