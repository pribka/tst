<template>
    <div class="card"
         @click="open">
        <div class="header">
            <div class="range">
                <div class="icon">
                    <img
                        :data-src="clockIcon" 
                        class="lazyload" >
                </div>
                <div class="info">
                    {{ range }}
                </div>
                <div v-if="item.is_template_on" class="repeat-period">
                    {{ repeatPeriod }}
                </div>
                <div v-else class="is-off">
                    {{ $t('Disabled') }}
                </div>
            </div>
            <div v-if="item.auto_approve" class="report-form">
                <div class="badge">
                    <a-popover placement="bottom">
                        <template slot="content">
                            {{ $t('Auto-check activated') }}
                        </template>
                        <img
                            :data-src="badgeCheck" 
                            class="lazyload" >
                    </a-popover>
                </div>
                <div class="label">
                    {{ $t('Report form') }}
                </div>
                <div class="name">
                    {{ item.report_form.name }}
                </div>
            </div>
            <div v-else class="report-form-without-badge">
                <div class="label">
                    {{ $t('Report form') }}
                </div>
                <div class="name">
                    {{ item.report_form.name }}
                </div>
            </div>
        </div>
        <div class="info">
            <div class="organization">
                {{ item.org_administrator.name }}
            </div>
            <div class="dates">
                <div class="item">
                    <div class="label">
                        {{ $t('Next consolidation period') }}
                    </div>
                    <div class="data">
                        {{ $moment(item.next_start).format('DD MMMM YYYYг.') }} - {{ $moment(item.next_end).format('DD MMMM YYYYг.') }}
                    </div>
                </div>
                <div class="item">
                    <div class="label">
                        {{ $t('Next report submission deadline') }}
                    </div>
                    <div class="data">
                        {{ $moment(item.next_dead_line).format('DD MMMM YYYYг.') }}
                    </div>
                </div>
            </div>
            <div class="author">
                <div class="avatar">
                    <a-avatar
                        :size="30" 
                        :key="item.author.id"
                        :src="item.author.avatar && item.author.avatar.path ? item.author.avatar.path : ''"
                        icon="user" />
                </div>
                <div class="name">
                    {{ item.author.last_name }} {{ item.author.first_name }}
                </div>
            </div>
        </div>
    </div>
</template>
<script>
import eventBus from '@/utils/eventBus'

export default {
    name: 'TemplateCard',
    props: {
        item: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            periods: {
                WEEKLY: this.$t('WEEKLY'),
                MONTHLY: this.$t('MONTHLY'),
                YEARLY: this.$t('YEARLY')
            }
        }
    },
    computed: {
        clockIcon() {
            return require(`@/assets/images/files/clock.svg`)
        },
        badgeCheck() {
            return require(`@/assets/images/files/badge-check.svg`)
        },
        range() {
            return `${this.$moment(this.item.start).format('DD MMMM YYYYг.')} - ${this.$moment(this.item.end).format('DD MMMM YYYYг.')}`
        },
        repeatPeriod() {
            return this.periods[this.item.repeat_period]
        }
    },
    methods: {
        open() {
            eventBus.$emit('view_template', this.item.id)
        },
    }
    
}
</script>
<style lang="scss" scoped>
.card{
    width: 100%;
    min-width: 0;
    border: 1px solid rgb(235, 235, 235, 1);
    border-radius: 8px;
    padding: 20px;
    color: #000;
    font-family: Roboto;
    font-size: 14px;
    font-style: normal;
    font-weight: 400;
    background: #fff;
    .header{
        display: grid;
        grid-template-columns: 1fr;
        border-bottom: 1px solid rgb(235, 235, 235, 1);
        padding-bottom: 20px;
        row-gap: 15px;
        .range{
            display: grid;
            grid-template-columns: auto 1fr auto;
            column-gap: 8px;
            width: 100%;
            align-content: center;
            .icon{
                align-self: center;
            }
            .info{
                align-self: center;
            }
            .repeat-period{
                opacity: 0.4;
                align-self: center;
            }
            .is-off{
                color: red;
                font-weight: 400;
                align-self: center;
            }
        }

        .report-form{
            display: grid;
            grid-template-columns: repeat(2, auto);
            grid-template-areas: "badge label" "badge name";
            width: fit-content;
            column-gap: 8px;
            .badge{
                grid-area: badge;
                min-width: 0;
            }
            .label{
                grid-area: label;
                font-size: 13px;
                opacity: 0.4;
            }
            .name{
                grid-area: name;
                font-size: 16px;
            }
        }
        .report-form-without-badge{
            display: grid;
            grid-template-columns: 1fr;
            width: fit-content;
            .label{
                font-size: 13px;
                opacity: 0.4;
            }
            .name{
                font-size: 16px;
            }
        }
    }
    .info{
        width: 100%;
        .organization{
            font-size: 16px;
            line-height: 120%;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-top: 15px;
        }
        .dates{
            display: grid;
            grid-template-columns: 1fr;
            row-gap: 15px;
            margin-top: 10px;
            .item{
                display: grid;
                grid-template-columns: 1fr;
                row-gap: 7px;
                .label{
                    font-size: 13px;
                    opacity: 0.4;
                }
                .data{
                    font-size: 14px;
                    line-height: 120%;
                }
            }
        }
        .author{
            display: grid;
            grid-template-columns: auto 1fr;
            column-gap: 10px;
            width: fit-content;
            align-content: center;
            margin-top: 20px;
            .avatar{
                width: 30px;
                height: 30px;
                align-self: center;
            }
            .name{
                align-self: center;
            }
        }
    }
}
@media (max-width: 1020px) {
    .card{
        .header{
            .range{
                display: grid;
                grid-template-columns: repeat(2, auto);
                grid-template-rows: auto;
                grid-template-areas: "icon repeat-period" "icon info";
                column-gap: 8px;
                width: fit-content;
                .icon{
                    grid-area: icon;
                    align-self: start;
                }
                .info{
                    grid-area: info;
                }
                .repeat-period{
                    grid-area: repeat-period;
                }
            }
        }
    }
}
.card:hover {
    border: 1px solid #EBEBEB;
    box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.08), 0px 0px 4px 0px rgba(0, 0, 0, 0.04);
    cursor: pointer;
}
</style>