<template>
    <div class="repair_card">
        <div class="card_row">
            <div class="col_2 md:flex items-center">
                <div class="repair_card__row">
                    <div class="label">{{ $t('sports.repairDate') }}</div>
                    <div class="value">{{ $moment(item.renovation_date).format('DD.MM.YYYY') }}</div>
                </div>
                <div class="repair_card__row">
                    <div class="label">{{ $t('sports.amount') }}</div>
                    <div class="value">{{ item.amount }}</div>
                </div>
                <div v-if="item.renovation_type" class="repair_card__row">
                    <div class="label">{{ $t('sports.repairType') }}</div>
                    <div class="value">{{ item.renovation_type.name }}</div>
                </div>
                <div v-if="item.comment" class="repair_card__row">
                    <div class="label">{{ $t('sports.comment') }}</div>
                    <div class="value">{{ item.comment }}</div>
                </div>
            </div>
            <div class="work_types">
                <div class="work_types__label">{{ $t('sports.work_types_card') }}</div>
                <ul>
                    <li v-for="(work, index) in works" :key="index">
                        <template v-if="work.label">{{ work.label }}:</template> <span>{{ work.value }}</span>
                    </li>
                </ul>
                <div v-if="item.attachments.length" class="files_wrap mt-3">
                    <div class="w_label">Прикреплённые файлы</div>
                    <div class="files_list">
                        <a 
                            v-for="file in item.attachments" 
                            :key="file.id" 
                            target="_blank" 
                            :href="file.path"
                            class="file_card truncate">
                            <div class="flex items-center mr-4 truncate">
                                <i class="fi fi-rr-document file_ico mr-2"></i>
                                <span class="truncate">{{ file.name }}</span>
                            </div>
                        </a>
                    </div>
                </div>
            </div>
        </div>
        <div v-if="actions && actions.renovation_info && actions.renovation_info.availability" class="actions">
            <a-button 
                type="primary"
                class="md:ml-1"
                size="large"
                flaticon
                v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                :content="$t('sports.edit')"
                :block="isMobile"
                icon="fi-rr-edit"
                @click="editItem()">
                <template v-if="isMobile">
                    {{ $t('sports.edit') }}
                </template>
            </a-button>
            <a-button 
                type="danger"
                class="md:ml-1"
                size="large"
                v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"
                :content="$t('sports.delete')"
                flaticon
                :block="isMobile"
                icon="fi-rr-trash"
                @click="deleteItem()">
                <template v-if="isMobile">
                    {{ $t('sports.delete') }}
                </template>
            </a-button>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { mapState } from 'vuex'
export default {
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapState({
            actions: state => state.facilities.projectActions
        }),
        isMobile() {
            return this.$store.state.isMobile
        },
        works() {
            if(this.item.works?.length) {
                return this.item.works.map(work => {
                    return {
                        label: work.work_type?.parent?.full_name || null,
                        value: work.work_type.full_name
                    }
                })
            }
            return []
        }
    },
    methods: {
        editItem() {
            eventBus.$emit('edit_repair_info', this.item)
        },
        deleteItem() {
            this.$confirm({
                title: this.$t('sports.repairDeleteMessage'),
                content: '',
                okText: this.$t('sports.delete'),
                okType: 'danger',
                zIndex: 2000,
                closable: true,
                maskClosable: true,
                cancelText: this.$t('sports.close'),
                onOk: () => {
                    return new Promise((resolve, reject) => {
                        this.$http.delete(`/sports_facilities/renovation/${this.item.id}/`)
                            .then(() => {
                                this.$message.success(this.$t('sports.repairDeleted'))
                                eventBus.$emit('repair_list_reload')
                                resolve()
                            })
                            .catch(e => {
                                console.log(e)
                                this.$message.error(this.$t('sports.deletedError'))
                                reject(e)
                            })
                    })
                }
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.repair_card{
    padding: 15px;
    border: 1px solid var(--border2);
    border-radius: var(--borderRadius);
    background: #ffffff;
    margin-bottom: 20px;
    color: #000;
    @media (min-width: 768px) {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
    }
    @media (min-width: 992px) {
        padding: 30px;
    }
    &__row{
        .label{
            opacity: 0.6;
            margin-bottom: 5px;
        }
        &:not(:last-child){
            margin-bottom: 10px;
            @media (min-width: 768px) {
                margin-right: 40px;
                margin-bottom: 0px;
            }
        }
    }
    .work_types{
        margin-top: 20px;
        &__label{
            opacity: 0.6;
            margin-bottom: 10px;
        }
    }
    ul{
        padding-left: 15px;
        li{
            list-style: disc;
            &:not(:last-child){
                margin-bottom: 10px;
            }
            span{
                opacity: 0.6;
            }
        }
    }
    .actions{
        display: flex;
        align-items: center;
        @media (max-width: 767px) {
            margin-top: 15px;
            display: grid;
            gap: 10px;
            grid-template-columns: 1fr 1fr;
        }
    }
    .files_wrap{
        .w_label{
            color: #000;
            opacity: 0.6;
            margin-bottom: 5px;
            line-height: 20px;
        }
    }
    .files_list{
        @media (min-width: 768px) {
            display: flex;
            flex-wrap: wrap;
        }
        .file_card{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
            border: 1px solid #D9D9D9;
            border-radius: 4px;
            padding: 10px 15px;
            color: #000;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            .file_ico{
                font-size: 28px;
                opacity: 0.4;
            }
            &:hover{
                border-color: var(--blue);
            }
            @media (min-width: 768px) {
                margin-right: 10px;
                max-width: 300px;
            }
        }
    }
}
</style>