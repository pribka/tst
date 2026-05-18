<template>
    <a-form-model
        ref="linkInvite"
        :model="form"
        :rules="rules">
        <div v-if="loading" class="flex justify-center">
            <a-spin />
        </div>
        <template v-else>
            <div class="mb-4">
                <a-alert 
                    :message="warningMessage" 
                    banner />
            </div>
            <a-form-model-item
                ref="link"
                :label="$t('team.invite_link')"
                prop="link">
                <div class="link_input">
                    <template v-if="linkLoading">
                        <div class="w-full flex items-center justify-center">
                            <a-spin size="small"/>
                        </div>
                    </template>
                    <template v-else>
                        <span class="w-full">{{ link }}</span>
                        <a-button 
                            type="link"
                            class="ant-btn-icon-only" 
                            v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }"  
                            :content="$t('team.copy_link')" 
                            @click="copyLink()">
                            <i class="fi fi-rr-copy-alt"></i>
                        </a-button>
                    </template>
                </div>
    
                <!-- <div class="token_deadline mt-1">
                    <a-collapse :bordered="false">
                        <a-collapse-panel key="1" header="Время жизни ссылки">
                            <div slot="extra" class="flex items-center gray">
                                <div class="label mr-1">
                                    <template v-if="isMobile">
                                        <template v-if="deadLineDate">
                                            {{ $t('team.until') }}
                                        </template>
                                        <template v-else>
                                            {{ $t('team.active_until') }}
                                        </template>
                                    </template>
                                    <template v-else>
                                        {{ $t('team.active_until') }}
                                    </template>
                                </div>
                                <template v-if="deadLineDate">{{ $moment(deadLineDate).format('DD.MM.YYYY HH:mm:ss') }}</template>
                                <template v-else>Без срока</template>
                            </div>
                            <div>
                                <div v-if="isMobile" class="mobile_radio">
                                    <a-radio-group 
                                        v-model="deadlineRadio"
                                        class="mb-2 w-full"
                                        :size="isMobile ? 'large' : 'default'"
                                        @change="onChangeDeadline">
                                        <a-radio-button value="day">
                                            День
                                        </a-radio-button>
                                        <a-radio-button value="week">
                                            Неделя
                                        </a-radio-button>
                                        <a-radio-button value="month">
                                            Месяц
                                        </a-radio-button>
                                    </a-radio-group>
                                    <a-radio-group 
                                        v-model="deadlineRadio"
                                        :size="isMobile ? 'large' : 'default'"
                                        class="w-full"
                                        @change="onChangeDeadline">
                                        <a-radio-button value="year">
                                            Год
                                        </a-radio-button>
                                        <a-radio-button value="infinite">
                                            Без срока
                                        </a-radio-button>
                                    </a-radio-group>
                                </div>
                                <a-radio-group 
                                    v-else
                                    v-model="deadlineRadio"
                                    class="mr-1"
                                    @change="onChangeDeadline">
                                    <a-radio-button value="day">
                                        День
                                    </a-radio-button>
                                    <a-radio-button value="week">
                                        Неделя
                                    </a-radio-button>
                                    <a-radio-button value="month">
                                        Месяц
                                    </a-radio-button>
                                    <a-radio-button value="year">
                                        Год
                                    </a-radio-button>
                                    <a-radio-button value="infinite">
                                        Без срока
                                    </a-radio-button>
                                </a-radio-group>
                                <a-date-picker 
                                    class="mt-2 md:mt-0"
                                    :class="isMobile && 'w-full'"
                                    v-model="deadlinePicket" 
                                    format="DD.MM.YYYY HH:mm:ss"
                                    :size="isMobile ? 'large' : 'default'"
                                    valueFormat="X"
                                    :disabled-date="disabledDate"
                                    :disabled-time="disabledDateTime"
                                    :show-time="{ 
                                        format: 'HH:mm',
                                        defaultValue: $moment().add('minute', 10)
                                    }" 
                                    placeholder="Выбрать дату"
                                    @change="onChangeDeadlinePicker" />
                            </div>
                            <div class="help_text">
                                При изменении времени необходимо обновить ссылку
                            </div>
                        </a-collapse-panel>
                    </a-collapse>
                </div> -->
                <div>
                    <div class="flex items-center justify-between">
                        <div>{{ $t('team.link_lifetime') }}</div>
                        <div class="flex items-center gray">
                            <div class="label mr-1">
                                <template v-if="isMobile">
                                    <template v-if="deadLineDate">
                                        {{ $t('team.until') }}
                                    </template>
                                    <template v-else>
                                        {{ $t('team.active_until') }}
                                    </template>
                                </template>
                                <template v-else>
                                    {{ $t('team.active_until') }}
                                </template>
                            </div>
                            <template v-if="deadLineDate">{{ $moment(deadLineDate).format('DD.MM.YYYY HH:mm:ss') }}</template>
                            <template v-else>{{ $t('team.no_deadline') }}</template>
                        </div>
                    </div>
                    <div>
                        <div v-if="isMobile" class="mobile_radio">
                            <a-radio-group 
                                v-model="deadlineRadio"
                                class="mb-2 w-full"
                                :size="isMobile ? 'large' : 'default'"
                                @change="onChangeDeadline">
                                <a-radio-button value="day">
                                    {{ $t('team.day') }}
                                </a-radio-button>
                                <a-radio-button value="week">
                                    {{ $t('team.week') }}
                                </a-radio-button>
                                <a-radio-button value="month">
                                    {{ $t('team.month') }}
                                </a-radio-button>
                            </a-radio-group>
                            <a-radio-group 
                                v-model="deadlineRadio"
                                :size="isMobile ? 'large' : 'default'"
                                class="w-full"
                                @change="onChangeDeadline">
                                <a-radio-button value="year">
                                    {{ $t('team.year') }}
                                </a-radio-button>
                                <a-radio-button value="infinite">
                                    {{ $t('team.no_deadline') }}
                                </a-radio-button>
                            </a-radio-group>
                        </div>
                        <a-radio-group 
                            v-else
                            v-model="deadlineRadio"
                            class="mr-1"
                            @change="onChangeDeadline">
                            <a-radio-button value="day">
                                {{ $t('team.day') }}
                            </a-radio-button>
                            <a-radio-button value="week">
                                {{ $t('team.week') }}
                            </a-radio-button>
                            <a-radio-button value="month">
                                {{ $t('team.month') }}
                            </a-radio-button>
                            <a-radio-button value="year">
                                {{ $t('team.year') }}
                            </a-radio-button>
                            <a-radio-button value="infinite">
                                {{ $t('team.no_deadline') }}
                            </a-radio-button>
                        </a-radio-group>
                        <a-date-picker 
                            class="mt-2 md:mt-0"
                            :class="isMobile && 'w-full'"
                            v-model="deadlinePicket" 
                            format="DD.MM.YYYY HH:mm:ss"
                            :size="isMobile ? 'large' : 'default'"
                            valueFormat="X"
                            :disabled-date="disabledDate"
                            :disabled-time="disabledDateTime"
                            :show-time="{ 
                                format: 'HH:mm',
                                defaultValue: $moment().add('minute', 10)
                            }" 
                            :placeholder="$t('team.select_date')"
                            @change="onChangeDeadlinePicker" />
                    </div>
                    <div class="flex justify-between items-center">
                        <div class="help_text">
                            {{ $t('team.update_link_help') }}
                        </div>
                        <a-button
                            type="link"
                            flaticon
                            icon="fi-rr-refresh"
                            @click="getNewLink">
                            {{ $t('team.update_link') }}
                        </a-button>
                    </div>
                </div>
                <div class="share_links">
                    <div class="label mr-2">{{ $t('team.share') }}</div>
                    <div 
                        class="share_btn" 
                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                        :content="$t('team.share_telegram')"
                        @click="tgShare()">
                        <img src="@/assets/images/telegram.svg" />
                    </div>
                    <div 
                        class="share_btn" 
                        v-tippy="!isMobile ? { inertia : true, duration : '[600,300]'} : { touch: false }" 
                        :content="$t('team.share_whatsapp')"
                        @click="wpShare()">
                        <img src="@/assets/images/WhatsApp.svg" />
                    </div>
                </div>
            </a-form-model-item>
        </template>
    </a-form-model>
</template>

<script>
import { mapState } from 'vuex'
export default {
    props: {
        orgId: {
            type: [String, Number],
            required: true
        }
    },
    computed: {
        ...mapState({
            isMobile: state => state.isMobile
        }),
        warningMessage() {
            return this.$t('team.warning_message')
        }
    },
    data() {
        return {
            loading: false,
            linkLoading: false,
            link: null,
            form: {},
            rules: {},
            deactivate_at: null,
            deadlineRadio: 'day',
            deadlinePicket: null,
            deadLineDate: null,
        }
    },
    created() {
        this.deactivate_at = this.$moment().add('days', 1).toISOString()
        this.getLink()
    },
    methods: {
        async getNewLink() {
            try {
                const deactivate_at = this.deactivate_at || null
                this.linkLoading = true
                const { data } = await this.$http.post(`/users/my_organizations/${this.orgId}/invite/`, {
                    deactivate_at
                })
                if(data?.invite) {
                    this.$nextTick(async () => {
                        this.updateLink(data)
                    })
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.linkLoading = false
            }
        },
        range(start, end) {
            const result = [];
            for (let i = start; i < end; i++) {
                result.push(i);
            }
            return result;
        },
        disabledDateTime() {
            return {
                disabledHours: () => this.range(0, this.$moment().format('HH')),
                disabledMinutes: () => this.range(0, this.$moment().add('minute', 10).format('mm'))
            }
        },
        disabledDate(current) {
            return current && current < this.$moment().add('days', -1).endOf('day');
        },
        onChangeDeadlinePicker(val) {
            this.deadlineRadio = null
            this.deactivate_at = this.$moment.unix(val).toISOString()
        },
        onChangeDeadline(val) {
            const value = val.target.value
            this.deadlinePicket = null

            if(value === 'week') {
                this.deactivate_at = this.$moment().add('weeks', 1).toISOString()
            }
            if(value === 'month') {
                this.deactivate_at = this.$moment().add('months', 1).toISOString()
            }
            if(value === 'year') {
                this.deactivate_at = this.$moment().add('years', 1).toISOString()
            }
            if(value === 'day') {
                this.deactivate_at = this.$moment().add('days', 1).toISOString()
            }
            if(value === 'infinite') {
                this.deactivate_at = null
            }
        },
        updateLink(data) {
            this.link = data.invite
            this.deadLineDate = data.deactivate_at
        },
        async getLink() {
            try {
                this.loading = true
                const { data } = await this.$http.post(`/users/my_organizations/${this.orgId}/invite/`, {
                    deactivate_at: this.deactivate_at
                })
                if(data?.invite) {
                    this.link = data.invite
                    this.deadLineDate = data.deactivate_at
                }
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        tgShare() {
            window.open(`https://t.me/share/url?url=${this.link}&text=${this.$t('team.temp_link_text')}`, '_blank').focus()
        },
        wpShare() {
            window.open(`https://wa.me/?text=${this.$t('team.temp_link_text')} - ${this.link}`, '_blank').focus()
        },
        copyLink() {
            try {
                navigator.clipboard.writeText(this.link)
                this.$message.success(this.$t('team.link_copied'))
            } catch(e) {
                console.log(e)
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.mobile_radio{
    &::v-deep{
        .ant-radio-group{
            display: flex;
            align-items: center;
            .ant-radio-button-wrapper{
                width: 100%;
                text-align: center;
            }
        }
    }
}
.token_deadline{
    .help_text{
        color: var(--gray);
        margin-top: 5px;
        font-size: 13px;
    }
    &::v-deep{
        .ant-collapse-borderless{
            background-color: transparent;
            .ant-collapse-content{
                width: 100%;
            }
            .ant-collapse-item{
                border: 0px;
                .ant-collapse-content-box{
                    padding: 4px 0px 0px 0px;
                }
                .ant-collapse-header{
                    padding: 12px 0px 5px 20px;
                    color: #505050;
                    .anticon{
                        left: 0px;
                        margin-top: 3px;
                    }
                }
            }
        }
    }
}
.link_input{
    background-color: #eff2f5;
    border-radius: var(--borderRadius);
    display: flex;
    align-items: center;
    padding: 5px 15px;
    line-height: 22px;
}
.share_links{
    display: flex;
    align-items: center;
    margin-top: 10px;
    .share_btn{
        cursor: pointer;
        width: 35px;
        height: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #eff2f5;
        border-radius: 50%;
        img{
            max-width: 18px;
            height: auto;
        }
        &:not(:last-child){
            margin-right: 8px;
        }
    }
}
</style>