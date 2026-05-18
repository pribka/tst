<template>
    <div class="rationale" ref="rationaleComponent">
        <div class="rationale-set">
            <div class="specificity">
                <span>Специфика: </span>
                <span v-if="proposal.specificity?.code">
                    {{ proposal.specificity.code }} - {{ proposal.specificity.name }}
                </span>
                <span v-else class="no-data">
                    Не указана
                </span>
            </div>

            <div class="rationale-select">
                <div class="ant-col ant-form-item-label ant-form-item-required">Выберите обоснование:</div>
                <div :class="error && 'ant-form-item-control has-error'">
                    <a-select
                        v-model="proposal.rationale"
                        size="large"
                        showSearch
                        :filterOption="filterOption"
                        :disabled="viewMode || rationaleNotSet" >
                        <a-select-option
                            v-for="rationale in rationales"
                            :key="rationale.id"
                            :value="rationale.id">
                            {{rationale.rationale}}
                        </a-select-option>
                    </a-select>
                    <div v-if="error" class="ant-form-explain">Обязательно для заполнения</div>
                </div>
            </div>

        </div>
        <div class="attachments">
            <a-button
                class="custom_button mt-auto"
                type="primary"
                block
                ghost
                size="large"
                :disabled="viewMode || rationaleNotSet"
                @click="openFileModal">
                Прикрепите файл с пояснительной запиской
            </a-button>
            <div v-if="proposal?.attachments.length" class="label mt-5">Прикрепленные файлы:</div>
            <template v-if="viewMode">
                <div class="attachment_files">
                    <CommentFile
                        v-for="file in proposal.attachments"
                        :key="file.id"
                        :file="file"
                        :id="proposal.id" />
                </div>
            </template>
            <template v-else>
                <FileAttach 
                    ref="fileAttach"
                    :zIndex="1100"
                    :attachmentFiles="proposal.attachments"
                    :maxMBSize="50"
                    createFounder
                    :getModalContainer="getPopupContainer"
                    :showDeviceUpload="true"
                    :class="proposal.attachments.length && 'mt-2 mb-5'"
                    class="ml-2" />
            </template>
        </div>
    </div>
</template>

<script>
import FileAttach from '@apps/vue2Files/components/FileAttach'
import CommentFile from '@apps/vue2CommentsComponent/CommentFIle.vue'

export default {
    name: 'Rationale',
    components: {
        FileAttach,
        CommentFile
    },
    props: {
        proposal: {
            type: Object,
            require: true
        },
        rationales: {
            type: Array,
            require: true
        },
        edit: {
            type: Boolean,
            default: false
        },
        viewMode: {
            type: Boolean,
            default: false
        },
        unfilled: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
        }
    },
    computed:{
        rationaleNotSet() {
            return !this.proposal.specificity?.id
        },
        error() {
            return this.unfilled && !this.proposal.rationale
        }
    },
    methods: {
        filterOption(input, option) {
            return option.componentOptions.children[0].text.toLowerCase().indexOf(input.toLowerCase()) >= 0
        },
        openFileModal() {
            this.$nextTick(() => {
                this.$refs.fileAttach.openFileModal()
            })
        },
        getPopupContainer() {
            return this.$refs['rationaleComponent']
        },
    }
}
</script>

<style lang="scss" scoped>
.rationale{
    height: auto;
    .rationale-set{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        grid-template-rows: auto;
        column-gap: 30px;
        align-items: center;
        .rationale-select{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    }
    .attachments{
        margin-top: 20px;
    }
    .no-data{
        color: rgb(209 213 219);
    }
    .row:not(:last-child) {
        margin-bottom: 20px;
    }
    .attachment_files{
        display: flex;
        flex-wrap: wrap;
    }
}
</style>