<template>
    <a-drawer
        class="drawer_style"
        :class="classList"
        :title="title"
        placement="right"
        :zIndex="zIndex"
        :width="drawerWidth"
        :destroyOnClose="destroyOnClose"
        :closable="true"
        :visible="visible"
        :afterVisibleChange="afterVisibleChange"
        @close="close">
        <div class="drawer_body">
            <slot name="body"></slot>
        </div>

        <div class="drawer_footer">
            <slot name="footer"></slot>
        </div>
    </a-drawer>
</template>

<script>
export default {
    props: {
        value: [Boolean],
        width: {
            type: [Number, String],
            default: 800
        },
        zIndex: {
            type: Number,
            default: 1000
        },
        title: {
            type: [String],
            default: ""
        },
        maskClosable: {
            type: [Boolean],
            default: true
        },
        destroyOnClose: {
            type: [Boolean],
            default: false
        },
        classList: {
            type: String,
            default: ''
        },
        afterVisibleChange: {
            type: Function,
            default: () => {}
        }
    },
    data(){
        return{
            windowWidth: window.innerWidth
        }
    },

    computed: {

        drawerWidth() {
            if(this.windowWidth > 800)
                return this.width
            else if(this.windowWidth < 800 && this.windowWidth > 500)
                return this.windowWidth - 30
            else
                return this.windowWidth
        },
        visible: {
            get() {
                return this.value;
            },
            set(value) {
                this.$emit("input", value);
            },
        },
    },
    methods: {
        close(){
            this.visible=false
            this.$emit("close")
        }
    },
    created(){

    }
}
</script>

<style lang="scss">
.drawer_style .ant-drawer-body {
    overflow-y: auto;
}
</style>