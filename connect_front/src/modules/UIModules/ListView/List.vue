<template>
    <div 
        class="list_view" 
        :class="[labelDark && 'd_label', inline && 'l_inline', size === 'small' && 'list_view_sm']">
        <slot />
    </div>
</template>

<script>
export default {
    props: {
        inline: {
            type: Boolean,
            default: false
        },
        labelDark: {
            type: Boolean,
            default: false
        },
        size: {
            type: String,
            default: ""
        }
    }
}
</script>

<style lang="scss" scoped>
.list_view{
    &::v-deep{
        .list_view__item{
            &:not(:last-child){
                margin-bottom: 15px;
            }
            .item_label{
                margin-bottom: 5px;
            }
            .item_value{
                width: 100%;
                .ant-form-item{
                    margin-bottom: 0px;
                    .ant-form-item-control{
                        line-height: initial;
                    }
                }
            }
        }
    }
    &.d_label{
        &::v-deep{
            .item_label{
                color: var(--text);
            }
        }
    }
    &.l_inline{
        &::v-deep{
            .item_value{
                flex: 1 1 0%;
                min-width: 0;
                word-break: break-word;
            }
            .list_view__item{
                display: flex;
                align-items: center;
                .item_label{
                    min-width: 180px;
                    margin-bottom: 0px;
                    padding-right: 10px;
                    max-width: 180px;
                    word-break: break-word;
                    width: 100%;
                    @media (min-width: 1424px) {
                        min-width: 200px;
                        max-width: 200px;
                    }
                }
            }
        }
    }
    &.list_view_sm{
        &::v-deep{
            .list_view__item{
                &:not(:last-child){
                    margin-bottom: 6px;
                }
            }
        }
    }
}
</style>