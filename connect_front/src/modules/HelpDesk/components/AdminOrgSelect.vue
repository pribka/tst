<template>
    <a-popover
        :placement="placement"
        trigger="click"
        v-model="visible"
        transitionName=""
        :destroyTooltipOnHide="true"
        overlayClassName="admin_org_popover"
        :getPopupContainer="getPopupContainer"
        @visibleChange="visibleChange">
        <a-spin size="small" :spinning="injectLoading">
            <div v-if="inputType === 'input'" class="input_select truncate" :class="[value && 'selected_active', block && 'input_block']">
                <div class="mr-2 truncate">
                    <span class="s_plc" style="color: #888;">{{ placeholderText }}</span>
                    <transition name="slide-fade">
                        <div v-if="value" class="selected_name truncate">{{ value.name }}</div>
                    </transition>
                </div>
                <i class="fi fi-rr-angle-small-down arrow_icon"></i>
            </div>
            <div v-if="inputType === 'ghost'" class="input_select_ghost truncate" :class="[value && 'selected_active', block && 'input_block']">
                <div class="flex items-center truncate">
                    <div v-if="useIcon" class="mr-5">
                        <i class="fi" :class="icon" />
                    </div>
                    <div class="mr-2 truncate">
                        <div v-if="value" class="selected_name truncate">{{ value.name }}</div>
                        <span v-else class="s_plc" style="color: #888;">{{ placeholderText }}</span>
                    </div>
                </div>
                <i class="fi fi-rr-angle-small-down arrow_icon"></i>
            </div>
        </a-spin>
        <template #content>
            <div class="popover_list">
                <div 
                    v-for="(work, index) in list" 
                    :key="index"
                    :title="work.name"
                    :class="checkSelected(work)"
                    class="cursor-pointer project_item p-2 flex items-center truncate" 
                    @click="selectWork(work)">
                    {{ work.name }}
                </div>
                <div v-if="loading" class="flex justify-center">
                    <a-spin size="small" />
                </div>
            </div>

            <div class="pt-1">
                <a-button type="ui_ghost" block size="small" @click="visible = false">
                    {{ $t('Close') }}
                </a-button>
            </div>
        </template>
    </a-popover>
</template>

<script>
export default {
    props: {
        value: { type: [Object, Array, String] },
        selectOrg: { type: Function, default: () => {} },
        apiUrl: {
            type: String,
            default: '/help_desk/my_org_admins/'
        },
        injectLoading: {
            type: Boolean,
            default: false
        },
        inputType: {
            type: String,
            default: 'input'
        },
        placeholder: {
            type: String,
            default: ''
        },
        useIcon: {
            type: Boolean,
            default: false
        },
        icon: {
            type: String,
            default: 'fi-rr-portrait'
        },
        placement: {
            type: String,
            default: 'topLeft'
        },
        firstSelect: {
            type: Boolean,
            default: false
        },
        block: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            visible: false,
            loading: false,
            list: []
        }
    },
    computed: {
        placeholderText() {
            return this.placeholder || this.$t('helpdesk.service_organization')
        }
    },
    created() {
        if(this.firstSelect)
            this.getOrgList()
    },
    methods: {
        selectWork(work) {
            if(this.value?.id === work.id)
                return;
            this.$emit('input', work)
            this.$emit('change', work)
            this.selectOrg(work)
            this.visible = false
        },
        checkSelected(work) {
            if(this.value?.id === work.id) return 'active'
            else return ''
        },
        getPopupContainer(trigger) {
            return trigger.parentNode
        },
        visibleChange(vis) {
            if(vis) {
                this.getOrgList()
            }
        },
        async getOrgList() {
            if(!this.list.length) {
                try {
                    this.loading = true
                    const { data } = await this.$http.get('/help_desk/my_org_admins/')
                    if(data?.length) {
                        this.list = data
                        if(this.firstSelect && data.length === 1) {
                            this.selectWork(this.list[0])
                        }
                    }
                } catch(error) {
                    console.log(error)
                } finally {
                    this.loading = false
                }
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.slide-fade-enter-active {
  transition: all .3s ease;
}
.slide-fade-leave-active {
  transition: all .3s cubic-bezier(1.0, 0.5, 0.8, 1.0);
}
.slide-fade-enter, .slide-fade-leave-to{
  transform: translateY(10px);
  opacity: 0;
}
.input_select_ghost{
    background: transparent;
    min-width: 100%;
    max-width: 100%;
    padding: 6px 40px 2px 0px;
    cursor: pointer;
    display: flex;
    align-items: center;
    overflow: hidden;
    user-select: none;
    justify-content: space-between;
    position: relative;
    height: 32px;
    max-height: 32px;
    .arrow_icon{
        top: 0px;
        right: 8px;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        position: absolute;
        z-index: 5;
        color: #2D2D2D;
        font-size: 15px;
    }
}
.input_select{
    background: #fff;
    border-radius: var(--borderRadius);
    padding: 6px 40px 2px 15px;
    cursor: pointer;
    height: 38px;
    max-height: 38px;
    display: flex;
    align-items: flex-end;
    overflow: hidden;
    user-select: none;
    font-size: 14px;
    position: relative;
    min-width: 300px;
    max-width: 300px;
    justify-content: space-between;
    &.input_block{
        max-width: 100%;
        min-width: 100%;
    }
    .arrow_icon{
        top: 0px;
        right: 15px;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        position: absolute;
        z-index: 5;
    }
    .s_plc{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        position: absolute;
        top: 8px;
        left: 0;
        left: 15px;
        padding-right: 15px;
        width: 100%;
    }
    &.selected_active{
        .s_plc{
            font-size: 12px;
            margin-top: 2px;
            top: 0px;
        }
    }
}
.popover_list{
    max-height: 160px;
    overflow-y: auto;
    max-width: 250px;
    min-width: 250px
}
.project_item{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    border-radius: 8px;
    margin-bottom: 3px;
    user-select: none;
    &:hover,
    &.active{
        background: #f7f9fc
    }
}
.sel_p_btn{
    max-width: 300px
}
</style>

<style lang="scss">
.admin_org_popover{
    .ant-popover-arrow{
        display: none
    }
    &.ant-popover-placement-bottom, 
    &.ant-popover-placement-bottomLeft, 
    &.ant-popover-placement-bottomRight{
        padding-top: 0px
    }
    &.ant-popover-placement-top, 
    &.ant-popover-placement-topLeft, 
    &.ant-popover-placement-topRight{
        padding-bottom: 0px;
    }
}
</style>