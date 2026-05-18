<template>
    <div class="summary_card mb-3 rounded-lg" :class="[cardCollapse && 'active', smallBlock && 'small_block']">
        <div class="summary_card__header select-none flex items-center justify-between truncate" :class="useCollapse && 'cursor-pointer'" @click="cardCollapse = !cardCollapse">
            <h4 class="summary_card__label truncate font-semibold mb-0">
                <i class="fi fi-rr-pen-field mr-2" />
                {{ $t('workplan.summary_short') }}
            </h4>
            <i v-if="useCollapse" class="fi fi-rr-angle-small-down card_arrow opacity-80 ml-2" />
        </div>
        <div v-if="cardCollapse" v-html="summaryHtml" @click.stop class="mt-3 mb-2 summary_text" />
        <a-button v-if="useMore" type="link" class="px-0 flex items-center" @click="changeTap('transcribe')">
            {{ $t('workplan.details') }}
            <i class="fi fi-rr-arrow-small-right ml-2" />
        </a-button>
    </div>
</template>

<script>
export default {
    props: {
        summary: {
            type: String,
            default: ""
        },
        useCollapse: {
            type: Boolean,
            default: false
        },
        useMore: {
            type: Boolean,
            default: false
        },
        changeTap: {
            type: Function,
            default: () => {}
        },
        smallBlock: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            collapse: false
        }
    },
    computed: {
        cardCollapse: {
            get() {
                if(this.useCollapse)
                    return this.collapse
                return true
            },
            set(value) {
                this.collapse = value
            }
        },
        summaryHtml() {
            if (!this.summary) return ''
            return this.summary
                .replace(/(^|\n)\s*(\d+\.)\s*\.?\s*_+/g, '$1$2 ')
                .replace(/_+(\s*\n|$)/g, '$1')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>')
                .trim()
                .replace(/^/, '<p>')
                .replace(/$/, '</p>')
        },
    }
}
</script>

<style lang="scss" scoped>
.summary_text{
    &::v-deep{
        p{
            &:not(:last-child){
                margin-bottom: 10px;
            }
        }
    }
}
.summary_card{
    background: linear-gradient(135deg,  rgba(249,239,255,1) 46%,rgba(240,216,255,1) 100%);
    padding: 10px 20px;
    border: 1px solid #f1dcff;
    .summary_card__label{
        display: flex;
        align-items: center;
        font-size: 18px;
    }
    .card_arrow{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &.active{
        .card_arrow{
            transform: rotate(180deg);
        }
    }
    &.small_block{
        padding: 10px 15px;
        .summary_card__label{
            font-size: 14px;
        }
    }
}
</style>
