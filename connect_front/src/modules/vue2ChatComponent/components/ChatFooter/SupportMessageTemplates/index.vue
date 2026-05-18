<template>
    <div class="wrapper">
        <a-spin v-if="spinning">
        </a-spin>
        <template v-else>
            <keep-alive v-if="view === 'list'">
                <ListView
                    :deleteTemplate="deleteTemplate"
                    @openAddEdit="openAddEdit" />
            </keep-alive>
            <AddEditView
                v-if="view === 'addEdit'"
                :edit="edit"
                :editableTemplateID="editableTemplateID"
                :deleteTemplate="deleteTemplate"
                @closeAddEdit="closeAddEdit" />
        </template>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    name: 'SupportMessageTemplates',
    components: {
        ListView: () => import('./ListView.vue'),
        AddEditView: () => import('./AddEditView.vue')
    },
    data() {
        return {
            edit: false,
            view: 'list',
            editableTemplateID: '',
            spinning: false
        }
    },
    methods: {
        closeAddEdit() {
            this.view = 'list'
            this.$emit('changePopoverHeight', 318)
        },
        openAddEdit(edit=false, id='') {
            this.view = 'addEdit'
            this.edit = edit
            if(edit) {
                this.$emit('changePopoverHeight', 450)
                this.editableTemplateID = id
            } else {
                this.$emit('changePopoverHeight', 416)
            }
        },
        deleteTemplate(id) {
            if(this.spinning)
                return
            this.spinning = true
            const url = `chat/message_templates/${id}/`
            this.$http.delete(url)
                .then(response => {
                    if(response.status === 204)
                        eventBus.$emit('reloadSMTList')
                })
                .catch(e => {
                    console.log(e)
                })
                .finally(() => {
                    this.spinning = false
                })
        }
    }
}
</script>

<style lang="scss" scoped>
.wrapper{
    height: 100%;
    max-width: 552px;
    @media (min-width: 768px) {
        margin: 20px 25px 10px 25px;
    }
}
</style>