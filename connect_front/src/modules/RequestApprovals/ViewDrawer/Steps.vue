<template>
    <transition name="slide-fade">
        <div v-if="steps.length" class="steps_block mb-4">
            <div class="steps_track">
                <div
                    v-for="(item, index) in normalizedSteps"
                    :key="item.key"
                    class="step_item">
                    <div
                        v-if="item?.status?.code !== 'awaits'"
                        class="step_circle"
                        :class="circleClass(index)"
                        v-tippy
                        :content="item?.status?.name || ''">
                        <i
                            v-if="item?.status?.code === 'rejected' && rejectedIndex !== -1 && index === rejectedIndex"
                            class="fi fi-rr-cross" />
                        <i
                            v-else-if="item?.status?.code === 'on_rework' && rejectedIndex !== -1 && index === rejectedIndex"
                            class="fi fi-rr-rotate-right" />
                        <i v-else-if="isApproved(item, index)" class="fi fi-rr-check" />
                        <span v-else class="step_num">
                            {{ item.number || index + 1 }}
                        </span>
                    </div>
                    <div
                        v-else
                        class="step_circle"
                        :class="circleClass(index)">
                        <i
                            v-if="item?.status?.code === 'rejected' && rejectedIndex !== -1 && index === rejectedIndex"
                            class="fi fi-rr-cross" />
                        <i
                            v-else-if="item?.status?.code === 'on_rework' && rejectedIndex !== -1 && index === rejectedIndex"
                            class="fi fi-rr-rotate-right" />
                        <i v-else-if="isApproved(item, index)" class="fi fi-rr-check" />
                        <span v-else class="step_num">
                            {{ item.number || index + 1 }}
                        </span>
                    </div>

                    <div class="step_label" :class="{ active: index === active }">
                        {{ item.title }}
                    </div>

                    <div
                        v-if="index !== normalizedSteps.length - 1"
                        class="step_line"
                        :class="{ done: isLineDone(index) }" />
                </div>
            </div>
        </div>
    </transition>
</template>

<script>
import { errorHandler } from '@/utils/index.js'

export default {
    name: 'ApprovalStepsVisual',
    props: {
        approvals: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            steps: [],
            active: 0
        }
    },
    computed: {
        rejectedIndex() {
            if (!this.steps?.length) return -1
            return this.steps.findIndex(x => ['rejected', 'on_rework'].includes(x?.status?.code))
        },
        normalizedSteps() {
            if (!this.steps?.length) return []
            return this.steps.map((s, i) => ({
                ...s,
                key: s?.id || s?.number || i
            }))
        },
        lastApprovedIndex() {
            if (!this.normalizedSteps?.length) return -1
            return this.normalizedSteps.reduce(
                (acc, step, idx) => (step?.status?.code === 'approved' ? idx : acc),
                -1
            )
        }
    },
    methods: {
        isApproved(step, index) {
            if (this.rejectedIndex !== -1) {
                if (index > this.rejectedIndex) return false
                return step?.status?.code === 'approved'
            }
            if (this.lastApprovedIndex !== -1 && index < this.lastApprovedIndex) return true
            return step?.status?.code === 'approved'
        },
        isRejected(step) {
            return ['rejected', 'on_rework'].includes(step?.status?.code)
        },
        isLineDone(index) {
            const step = this.normalizedSteps?.[index]
            if (!step) return false
            if (this.rejectedIndex !== -1 && index >= this.rejectedIndex) return false
            return this.isApproved(step, index)
        },
        async getSteps() {
            try {
                const { data } = await this.$http.get(
                    `/processes/workflow_requests/${this.approvals.id}/stage_info/`
                )

                if (!Array.isArray(data) || !data.length) {
                    this.steps = []
                    this.active = 0
                    return
                }

                this.steps = data

                const rejectedIndex = data.findIndex(x => ['rejected', 'on_rework'].includes(x?.status?.code))
                if (rejectedIndex !== -1) {
                    this.active = rejectedIndex
                    return
                }

                const lastApprovedIndex = data.reduce(
                    (acc, step, idx) => (step?.status?.code === 'approved' ? idx : acc),
                    -1
                )
                if (lastApprovedIndex !== -1) {
                    const firstNotApprovedAfterApproved = data.findIndex(
                        (step, idx) => idx > lastApprovedIndex && step?.status?.code !== 'approved'
                    )
                    this.active = firstNotApprovedAfterApproved === -1 ? data.length : firstNotApprovedAfterApproved
                    return
                }

                const firstNotApprovedIndex = data.findIndex(
                    x => x?.status?.code !== 'approved'
                )

                if (firstNotApprovedIndex === -1) {
                    this.active = data.length
                    return
                }

                this.active = firstNotApprovedIndex
            } catch (error) {
                errorHandler({ error, show: false })
            }
        },
        circleClass(index) {
            const step = this.normalizedSteps?.[index]

            if (this.isRejected(step)) {
                return {
                    rejected: true
                }
            }

            if (this.isApproved(step, index)) {
                return {
                    done: true
                }
            }

            return {
                active: index === this.active,
                next: index !== this.active
            }
        }
    },
    created() {
        this.getSteps()
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
.slide-fade-enter,
.slide-fade-leave-to {
    transform: translateY(-10px);
    opacity: 0;
}
.steps_track {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
}

.step_item {
    position: relative;
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 0;
}

.step_circle {
    width: 34px;
    height: 34px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    user-select: none;
}

.step_circle.done {
    background: #43c475;
    color: #fff;
}

.step_circle.active {
    background: #e8ecfa;
    color: var(--blue);
}

.step_circle.next {
    background: #f0f1f6;
    color: #6b7280;
}

.step_circle.rejected {
    background: #FF5C5C;
    color: #fff;
}

.step_label {
    margin-top: 10px;
    font-size: 10px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #6b7280;
    text-align: center;
    white-space: normal;
    max-width: 120px;
}

.step_label.active {
    color: var(--blue);
}

.step_line {
    position: absolute;
    top: 17px;
    left: calc(50% + 26px);
    width: calc(100% - 52px);
    height: 2px;
    background: #f0f1f6;
}

.step_line.done {
    background: #e6efe3;
}
</style>
