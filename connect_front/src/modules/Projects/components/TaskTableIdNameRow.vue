<template>
    <span> 
        {{ record.name}}
        <template v-if="isMilestone">
            <a-tooltip :title="$t('Milestone')">
                <i class="ml-2 fi fi-rr-flag-alt"></i>
            </a-tooltip>
        </template>
    </span>
</template>

<script>
export default {
    props: {
        record: {
            type: Object,
            required: true
        },
        template: {
            type: String,
            default: ''
        }
    },
    components: {},
    computed: {
        isMilestone() {
            return this.record.task_type === 'milestone'
        },
    },
    data() {
        return {
            edit: false,
            loading: false,
            form: {
                name: "",
                description: "",
                duration: 0,
                taskType: ''
            },
            rules: {
                name: [
                    { required: true, message: this.$t('field_required'), trigger: "blur" },
                ],
                duration: [
                    { required: true, message: this.$t('field_required'), trigger: "blur" },
                ],
            }
        };
    },
    methods: {
        deleteTask() {
            const url = `/work_groups/task_templates/${this.record.id}/`
            this.$http.delete(url)
                .then(() => {
                    this.$store.commit('projects/REMOVE_TEMPLATE_TABLE_ROW', { id: this.record.id })
                })
                .catch(error => {
                    this.$message.error(this.$t('error'))
                    console.error(error)
                })
        },
        createTask() {
            const url = '/work_groups/task_templates/'
            const payload = {
                template: this.template,
                parent: this.recotd.parent || null,
                name: this.form.name,
                description: this.form.description,
                duration: `${this.form.duration} 00:00:00`,
                task_type: this.form.taskType
            }
            this.loading = true
            this.$http.post(url, payload)
                .then(() => {
                    this.clearForm()
                })
                .catch(() => {
                    this.$message.error(this.$t('error'))
                    console.error(error)
                })
                .finally(() => {
                    this.loading = false
                })
        },
        editTask() {
            const url = `work_groups/task_templates/${this.record.id}/`
            const payload = {
                name: this.form.name,
                description: this.form.description,
                duration: `${this.form.duration} 00:00:00`,
            }
            this.loading = true
            this.$http.post(url, payload)
                .then(() => {
                    this.clearForm()
                })
                .catch(() => {
                    this.$message.error(this.$t('error'))
                    console.error(error)
                })
                .finally(() => {
                    this.loading = false
                })
        },
        enableEditMode(taskType) {
            const payload = { id: this.record.id }
            this.$store.commit('projects/SET_EDIT_TEMPLATE_TABLE_ROW', payload)
        },
        disableEditMode() {
            this.edit = false
            this.taskType = ''
            this.clearForm()
        },
        clearForm() {
            this.form = {
                name: '',
                description: '',
                duration: 0,
                taskType: ''
            }
        }
    },
};
</script>

<style lang="scss" scoped>
</style>