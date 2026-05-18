<template>
    <a-dropdown
        :trigger="['click']"
        placement="topLeft"
        overlayClassName="statuses-overlay">
        <a-tag :color="color">
            {{ statusName }}
        </a-tag>
        <a-menu slot="overlay" v-if="showMenu" @click="handleMenuClick">
            <a-menu-item
                v-for="option in statuses"
                class="option"
                :key="option.code" >
                <a-tag :color="option.color">
                    {{ option.name }}
                </a-tag>
            </a-menu-item>
        </a-menu>
    </a-dropdown>
</template>
<script>
import { mapState, mapMutations, mapActions } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'ObjectiveStatus',
    props: {
        objective: {
            type: Object,
            required: true
        }
    },
    computed: {
        ...mapState({
            statuses: state => state.okr.statuses,
            objectiveDetail: state => state.okr.objectiveDetail
        }),
        statusName() {
            return this.objective.status.name || 'Не указано'
        },
        color() {
            return this.objective.status.color || '#6d6e6f'
        },
        showMenu() {
            return this.objective.actions.edit
        }
    },
    methods: {
        ...mapMutations({
            UPDATE_OBJECTIVE_STATUS: 'okr/UPDATE_OBJECTIVE_STATUS',
            UPDATE_OBJECTIVE_DETAIL_STATUS: 'okr/UPDATE_OBJECTIVE_DETAIL_STATUS'
        }),
        ...mapActions({
            fetchObjectivesCount: 'okr/fetchObjectivesCount'
        }),
        async handleMenuClick(event) {
            this.$emit('setLoading', true)
            const payload = {
                status: event.key
            }
            try {
                const { data } = await this.$http.patch(`okr/objectives/${this.objective.id}/`, payload)
                if (data) {
                    this.UPDATE_OBJECTIVE_STATUS({
                        objectiveID: this.objective.id,
                        newStatus: data.status
                    })
                    if (this.objectiveDetail) {
                        this.UPDATE_OBJECTIVE_DETAIL_STATUS(data.status)
                    }
                    this.fetchObjectivesCount()
                }
            } catch(error) {
                errorHandler({error})
            } finally {
                this.$emit('setLoading', false)
            }

        }
    }
}
</script>
<style lang="scss">
.statuses-overlay {
    .ant-dropdown-menu .ant-dropdown-menu-item {
        white-space: normal;
    }
    .ant-tag {
        border-radius: 4px;
        height: 100%;
    }
}
</style>