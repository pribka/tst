<template>
    <div 
        class="flex items-center cursor-pointer row_name"
        :title="stringView"
        @click="clickHandler(clickHandlerParam)">
        <template v-if="stringView">
            <div class="pr-2">
                <a-avatar 
                    :size="26" 
                    icon="fi-rr-users-alt"
                    flaticon
                    :key="workgroupLogoPath"
                    :src="workgroupLogoPath" />
            </div>
            <div class="line-clamp-2 break-words" style="line-height: 18px;">
                {{ stringView }}
            </div>
        </template>
    </div>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        openHandler: {
            type: Function,
            default: () => {}
        },
        model: {
            type: String,
            default: ''
        },
        tableType: {
            type: String,
            default: ''
        },
        column: {
            type: Object,
            default: () => {}
        },
    },
    computed: {
        stringView() {
            if(this.column.key === 'project') {
                return this.record.project?.name || null
            }
            if(this.column.key === 'workgroup') {
                return this.record.workgroup?.name || null
            }
            if(['organization', 'contractor'].includes(this.column.key)) {
                return this.record[this.column.key]?.name || null
            }
            return this.record.name
        },
        isWorkgroupAndProject() {
            return this.model === 'workgroups.WorkgroupModel'
        },
        isModeration() {
            return this.tableType === 'moderation'
        },
        isName() {
            return this.column.key === 'name'
        },
        clickHandler() {
            if(this.column.key === 'project' && this.record?.project?.id) {
                const query = {...this.$route.query}
                query.viewProject = this.record.project.id
                this.$router.replace({query})
            }
            if(this.column.key === 'workgroup' && this.record?.workgroup?.id) {
                const query = {...this.$route.query}
                query.viewGroup = this.record.project.id
                this.$router.replace({query})
            }
            if((this.isWorkgroupAndProject && this.isName) ||
                this.isModeration)
                return this.openHandler        
            return () => {}
        },
        clickHandlerParam() {
            if(this.isWorkgroupAndProject && this.isName)
                return this.record.id
            if (this.isModeration)
                return this.record
            return null
        },
        workgroupLogoPath() {
            if(['organization', 'contractor'].includes(this.column.key)) {
                return this.record[this.column.key]?.logo || ''
            }
            if(this.column.key === 'project')
                return this.record.project?.workgroup_logo?.path || ''
            if(this.column.key === 'workgroup')
                return this.record.workgroup?.workgroup_logo?.path || ''
            return this.record?.workgroup_logo?.path || ''

        }

    }
}
</script>

<style lang="scss" scoped>
.row_name{
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    &:hover{
        color: var(--blue);
    }
}
.line-clamp-2 {
    overflow: hidden;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
}
</style>