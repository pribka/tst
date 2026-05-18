<template>
    <div>
        <a-form-model-item
            v-if="formInfo.files"
            :rules="formInfo.files.rules"
            class="mb-0"
            style="margin-bottom: 0px;"
            prop="attachments">
            <a-button
                type="link"
                size="small"
                class="p-0"
                @click="openFileModal">
                + {{ $t("Attach files") }}
            </a-button>
            <div v-show="value.attachments.length">
                <p>{{ $t("Attached files") }}</p>
                <FileAttach
                    ref="fileAttach"
                    :zIndex="1100"
                    class="task_files_list"
                    :attachmentFiles="value.attachments"
                    :maxMBSize="50"
                    createFounder
                    listType="picture"
                    :showDeviceUpload="true"/>
            </div>
        </a-form-model-item>
    </div>

</template>

<script>
export default {
    components: { 
        FileAttach: () => import("@apps/vue2Files/components/FileAttach")
    },
    props: {
        value: { // form
            type: Object,
            required: true
        },
        formInfo: {
            type: Object,
            required: true
        },
    },
    data() {
        return {
        }
    },
    methods: {
        openFileModal() {
            this.$nextTick(() => {
                this.$refs.fileAttach.openFileModal();
            });
        },
    }
}
</script>

<style lang="scss" scoped>
.task_files_list{
    &::v-deep{
        .file_p_card{
            background: #fff;
        }
    }
}
</style>