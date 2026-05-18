<template>
    <div>
        <transition name="extand">
            <div :key="report.id" >
                <div class="header items-center"
                     :class="isExpand && 'border-b'">
                    <div class="contractor items-center pl-4 py-2">
                        <span :key="report.contractor.logo" class="pr-2">
                            <a-avatar 
                                :size="30"
                                :src="report.contractor.logo"
                                icon="fi-rr-users-alt" 
                                flaticon />
                        </span>
                        <span class="break-all">{{ report.contractor.name }}</span>
                    </div>
                    <template v-if="report.update_is_disabled && report.update_is_available">
                        <a-popover>
                            <template v-if="report?.update_is_disabled_message" slot="content">
                                {{report.update_is_disabled_message}}
                            </template>
                            <a-button 
                                type="link" 
                                :icon="addButtonIcon"
                                disabled />
                        </a-popover>
                    </template>
                    <template v-else>
                        <div v-if="report.update_is_available">
                            <a-popover>
                                <template slot="content">
                                    <p>{{$t('Upload')}}</p>
                                </template>
                                <a-button 
                                    type="link" 
                                    :icon="addButtonIcon"
                                    :disabled="fileChangeIsDisabled(report)"
                                    @click="uploadReport(report)" />
                            </a-popover>
                        </div>
                        <div v-else></div>
                    </template>
                    <div class="status">
                        <a-tag v-if="report.status && report.status.name" :color="report.status.color || ''">
                            {{ report.status.name }}
                        </a-tag>
                    </div>
                    <div 
                        v-if="report.view_is_available"
                        class="button"
                        :class="isExpand && 'rotate-90'"
                        @click="clickHandler">
                        <a-button
                            type="link">
                            <i class="fi fi-rr-angle-right"></i>
                        </a-button>
                    </div>
                </div>
                <div class="item_body " v-show="isExpand">
                    <a-spin :spinning="actionsLoading">
                        <component 
                            ref="reportViewWidget"
                            :is="widget"
                            :report="report"
                            :openReport="openReport"
                            :fileChangeIsDisabled="fileChangeIsDisabled"
                            :actions="actions"
                            :deleteReportFile="deleteReportFile" />
                    </a-spin>
                </div>
            </div>
        </transition>
    </div>
</template>
  
<script>
export default {
    name: 'Report',
    props: {
        report: {
            type: Object,
            required: true
        },
        openReport: {
            type: Function,
            required: true
        },
        fileChangeIsDisabled: {
            type: Function,
            required: true
        },
        uploadReport: {
            type: Function,
            required: true
        },
        deleteReportFile: {
            type: Function,
            required: true
        }
    },
    data() {
        return {
            isExpand: false,
            actionsLoading: false,
            actions: null
        }
    },
    computed: {
        addButtonIcon() {
            return this.report?.add_button_icon ? this.report.add_button_icon : 'cloud-upload'
        },
        widget() {
            return () => import(`./Widgets/${this.report.widget}.vue`)
                .then(module => {
                    return module
                })
                .catch(e => {
                    console.log('error')
                    return import(`./Widgets/NotWidget.vue`)
                })
        }
    },
    methods: {
        clickHandler() {
            this.isExpand = !this.isExpand
            if(this.isExpand) {

                this.getActions()
            } else {
                this.actions=null
            }
        },
        async getActions() {
            try {
                this.actionsLoading = true
                const { data } = await this.$http.get(`/consolidation/report/${this.report.id}/action_info/`)
                if(data?.actions) {
                    this.actions = data.actions
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.actionsLoading = false
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.header {
    background-color: rgb(243 244 246);
    display: grid;
    grid-template-columns: 1fr 40px 130px 50px;
    .status {
        justify-self: right;
    }
}
.contractor {
    display: grid;
    grid-template-columns: max-content 1fr;
}
.item_body {
    padding: 15px;
}
</style>