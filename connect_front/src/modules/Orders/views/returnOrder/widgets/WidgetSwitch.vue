<template>
    <div class="order_block"
         :class="!isMobile || 'order_block_mobile'">
        <div class="label">
            <i 
                class="fi icon" 
                :class="item.icon"></i>
            {{ item.title }}
        </div>
        <component 
            :is="widget"
            :form="form"
            :reload="reload"
            :changeContract="changeContract"
            :item="item" />
    </div>
</template>

<script>
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        form: {
            type: Object,
            required: true
        },
        changeContract: {
            type: Function,
            default: () => {}
        },
        reload: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        widget() {
            return () => import(`./${this.item.widget}`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./NotWidget.vue`)
                })
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    }
}
</script>

<style lang="scss" scoped>
.order_block{
    border: 1px solid var(--border2);
    position: relative;
    padding: 30px;
    border-radius: var(--borderRadius);
    .label{
        font-weight: 600;
        font-size: 15px;
        background: #fff;
        padding: 0 10px;
        position: absolute;
        top: 0;
        left: 20px;
        z-index: 1;
        line-height: 18px;
        margin-top: -9px;
        color: #000;
        display: flex;
        align-items: center;
        .icon{
            margin-right: 10px;
            color: var(--blue);
        }
    }
    &:not(:last-child){
        margin-bottom: 30px;
    }
}
.order_block_mobile {
    padding: 0px;
    padding-top: 15px;

    border: none;
    .label{
        left: 0;

        padding: 0;

        background-color: transparent;
    }
}
</style>