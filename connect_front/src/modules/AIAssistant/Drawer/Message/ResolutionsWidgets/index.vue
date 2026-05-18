<template>
    <div class="intents_form__item">
        <div class="item_label">
            {{ resolution.title || widgetKey }}:
        </div>
        <div class="item_value">
            <a-form-model-item 
                :ref="widgetKey" 
                :prop="widgetKey" 
                class="mb-0 item_control"
                :rules="resolution.required ? {
                    required: true,
                    message: $t('field_required'),
                    trigger: 'change'
                } : null">
                <component 
                    :is="EditWidget"
                    :widgetKey="widgetKey"
                    :resolution="resolution"
                    :isEdit="isEdit"
                    :injectUpdate="injectUpdate"
                    :injectChangeField="injectChangeField"
                    :injectDelete="injectDelete"
                    :useInject="useInject"
                    :intentIndex="intentIndex"
                    :formValidate="formValidate"
                    :messageIndex="messageIndex"
                    :intents="intents"
                    :message="message" />
            </a-form-model-item>
        </div>
    </div>
</template>

<script>
import props from './props.js'
export default {
    props: {...props},
    computed: {
        rulesType() {
            if(this.resolution?.type === 'ManyToManyField') {
                return 'array'
            }
            return 'string'
        },
        EditWidget() {
            return () => import(`./Widgets/${this.resolution.widget}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log(e, 'error')
                    return import('./Widgets/NotWidget.vue')
                })
        }
    }
}
</script>

<style lang="scss" scoped>
.item_control{
    &::v-deep{
        .ant-form-item-control{
            line-height: initial;
        }
        .field_empty{
            color: #888888;
        }
    }
}
.intents_form{
    &__item{
        @media (min-width: 768px) {
            display: flex;
            align-items: flex-start;
        }
        &:not(:last-child){
            margin-bottom: 10px;
        }
        .item_value{
            word-break: break-word;
            min-width: 0;
            width: 100%;
            @media (min-width: 768px) {
                flex: 1 1 0%;
            }
        }
        .item_label{
            color: #888888;
            @media (max-width: 767.98px) {
                margin-bottom: 5px;
            }
            @media (min-width: 768px) {
                min-width: 150px;
                padding-right: 20px;
                max-width: 150px;
            }
        }
    }
}
</style>