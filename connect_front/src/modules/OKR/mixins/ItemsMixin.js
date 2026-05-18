import eventBus from '@/utils/eventBus'
import DeleteObjective from '@apps/OKR/mixins/DeleteObjective'
import { mapMutations, mapActions } from 'vuex'
import ObjectiveActionMenu from '@apps/OKR/components/ObjectiveActionMenu.vue'
import ObjectiveStatus from '@apps/OKR/components/ObjectiveStatus.vue'

export default {
    components: {
        ObjectiveActionMenu,
        ObjectiveStatus
    },
    mixins: [
        DeleteObjective,
        ObjectiveStatus
    ],
    computed: {
        period() {
            return `${this.$moment(this.objective.date_start).format(this.dateFormat)} - ${this.$moment(this.objective.date_end).format(this.dateFormat)}`
        },
        badgeColor() {
            return this.objective?.value_efforts?.hex_color ? this.objective.value_efforts.hex_color : undefined
        },
        badgeName() {
            return this.objective?.value_efforts?.name ? this.objective.value_efforts.name : ''
        },
        keyResultsList() {
            return this.objective?.key_results ? this.objective.key_results : []
        }
    },
    methods: {
        ...mapMutations({
            REMOVE_OBJECTIVE: 'okr/REMOVE_OBJECTIVE',
            SET_LOADING: 'okr/SET_LOADING',
        }),
        ...mapActions({
            fetchKeyResults: 'okr/fetchKeyResults'
        }),
        setLoading(val) {
            this.loading = val
        },
        editObjective() {
            eventBus.$emit('edit_objective', this.objective.id)
        },
        showRetro() {
            eventBus.$emit('open_objective_details', this.objective.id, 'retrospective')
        },
        openDetail() {
            eventBus.$emit('open_objective_details', this.objective.id)
        },
        deleteHandler() {
            this.deleteObjective(this.objective.id)
                .then(async () => {
                    this.SET_LOADING(true)
                    this.REMOVE_OBJECTIVE(this.objective)
                })
                .finally(() => {
                    this.SET_LOADING(false)
                })
        }
    }
}