<template>
    <div class="consolidation_placeholder">
        <div class="consolidation_placeholder__dummy">
            <div class="consolidation_placeholder__ai_hint">
                <img src="@/assets/svg/ai_icons.svg" class="consolidation_placeholder__ai_icon" />
                <div class="consolidation_placeholder__ai_text">
                    <div class="consolidation_placeholder__ai_line consolidation_placeholder__ai_line--primary shimmer" />
                </div>
            </div>

            <div class="consolidation_placeholder__section_title shimmer" />

            <div class="consolidation_placeholder__kpi_row">
                <div
                    v-for="index in 9"
                    :key="`kpi-${index}`"
                    class="consolidation_placeholder__kpi_card"
                    :class="{
                        'consolidation_placeholder__kpi_card--danger': index === 4,
                        'consolidation_placeholder__kpi_card--warning': index === 5
                    }">
                    <div class="consolidation_placeholder__kpi_value shimmer" />
                    <div class="consolidation_placeholder__kpi_title shimmer" />
                    <div class="consolidation_placeholder__kpi_text shimmer" />
                </div>
            </div>

            <div class="consolidation_placeholder__section_title consolidation_placeholder__section_title--charts shimmer" />

            <div class="consolidation_placeholder__chart_row">
                <div
                    v-for="index in 4"
                    :key="`chart-${index}`"
                    class="consolidation_placeholder__chart_card">
                    <div class="consolidation_placeholder__chart_title shimmer" />
                    <div class="consolidation_placeholder__chart_area">
                        <div class="consolidation_placeholder__chart_grid">
                            <div
                                v-for="line in 5"
                                :key="`line-${index}-${line}`"
                                class="consolidation_placeholder__chart_line" />
                        </div>

                        <div
                            v-if="index === 1"
                            class="consolidation_placeholder__bars_group">
                            <div
                                v-for="group in barGroups"
                                :key="`bars-a-${group}`"
                                class="consolidation_placeholder__bars_item">
                                <div class="consolidation_placeholder__bar consolidation_placeholder__bar--blue" :style="{ height: `${36 + group * 10}px` }" />
                                <div class="consolidation_placeholder__bar consolidation_placeholder__bar--green" :style="{ height: `${54 + group * 8}px` }" />
                                <div class="consolidation_placeholder__bar consolidation_placeholder__bar--red" :style="{ height: `${28 + group * 7}px` }" />
                            </div>
                        </div>

                        <div
                            v-else-if="index === 2"
                            class="consolidation_placeholder__line_chart">
                            <svg
                                class="consolidation_placeholder__line_svg"
                                viewBox="0 0 320 180"
                                preserveAspectRatio="none">
                                <path
                                    class="consolidation_placeholder__line_area consolidation_placeholder__line_area--blue"
                                    d="M20 54 C72 58, 112 70, 148 96 C180 118, 206 134, 234 144 C258 152, 280 136, 300 92 L300 170 L20 170 Z" />
                                <path
                                    class="consolidation_placeholder__line_curve consolidation_placeholder__line_curve--blue"
                                    d="M20 54 C72 58, 112 70, 148 96 C180 118, 206 134, 234 144 C258 152, 280 136, 300 92" />
                            </svg>
                        </div>

                        <div
                            v-else-if="index === 3"
                            class="consolidation_placeholder__bars_group">
                            <div
                                v-for="group in barGroups"
                                :key="`bars-b-${group}`"
                                class="consolidation_placeholder__bars_item">
                                <div class="consolidation_placeholder__bar consolidation_placeholder__bar--blue" :style="{ height: `${44 + group * 9}px` }" />
                                <div class="consolidation_placeholder__bar consolidation_placeholder__bar--gold" :style="{ height: `${26 + group * 6}px` }" />
                            </div>
                        </div>

                        <div
                            v-else
                            class="consolidation_placeholder__line_chart">
                            <svg
                                class="consolidation_placeholder__line_svg"
                                viewBox="0 0 320 180"
                                preserveAspectRatio="none">
                                <path
                                    class="consolidation_placeholder__line_area consolidation_placeholder__line_area--red"
                                    d="M22 130 C70 126, 112 120, 156 114 C190 108, 220 96, 246 142 C268 178, 286 108, 302 58 L302 170 L22 170 Z" />
                                <path
                                    class="consolidation_placeholder__line_curve consolidation_placeholder__line_curve--red"
                                    d="M22 130 C70 126, 112 120, 156 114 C190 108, 220 96, 246 142 C268 178, 286 108, 302 58" />
                            </svg>
                        </div>

                        <div class="consolidation_placeholder__chart_legend">
                            <div
                                v-if="index === 1"
                                class="consolidation_placeholder__legend_item consolidation_placeholder__legend_item--blue" />
                            <div
                                v-if="index === 1"
                                class="consolidation_placeholder__legend_item consolidation_placeholder__legend_item--green" />
                            <div
                                v-if="index === 1"
                                class="consolidation_placeholder__legend_item consolidation_placeholder__legend_item--red" />

                            <div
                                v-else-if="index === 2"
                                class="consolidation_placeholder__legend_item consolidation_placeholder__legend_item--blue" />

                            <template v-else-if="index === 3">
                                <div class="consolidation_placeholder__legend_item consolidation_placeholder__legend_item--blue" />
                                <div class="consolidation_placeholder__legend_item consolidation_placeholder__legend_item--gold" />
                            </template>

                            <div
                                v-else
                                class="consolidation_placeholder__legend_item consolidation_placeholder__legend_item--red" />
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="consolidation_placeholder__overlay" />

        <div class="consolidation_placeholder__content">
            <div class="consolidation_placeholder__icon">
                <i class="fi fi-rr-chart-line-up" />
            </div>
            <div class="consolidation_placeholder__title">
                {{ $t('workplan.consolidation_placeholder_title') }}
            </div>
            <div class="consolidation_placeholder__text">
                {{ $t('workplan.consolidation_placeholder_text') }}
            </div>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            barGroups: [1, 2, 3, 4, 5, 6, 7]
        }
    }
}
</script>

<style lang="scss" scoped>
.consolidation_placeholder{
    position: relative;
    margin-top: 14px;
    min-height: 560px;
    border-radius: 20px;
    overflow: hidden;
    &__dummy{
        position: relative;
        z-index: 1;
        padding: 22px 0 24px;
    }

    &__ai_hint{
        display: flex;
        align-items: center;
        gap: 14px;
        min-height: 58px;
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 16px;
        background: rgba(245, 230, 255, 0.55);
        box-shadow: inset 0 0 0 1px rgba(239, 206, 255, 0.72);
    }

    &__ai_icon{
        width: 28px;
        max-width: 28px;
        flex: 0 0 28px;
    }

    &__ai_text{
        flex: 1;
        min-width: 0;
    }

    &__ai_line{
        border-radius: 999px;
        &--primary{
            width: min(420px, 74%);
            height: 18px;
        }
    }

    &__overlay{
        position: absolute;
        inset: 0;
        z-index: 2;
        background:
            linear-gradient(180deg, rgba(245, 248, 253, 0.26) 0%, rgba(245, 248, 253, 0.34) 100%);
        backdrop-filter: blur(3px);
    }

    &__content{
        position: absolute;
        inset: 0;
        z-index: 3;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        text-align: center;
        padding: 36px 24px 32px;
    }

    &__icon{
        color: #5F7192;
        display: flex;
        align-items: center;
        justify-content: center;
        .fi{
            font-size: 30px;
            line-height: 1;
        }
    }

    &__title{
        margin-top: 18px;
        font-size: 22px;
        line-height: 1.2;
        font-weight: 600;
        color: #22304A;
    }

    &__text{
        margin-top: 10px;
        max-width: 460px;
        font-size: 14px;
        line-height: 1.5;
        color: #6F7F9B;
    }

    &__kpi_row{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(132px, 132px));
        gap: 12px;
    }

    &__section_title{
        width: 110px;
        height: 18px;
        border-radius: 10px;
        margin-bottom: 16px;
        &--charts{
            margin-top: 24px;
        }
    }

    &__kpi_card{
        min-height: 112px;
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.55);
        box-shadow: inset 0 0 0 1px rgba(226, 233, 244, 0.9);
        &--danger{
            box-shadow: inset 0 0 0 1px rgba(244, 199, 195, 0.95);
        }
        &--warning{
            box-shadow: inset 0 0 0 1px rgba(244, 225, 163, 0.95);
        }
    }

    &__kpi_value{
        width: 56px;
        height: 26px;
        border-radius: 10px;
    }

    &__kpi_title{
        width: 88px;
        height: 14px;
        border-radius: 8px;
        margin-top: 14px;
    }

    &__kpi_text{
        width: 72px;
        height: 12px;
        border-radius: 8px;
        margin-top: 8px;
    }

    &__chart_row{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 16px;
    }

    &__chart_card{
        min-height: 300px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.44);
        box-shadow: inset 0 0 0 1px rgba(226, 233, 244, 0.9);
        padding: 16px 16px 18px;
    }

    &__chart_title{
        width: 148px;
        height: 18px;
        border-radius: 10px;
        margin-bottom: 22px;
    }

    &__chart_area{
        height: 218px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
    }

    &__chart_grid{
        position: absolute;
        inset: 0 0 28px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        pointer-events: none;
    }

    &__chart_line{
        border-top: 2px dashed rgba(205, 216, 234, 0.62);
    }

    &__bars_group{
        height: 100%;
        display: flex;
        align-items: flex-end;
        gap: 16px;
        padding: 18px 12px 0;
    }

    &__bars_item{
        flex: 1;
        display: flex;
        align-items: flex-end;
        gap: 6px;
        min-width: 0;
    }

    &__bar{
        flex: 1;
        border-radius: 1px 1px 0 0;
        opacity: 0.82;
        &--blue{
            background: #4A94D8;
        }
        &--green{
            background: #4FBD7B;
        }
        &--red{
            background: #FB7B7B;
        }
        &--gold{
            background: #D3A03A;
        }
    }

    &__line_chart{
        position: relative;
        height: 100%;
        margin: 10px 10px 0;
    }

    &__line_svg{
        width: 100%;
        height: 100%;
        overflow: visible;
    }

    &__line_area{
        opacity: 0.16;
        &--blue{
            fill: #4A94D8;
        }
        &--red{
            fill: #FB7B7B;
        }
    }

    &__line_curve{
        fill: none;
        stroke-width: 5;
        stroke-linecap: round;
        stroke-linejoin: round;
        opacity: 0.9;
        &--blue{
            stroke: #4A94D8;
        }
        &--red{
            stroke: #F26E6E;
        }
    }

    &__chart_legend{
        display: flex;
        gap: 12px;
        margin-top: 18px;
    }

    &__legend_item{
        width: 42px;
        height: 10px;
        border-radius: 8px;
        opacity: 0.8;
        &--blue{
            background: #4A94D8;
        }
        &--green{
            background: #4FBD7B;
        }
        &--red{
            background: #FB7B7B;
        }
        &--gold{
            background: #D3A03A;
        }
    }
}

.shimmer{
    background: rgba(214, 223, 238, 0.88);
}

@media (max-width: 1200px) {
    .consolidation_placeholder{
        min-height: 500px;

        &__dummy{
            padding-top: 18px;
        }

        &__ai_hint{
            padding: 12px 16px;
        }

        &__content{
            padding-top: 28px;
        }

        &__kpi_row{
            grid-template-columns: repeat(auto-fit, minmax(124px, 1fr));
            gap: 10px;
        }

        &__chart_row{
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 14px;
        }

        &__chart_card{
            min-height: 260px;
        }

        &__chart_area{
            height: 186px;
        }

        &__content{
            padding: 28px 20px;
        }

        &__title{
            font-size: 20px;
            margin-top: 12px;
        }

        &__text{
            max-width: 520px;
        }
    }
}

@media (max-width: 768px) {
    .consolidation_placeholder{
        min-height: 420px;
        border-radius: 16px;

        &__dummy{
            padding: 16px 0;
        }

        &__ai_hint{
            gap: 12px;
            padding: 12px 14px;
        }

        &__ai_line{
            &--primary{
                width: 78%;
            }
        }

        &__content{
            text-align: center;
            align-items: center;
            padding: 64px 18px 24px;
        }

        &__title{
            font-size: 18px;
            margin-top: 12px;
        }

        &__text{
            font-size: 13px;
            max-width: 100%;
        }

        &__kpi_row{
            grid-template-columns: repeat(2, minmax(120px, 1fr));
            gap: 10px;
        }

        &__kpi_card{
            &:nth-child(n+3){
                display: none;
            }
        }

        &__chart_row{
            grid-template-columns: 1fr;
            gap: 12px;
            margin-top: 18px;
        }

        &__chart_card{
            &:nth-child(n+2){
                display: none;
            }
        }

        &__chart_card{
            min-height: 220px;
            padding: 14px;
        }

        &__chart_area{
            height: 148px;
        }
    }
}
</style>
