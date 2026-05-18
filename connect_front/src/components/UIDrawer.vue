<template>
    <a-drawer
        title="UI components"
        :visible="visible"
        class="invite_drawer"
        @close="visible = false"
        destroyOnClose
        :width="drawerWidth"
        placement="right">
        <div class="ui_list">
            <div class="ui_list__item">
                <label>Buttons</label>
                <div class="flex items-center mb-2">
                    <a-button type="success">
                        Success
                    </a-button>
                    <div class="info_text">
                        type="success"
                    </div>
                </div>
                <div class="flex items-center mb-2">
                    <a-button type="green">
                        Green
                    </a-button>
                    <div class="info_text">
                        type="green"
                    </div>
                </div>
                <div class="flex items-center mb-2">
                    <a-button type="success" ghost>
                        Success ghost
                    </a-button>
                    <div class="info_text">
                        type="success" ghost
                    </div>
                </div>
                <div class="flex items-center mb-2">
                    <a-button type="ui">
                        UI button
                    </a-button>
                    <div class="info_text">
                        type="ui"
                    </div>
                </div>
                <div class="flex items-center mb-2">
                    <a-button type="ui" ghost>
                        UI ghost
                    </a-button>
                    <div class="info_text">
                        type="ui" ghost
                    </div>
                </div>
            </div>
            <div class="ui_list__item">
                <label>Avatars</label>
                <div class="flex items-center mb-2">
                    <a-avatar 
                        :size="60"
                        flaticon
                        icon="fi-rr-users-alt" />
                    <div class="info_text">
                        icon="fi-rr-users-alt" flaticon
                    </div>
                </div>
            </div>
            <div class="ui_list__item">
                <label>Checkbox</label>
                <div class="flex items-center mb-2">
                    <a-checkbox checked checkboxColor="#28af14">
                        Зеленый
                    </a-checkbox>
                    <a-checkbox checked checkboxColor="rgb(244, 60, 54)">
                        Красный
                    </a-checkbox>
                    <div class="info_text">
                        checkboxColor="#28af14"
                    </div>
                </div>
            </div>
        </div>
    </a-drawer>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: "UIComponentsDrawer",
    computed: {
        windowWidth() {
            return this.$store.state.windowWidth
        },
        drawerWidth() {
            if(this.windowWidth > 1200)
                return 1200
            else {
                return '100%'
            }
        }
    },
    data() {
        return {
            visible: false
        }
    },
    created() {
        eventBus.$on('open_ui_drawer', () => {
            this.visible = true
        })
    },
    beforeDestroy() {
        eventBus.$off('open_ui_drawer')
    }
}
</script>

<style lang="scss" scoped>
.ui_list{
    &__item{
        padding: 20px 0;
        &:not(:last-child){
            border-bottom: 1px solid var(--border2);
        }
        & > label{
            display: block;
            font-weight: 600;
            margin-bottom: 20px;
            font-size: 20px;
        }
    }
    .info_text{
        margin-left: 20px;
    }
}
</style>