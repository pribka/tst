<template>
    <div>
        <a-tooltip :title="$t('Delete')">
            <a-popconfirm 
                :title="$t('Are you sure?')" 
                ok-text="Да" 
                cancel-text="Нет"
                @confirm="deleteTask">
                <a-button :loading="loading.delete" class="border-0 shadow-none" type="danger" ghost flaticon icon="fi-rr-trash"></a-button>
            </a-popconfirm>
        </a-tooltip>
        <a-tooltip :title="$t('Edit')">
            <a-button  type="link" flaticon icon="fi-rr-edit" @click="editTask"></a-button>
        </a-tooltip>
        <a-tooltip :title="$t('Move up')">
            <a-button :loading="loading.move" type="link" flaticon icon="fi-rr-arrow-small-up" @click="move('up')"></a-button>
        </a-tooltip>
        <a-tooltip :title="$t('Move down')">
            <a-button :loading="loading.move" type="link" flaticon icon="fi-rr-arrow-small-down" @click="move('down')"></a-button>
        </a-tooltip>
    </div>
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
    data() {
        return {
            loading: {
                delete: false,
                move: false
            }
            
        };
    },
    methods: {
        move(direction) {
            const url = `/work_groups/task_templates/${this.record.id}/${direction}/`
            this.loading.move = true;
            this.$http.put(url)
                .then(({ data }) => {
                    this.$store.commit('projects/MOVE_TEMPLATE_TASK', { id: this.record.id, direction: direction })
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('Error'))
                })
                .finally(() => {
                    this.loading.move = false;
                })

        },
        deleteTask() {
            const url = `/work_groups/task_templates/${this.record.id}/`
            this.loading.delete = true;
            this.$http.delete(url)
                .then(() => {
                    this.$store.commit('projects/REMOVE_TEMPLATE_TABLE_ROW', { id: this.record.id })
                })
                .catch(error => {
                    console.error(error)
                    this.$message.error(this.$t('Error'))
                })
                .finally(() => {
                    this.loading.delete = false;
                })
        },
        editTask() {
            const payload = { id: this.record.id }
            this.$store.commit('projects/SET_EDIT_TEMPLATE_TABLE_ROW', payload)
        },
    },
};
</script>