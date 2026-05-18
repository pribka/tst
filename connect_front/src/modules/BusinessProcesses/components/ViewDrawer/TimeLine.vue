<template>
    <a-timeline 
        class="process_timeline" 
        :pending="reloadLoading">
        <a-timeline-item>
            <div class="font-semibold">
                {{$moment(process.created_at).format('DD.MM.YYYY HH:mm')}} - Заявка создана
            </div>
        </a-timeline-item>
        <a-timeline-item 
            v-for="(item, index) in process.time_line" 
            :key="index"
            :color="color(item)">
            <a-icon 
                slot="dot" 
                :type="icon(item)" />
            <div class="font-semibold">
                {{$moment(item.created_at).format('DD.MM.YYYY HH:mm')}} - {{ statusText(item) }}
            </div>
            <div class="operator mt-1">
                <div class="mb-1 label font-light">
                    Ответственный:
                </div>
                <div class="val">
                    <Profiler
                        :avatarSize="22"
                        nameClass="text-sm"
                        :user="item.operator" />
                </div>
            </div>
            <div 
                v-if="item.comment.length || item.attachments && item.attachments.length" 
                class="comment mt-3">
                <a-alert
                    :showIcon="false"
                    banner>
                    <template 
                        v-if="item.comment"
                        slot="message">
                        Комментарий
                    </template>
                    <template slot="description">
                        <div 
                            v-if="item.comment" 
                            class="com_item">
                            {{ item.comment }}
                        </div>
                        <div 
                            v-if="item.attachments && item.attachments.length"
                            ref="lght_pwrap"
                            class="file_list com_item">
                            <TimeLineFile 
                                v-for="file in item.attachments" 
                                :key="file.id"
                                :file="file" />
                        </div>
                    </template>
                </a-alert>
            </div>
        </a-timeline-item>
        <a-timeline-item 
            v-if="process.status === 'rejected'" 
            color="red">
            <div class="font-semibold">
                {{$moment(process.finished_date).format('DD.MM.YYYY HH:mm')}} - Заявка отклонена
            </div>
        </a-timeline-item>
        <a-timeline-item 
            v-if="process.status === 'approved'" 
            color="green">
            <div class="font-semibold">
                {{$moment(process.finished_date).format('DD.MM.YYYY HH:mm')}} - Заявка утверждена
            </div>
        </a-timeline-item>
    </a-timeline>
</template>

<script>
import TimeLineFile from './TimeLineFile'
export default {
    components: {
        TimeLineFile
    },
    props: {
        process: {
            type: Object,
            required: true
        },
        reloadLoading: {
            type: Boolean,
            default: false
        }
    },
    created() {
        this.$nextTick(() => {
            this.initGallery()
        })
    },
    watch: {
        'process.time_line'() {
            this.$nextTick(() => {
                this.initGallery()
            })
        }
    },
    methods: {
        initGallery() {
            this.$nextTick(() => {
                const lightboxWrap = this.$refs[`lght_pwrap`]
                if(lightboxWrap?.length) {
                    lightboxWrap.forEach(item => {
                        const lightbox = item.querySelectorAll('.lht_l')
                        if(lightbox?.length) {
                            lightGallery(item, {
                                selector: ".lht_l",
                                thumbnail: true,
                                rotateLeft: true,
                                rotateRight: true,
                                flipHorizontal: false,
                                flipVertical: false,
                                fullScreen: true,
                                animateThumb: true,
                                showThumbByDefault: true,
                                download: true,
                                speed: 300
                            })
                        }
                    })
                }
            })
        },
        color(item) {
            switch (item.approved) {
            case true:
                return 'green'
                break;
            default:
                return 'red'
            }
        },
        icon(item) {
            switch (item.approved) {
            case true:
                return 'check'
                break;
            default:
                return 'stop'
            }
        },
        statusText(item) {
            switch (item.approved) {
            case true:
                return 'Утверждена'
                break;
            default:
                return 'Отклонена'
            }
        }
    }
}
</script>

<style lang="scss">
.process_timeline{
    .com_item{
        &:not(:last-child){
            margin-bottom: 10px;
        }
    }
    .ant-alert{
        .ant-alert-message{
            font-size: 13px;
            font-weight: 300;
        }
    }
    .file_list{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        .file_item{
            &:not(:last-child){
                margin-right: 5px;
            }
        }
        .file_wrap{
            .file_doc{
                display: flex;
                align-items: center;
                justify-content: center;
                flex-wrap: wrap;
            }
            width: 50px;
            height: 50px;
            border-radius: var(--borderRadius);
            overflow: hidden;
            border: 1px solid var(--border2);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 5px;
            text-align: center;
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
            transition: border 200ms ease-out;
            background: #fafafa;
            img{
                width: 100%;
                object-fit: cover;
                vertical-align: middle;
                -o-object-fit: cover;
            }
            span{
                font-size: 12px;
                font-weight: 300;
                display: block;
                width: 100%;
            }
        }
    }
}
</style>