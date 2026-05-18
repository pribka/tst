<template>
    <div class="aside">
        <template v-if="project">
            <div class="flex items-center mb-4 aside_status flex-wrap">
                <a-button v-if="project.stage && project.stage.name" type="success" ghost :size="isMobile ? 'default' : 'large'">
                    {{ project.stage.name }}
                </a-button>
                <a-button :type="project.has_documentation ?  'success' : 'primary'" ghost :size="isMobile ? 'default' : 'large'">
                    {{ project.has_documentation ?  $t('invest.psd_developed') : $t('invest.psd_not_developed') }}
                </a-button>
            </div>
            <div class="aside__block">
                <div class="aside_label">{{ $t('invest.main_info') }}</div>
                <div class="block_list">
                    <div v-if="project.location" class="block_list__item">
                        <div class="name">{{ $t('invest.location') }}:</div>
                        <div class="value">{{ project.location.full_name }}</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.company_name') }}:</div>
                        <div class="value">{{ project.company_name }}</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.company_bin') }}:</div>
                        <div class="value">{{ project.company_bin }}</div>
                    </div>
                    <div v-if="project.category" class="block_list__item">
                        <div class="name">{{ $t('invest.category') }}:</div>
                        <div class="value">{{ project.category.name }}</div>
                    </div>
                    <div v-if="project.subcategory" class="block_list__item">
                        <div class="name">{{ $t('invest.subcategory') }}:</div>
                        <div class="value">{{ project.subcategory.name }}</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.director') }}:</div>
                        <div class="value">{{ project.company_director_name }}</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.director_phone') }}:</div>
                        <div class="value"><a :href="`tel:${project.company_phone}`">{{ project.company_phone }}</a></div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.foreign_investor') }}:</div>
                        <div class="value">{{ project.foreign_investor_info || $t('invest.no') }}</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.project_capacity') }}: </div>
                        <div class="value">{{ project.project_capacity }} <span v-if="project.measure_unit" class="lowercase">{{ project.measure_unit.name_short }}</span></div>
                    </div>
                    <div v-if="project.date_start" class="block_list__item">
                        <div class="name">{{ $t('invest.start_date') }}:</div>
                        <div class="value">{{ $moment(project.date_start).format('DD MMMM YYYY') }}г.</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.planned_completion') }}:</div>
                        <div class="value">{{ $moment(project.dead_line).format('DD MMMM YYYY') }}г.</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.project_stage') }}:</div>
                        <div class="value">{{ project?.stage?.name || $t('invest.not_specified') }}</div>
                    </div>
                </div>
            </div>
            <div class="aside__block">
                <div class="aside_label">{{ $t('invest.project_cost') }}</div>
                <PriceChart :item="project" graphColor="#eff2f5" :useBackground="false" />
            </div>
            <div class="aside__block">
                <div class="aside_label">{{ $t('invest.implementation_stage') }}</div>
                <div class="progress">
                    <div class="progress_label">{{ $t('invest.construction_stage') }}, %</div>
                    <div class="progress_input" :class="Number(project.installation_stage) === 100 && 'success'">
                        <div class="progress_input__active" :style="`width: ${Number(project.installation_stage)}%;`">
                            <div class="badge">{{ project.installation_stage }}%</div>
                        </div>
                    </div>
                </div>
                <div class="block_list">
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.infrastructure') }}:</div>
                        <div class="value">{{ project.infrastructure_info }}</div>
                    </div>
                </div>
            </div>
            <div class="aside__block">
                <div class="aside_label">{{ $t('invest.funding_sources') }}</div>
                <div 
                    v-for="source in project.funding_sources" 
                    :key="source.id" 
                    class="block_list source">
                    <div v-if="source.funding_source" class="block_list__item">
                        <div class="name">{{ source.funding_source.name }}:</div>
                        <div class="value">{{ source.amount }} млн. тенге</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.comment') }}:</div>
                        <div class="value">{{ source.comment }}</div>
                    </div>
                </div>
            </div>
            <div class="aside__block">
                <div class="aside_label">{{ $t('invest.additional_info') }}</div>
                <div class="block_list">
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.temporary_jobs') }}:</div>
                        <div class="value">{{ project.jobs_temporary ? jobLabel(project.jobs_temporary) : $t('invest.no') }}</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.permanent_jobs') }}:</div>
                        <div class="value">{{ project.jobs_permanent ? jobLabel(project.jobs_permanent) : $t('invest.no') }}</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.land_allocated') }}: </div>
                        <div class="value">{{ project.land_plot_is_allocated ? $t('invest.yes') : $t('invest.no') }}</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.land_plot') }}:</div>
                        <div class="value">{{ Math.round(project.land_plot) }} га</div>
                    </div>
                    <div class="block_list__item">
                        <div class="name">{{ $t('invest.cadaster') }}: </div>
                        <div class="value">{{ project.cadaster || $t('invest.no') }}</div>
                    </div>
                </div>
            </div>
        </template>
        <a-skeleton v-else active />
    </div>
</template>

<script>
import PriceChart from './PriceChart.vue'
import { declOfNum } from '../utils.js'
export default {
    components: {
        PriceChart
    },
    props: {
        loading: {
            type: Boolean,
            default: false
        },
        project: {
            type: Object,
            default: () => {}
        }
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    methods: {
        jobLabel(num, showCount = true) {
            if(showCount) {
                return num + ' ' + declOfNum(num,
                    [this.$t('invest.invest_mesto'), this.$t('invest.invest_mest'), this.$t('invest.invest_mest_plural')])
            } else {
                return declOfNum(num,
                    [this.$t('invest.invest_mesto'), this.$t('invest.invest_mest'), this.$t('invest.invest_mest_plural')])
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.aside{
    background: #fff;
    padding: 15px;
    border-radius: var(--borderRadius);
    @media (min-width: 768px) {
        background: #eff2f5;
        padding: 20px;
    }
    @media (min-width: 1700px) {
        padding: 30px;
    }
    .aside_label{
        font-size: 20px;
        color: #000000;
        margin-bottom: 20px;
    }
    &__block{
        &:not(:last-child){
            padding-bottom: 30px;
            margin-bottom: 30px;
            border-bottom: 1px solid #bfc2c4;
        }
    }
    .progress{
        margin-bottom: 20px;
        .progress_label{
            margin-bottom: 30px;
        }
        .progress_input{
            background: #ffffff;
            height: 8px;
            width: 100%;
            position: relative;
            border-radius: 8px;
            &__active{
                background: #1D65C0;
                border-radius: 8px;
                height: 100%;
                position: absolute;
                top: 0;
                left: 0;
                width: 0px;
                transition: all .3s cubic-bezier(.645,.045,.355,1);
                .badge{
                    position: absolute;
                    color: #000;
                    right: -7px;
                    top: -27px;
                }
                &::after{
                    content: "";
                    position: absolute;
                    right: 0;
                    top: -4px;
                    background: #1D65C0;
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    transition: all .3s cubic-bezier(.645,.045,.355,1);
                }
            }
            &.success{
                .progress_input__active{
                    background: rgb(63, 134, 0);
                    &::after{
                        opacity: 0;
                    }
                }
            }
        }
    }
    .aside_status{
        &::v-deep{
            .ant-btn{
                cursor: default;
                margin-bottom: 15px;
                &:not(:last-child){
                    margin-right: 15px;
                }
            }
        }
    }
    .block_list{
        font-size: 14px;
        &.equipment{
            &:not(:last-child){
                margin-bottom: 20px;
            }
        }
        &.source{
            &:not(:last-child){
                margin-bottom: 30px;
            }
        }
        .equipment_subtitle{
            font-size: 14px;
            color: #000;
            margin-bottom: 13px;
        }
        &__item{
            @media (min-width: 768px) {
                display: flex;
            }
            &:not(:last-child){
                margin-bottom: 14px;
            }
            .name{
                color: #000000;
                opacity: 0.6;
                word-break: break-word;
                @media (min-width: 768px) {
                    min-width: 210px;
                    max-width: 210px;
                    padding-right: 20px;
                }
                @media (min-width: 1200px) {
                    min-width: 260px;
                    max-width: 260px;
                }
            }
            .value{
                color: #000000;
                word-break: break-word;
            }
        }
    }
}
</style>