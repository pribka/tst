<template>
    <div class="kanban">
        <div class="quarter">
            <div class="label">{{ `1 ${$t('okr.quarter')}`}}</div>
            <draggable
                v-model="quarter_1"
                v-bind="dragOptions"
                :disabled="draggableDisabled"
                group="quarters"
                class="list"
                @change="e => onDragChange(1, e)">
                <ObjectiveCard
                    v-for="objective in quarter_1"
                    :ref="`oCard_${objective.id}`"
                    :key="objective.id"
                    :objective="objective" />
            </draggable>
            <a-empty v-if="!quarter_1.length" :description="false" />
        </div>
        <div class="quarter">
            <div class="label">{{ `2 ${$t('okr.quarter')}`}}</div>
            <draggable
                v-model="quarter_2"
                v-bind="dragOptions"
                :disabled="draggableDisabled"
                group="quarters"
                class="list"
                @change="e => onDragChange(2, e)">
                <ObjectiveCard
                    v-for="objective in quarter_2"
                    :ref="`oCard_${objective.id}`"
                    :key="objective.id"
                    :objective="objective" />
            </draggable>
            <a-empty v-if="!quarter_2.length" :description="false" />
        </div>
        <div class="quarter">
            <div class="label">{{ `3 ${$t('okr.quarter')}`}}</div>
            <draggable
                v-model="quarter_3"
                v-bind="dragOptions"
                :disabled="draggableDisabled"
                group="quarters"
                class="list"
                @change="e => onDragChange(3, e)">
                <ObjectiveCard
                    v-for="objective in quarter_3"
                    :ref="`oCard_${objective.id}`"
                    :key="objective.id"
                    :objective="objective" />
            </draggable>
            <a-empty v-if="!quarter_3.length" :description="false" />
        </div>
        <div class="quarter">
            <div class="label">{{ `4 ${$t('okr.quarter')}`}}</div>
            <draggable
                v-model="quarter_4"
                v-bind="dragOptions"
                :disabled="draggableDisabled"
                group="quarters"
                class="list"
                @change="e => onDragChange(4, e)">
                <ObjectiveCard
                    v-for="objective in quarter_4"
                    :ref="`oCard_${objective.id}`"
                    :key="objective.id"
                    :objective="objective" />
            </draggable>
            <a-empty v-if="!quarter_4.length" :description="false" />
        </div>
    </div>
</template>
<script>
import draggable from "vuedraggable"
import { mapMutations } from 'vuex'
import { errorHandler } from '@/utils/index.js'
export default {
    name: 'Kanban',
    components: {
        ObjectiveCard: () => import('./components/ObjectiveCard.vue'),
        draggable
    },
    data() {
        return {
            dragOptions: {
                animation: 200,
                ghostClass: "ghost"
            }
        }
    },
    computed: {
        quarter_1: {
            get() {
                return this.$store.state.okr.quarter_1
            },
            set(value) {
                this.setQuarter({ quarter: 1, value: value})
            }
        },
        quarter_2: {
            get() {
                return this.$store.state.okr.quarter_2
            },
            set(value) {
                this.setQuarter({ quarter: 2, value: value})
            }
        },
        quarter_3: {
            get() {
                return this.$store.state.okr.quarter_3
            },
            set(value) {
                this.setQuarter({ quarter: 3, value: value})
            }
        },
        quarter_4: {
            get() {
                return this.$store.state.okr.quarter_4
            },
            set(value) {
                this.setQuarter({ quarter: 4, value: value})
            }
        },
        draggableDisabled() {
            return this.$store.state.okr?.actions?.create_objectives ? !this.$store.state.okr?.actions?.create_objectives.availability : true
        }
    },
    methods: {
        ...mapMutations({
            setQuarter: 'okr/SET_QUARTER',
            updateObjectiveOnList: 'okr/UPDATE_OBJECTIVE_ON_LIST'
        }),
        async onDragChange(quarter, e) {
            if(e.added) {
                let objective = e.added.element
                this.$refs[`oCard_${objective.id}`][0].setLoading(true)
                try {
                    const { data } = await this.$http.post(`okr/objectives/${objective.id}/set_quarter/`, { quarter: quarter })
                    if (data) {
                        this.updateObjectiveOnList({
                            objectiveID: objective.id,
                            data: data
                        })
                        this.$message.success(this.$t('okr.okrPeriodChanged'))
                    }
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.$refs[`oCard_${objective.id}`][0].setLoading(false)
                }
                
            }

        },
        
    }
}
</script>
<style lang="scss" scoped>
.kanban {
    height: 100%;
    width: 100%;
    flex: 1;
    overflow: auto;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    .quarter {
        background-color: #FFFFFF;
        min-width: 380px;
        border-radius: 12px;
        padding: 20px 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        .label {
            font-weight: 400;
            font-size: 14px;
            color: #2D2D2D;
        }
        .list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
    }
}
</style>