<template>
    <div class="sla_preview" :class="showRelated && 'mt-2'">
        <template v-if="sources.length">
            <div class="mb-2 flex items-center text-xs">
                {{ $t('helpdesk.current_source', { source: sources[0].description }) }}
            </div>
        </template>
        <div 
            v-if="currentSla" 
            class="sla_card flex xl:items-center flex-col xl:flex-row" 
            :class="showRelated ? 'gap-6' : 'gap-4'">
            <div class="sla_card__bg" :style="`background: ${currentSla.color};`" />
            <div class="sla_card__item">
                <div class="label">
                    {{ $t('helpdesk.sla_rule') }}
                </div>
                <div>
                    {{ currentSla.name }}
                </div>
            </div>
            <div v-if="currentSla.first_reaction_time" class="sla_card__item">
                <div class="label">
                    {{ $t('helpdesk.first_reaction_time') }}
                </div>
                <div>
                    {{ formatSeconds(currentSla.first_reaction_time) }}
                </div>
            </div>
            <div v-if="currentSla.solve_time" class="sla_card__item">
                <div class="label">
                    {{ $t('helpdesk.solve_time') }}
                </div>
                <div>
                    {{ formatSeconds(currentSla.solve_time) }}
                </div>
            </div>
            <div v-if="showRelated && currentSla.level" class="sla_card__item">
                <div class="label">
                    {{ $t('helpdesk.sla_level') }}
                </div>
                <div>
                    {{ currentSla.level }}
                </div>
            </div>
        </div>
        <a-collapse v-if="showRelated && sources.length && sources.length > 1" :bordered="false" class="sla_collapse">
            <a-collapse-panel key="1" :header="$t('helpdesk.sources')">
                <div v-for="(item, index) in sources" :key="index" class="sla_list">
                    <div class="mb-2">
                        {{ item.description }}<template v-if="item.related_object">: {{ item.related_object.name }}</template>
                    </div>
                    <div 
                        class="sla_card flex xl:items-center flex-col xl:flex-row" 
                        :class="showRelated ? 'gap-6' : 'gap-4'">
                        <div class="sla_card__bg" :style="`background: ${currentSla.color};`" />
                        <div class="sla_card__item">
                            <div class="label">
                                {{ $t('helpdesk.sla_rule') }}
                            </div>
                            <div>
                                {{ item.sla.name }}
                            </div>
                        </div>
                        <div v-if="item.sla.first_reaction_time" class="sla_card__item">
                            <div class="label">
                                {{ $t('helpdesk.first_reaction_time') }}
                            </div>
                            <div>
                                {{ formatSeconds(item.sla.first_reaction_time) }}
                            </div>
                        </div>
                        <div v-if="item.sla.solve_time" class="sla_card__item">
                            <div class="label">
                                {{ $t('helpdesk.solve_time') }}
                            </div>
                            <div>
                                {{ formatSeconds(item.sla.solve_time) }}
                            </div>
                        </div>
                        <div v-if="item.sla.level" class="sla_card__item">
                            <div class="label">
                                {{ $t('helpdesk.sla_level') }}
                            </div>
                            <div>
                                {{ item.sla.level }}
                            </div>
                        </div>
                    </div>
                </div>
            </a-collapse-panel>
        </a-collapse>
    </div>
</template>

<script>
import { formatSeconds } from '../../utils/utils.js'
export default {
    props: {
        sla: {
            type: Object,
            default: () => null
        },
        showRelated: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        currentSla() {
            return this.sla.sla
        },
        sources() {
            return this.sla.sources?.length ? this.sla.sources : []
        }
    },
    methods: {
        formatSeconds
    }
}
</script>

<style lang="scss" scoped>
.sla_list{
    &:not(:last-child){
        margin-bottom: 10px;
    }
}
.sla_card{
    padding: 15px;
    border-radius: 8px;
    word-break: break-word;
    position: relative;
    overflow: hidden;
    &__bg{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.1;
    }
    &:not(:last-child){
        margin-bottom: 10px;
    }
    &__item{
        .label{
            margin-bottom: 2px;
            color: #888888;
            font-size: 13px;
        }
    }
}
.sla_collapse{
    &.ant-collapse-borderless{
        background-color: transparent;
        &::v-deep{
            .ant-collapse-item{
                border: 0px;
                .ant-collapse-content-box{
                    padding-left: 0px;
                    padding-right: 0px;
                    padding-bottom: 0px;
                }
                .ant-collapse-header{
                    padding: 5px 0 5px 20px;
                    color: var(--blue);
                    .ant-collapse-arrow{
                        left: 0;
                    }
                }
            }
        }
    }
}
</style>