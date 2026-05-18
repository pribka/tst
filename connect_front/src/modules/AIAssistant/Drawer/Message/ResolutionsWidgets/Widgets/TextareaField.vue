<template>
    <div class="textarea_editor">
        <component
            v-if="isEdit"
            v-model="value"
            :is="ckEditor"
            :taskId="formKey || null"
            :placeholder="$t('ai_assistant.description_placeholder')"
            @change="ckeditorChange" />
        <div v-else>
            <TextViewer 
                v-if="value"
                class="body_text" 
                :body="value" />
            <div v-else class="field_empty">{{ $t('ai_assistant.description_not_specified') }}</div>
        </div>
    </div>
</template>

<script>
import props from '../props.js'
import mixins from './mixins.js'
export default {
    props: {...props},
    mixins: [mixins],
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
    },
    data() {
        return {
            value: "",
            formKey: String(Date.now())
        }
    },
    computed: {
        ckEditor() {
            return () => import("@apps/CKEditor")
        }
    },
    created() {
        if(this.intents.resolutions?.[this.widgetKey]?.value) {
            this.value = this.intents.resolutions[this.widgetKey].value
        }
    }
}
</script>

<style lang="scss" scoped>
.textarea_editor{
    &::v-deep{
        .ck-editor__top{
            position: sticky !important;
            top: 0px !important;
            background: white !important;
            z-index: 100;
        }
        .ck{
            &.ck-toolbar__items{
                margin-right: 0px!important;
            }
            &.ck-toolbar__separator{
                opacity: 0;
                margin-right: 0px!important;
            }
            &.ck-toolbar{
                border: 0px;
                padding-left: 0px!important;
                padding-right: 0px!important;
                margin-left: -7px;
            }
            &.ck-content{
                border: 0px!important;
                box-shadow: none!important;
                padding-left: 0px!important;
                padding-right: 0px!important;
            }
        }
    }
}
</style>
