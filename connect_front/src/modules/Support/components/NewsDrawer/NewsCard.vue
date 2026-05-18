<template>
    <div class="pb-4">
        <div ref="newsCard" class="news_card" @click="openNews">
            <div class="created_data">
                <i class="fi fi-rr-calendar"></i> {{ $moment(item.created_at).format('DD MMM YYYY г.') }}
            </div>
            <h2>
                <span v-if="item.is_important" class="important">
                    <img src="../../assets/img/fire.svg" />
                </span>
                {{ item.title }}
            </h2>
            <div class="main_text">
                {{ shortText }}
            </div>
            <div class="news_card__actions">
                <a-button type="flat_primary" class="flex items-center" @click.stop="openNews">
                    {{ $t('open') }}
                    <i class="fi fi-rr-arrow-small-right ml-2" />
                </a-button>
                <div class="flex items-center gap-1 like_actions" @click.stop>
                    <div class="flex items-center">
                        <a-button
                            type="ui_ghost"
                            flaticon
                            shape="circle"
                            icon="fi-rr-social-network"
                            :class="{ 'blue_color': myVote === 'like'}"
                            @click.stop="vote('like')" />
                        <div v-if="taskVote.likes_count" class="vote_count">
                            {{ taskVote.likes_count }}
                        </div>
                    </div>
                    <div class="flex items-center">
                        <a-button
                            type="ui_ghost"
                            class="ml-1"
                            flaticon
                            shape="circle"
                            icon="fi-rr-hand"
                            :class="{ 'text_red': myVote === 'dislike'}"
                            @click.stop="vote('dislike')" />
                        <div v-if="taskVote.dislikes_count" class="vote_count">
                            {{ taskVote.dislikes_count }}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import eventBus from '@/utils/eventBus'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        item: {
            type: Object,
            required: true
        },
        setNewsRead: {
            type: Function,
            default: () => {}
        },
        externalVote: {
            type: Object,
            default: null
        },
        updateNewsVote: {
            type: Function,
            default: () => {}
        }
    },
    computed: {
        myVote() {
            if(this.taskVote.my_vote === null)
                return null
            if(this.taskVote.my_vote)
                return 'like'
            return 'dislike'
        },
        shortText() {
            const source = this.item.short_content || this.clearHtml(this.item.content)
            const maxLength = 240
            if(!source)
                return ''
            if(source.length <= maxLength)
                return source
            return `${source.slice(0, maxLength).trim()}...`
        }
    },
    data() {
        return {
            taskVote: {
                likes_count: 0,
                dislikes_count: 0,
                my_vote: null
            },
            taskVoteLoading: false
        }
    },
    watch: {
        externalVote: {
            deep: true,
            handler(v) {
                if(v) {
                    this.taskVote = {...v}
                }
            }
        }
    },
    created() {
        if(this.externalVote) {
            this.taskVote = {...this.externalVote}
        } else {
            this.getVote()
        }
    },
    methods: {
        clearHtml(value = '') {
            return String(value).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
        },
        openNews() {
            if(this.$route.query.newsItem === this.item.id)
                return
            const query = {
                ...this.$route.query,
                newsItem: this.item.id
            }
            this.$router.push({ query })
            if(!this.item.has_read) {
                this.setNewsRead(this.item.id)
                eventBus.$emit('read_news_count')
            }
        },
        syncVote() {
            const payload = {
                id: this.item.id,
                vote: {...this.taskVote}
            }
            this.updateNewsVote(payload.id, payload.vote)
            eventBus.$emit('support_news_vote_changed', payload)
        },
        async vote(choice) {
            let boolChoice,
                fieldToVote,
                oppositeFieldToVote
            if (choice === 'like') {
                fieldToVote = 'likes_count'
                oppositeFieldToVote = 'dislikes_count'
                boolChoice = true
            } else if (choice === 'dislike') {
                fieldToVote = 'dislikes_count'
                oppositeFieldToVote = 'likes_count'
                boolChoice = false
            }
            const payload = {
                vote: boolChoice
            }

            await this.$http.post(`vote/${this.item.id}/`, payload)
                .then(() => {
                    if(this.taskVote.my_vote !== null) {
                        if(this.taskVote.my_vote === boolChoice) {
                            this.taskVote[fieldToVote] += -1
                            this.taskVote.my_vote = null
                        } else {
                            this.taskVote[oppositeFieldToVote] += -1
                            this.taskVote[fieldToVote] += 1
                            this.taskVote.my_vote = boolChoice
                        }
                    } else {
                        this.taskVote[fieldToVote] += 1
                        this.taskVote.my_vote = boolChoice
                    }
                    this.syncVote()
                })
                .catch(error => errorHandler({ error }))
        },
        async getVote() {
            try {
                this.taskVoteLoading = true
                const { data } = await this.$http.get(`vote/${this.item.id}/`)
                this.taskVote = data
                this.syncVote()
            } catch(error) {
                errorHandler({ error, show: false })
            } finally {
                this.taskVoteLoading = false
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.vote_count{
    color: #888888;
}
.like_actions{
    &::v-deep{
        .ant-badge-count{
            min-width: 15px;
            height: 15px;
            line-height: 15px;
            top: 4px;
            right: 2px;
            font-size: 10px;
            &.ant-badge-multiple-words{
                padding: 0 4px;
            }
            .ant-scroll-number-only{
                height: 15px;
                p{
                    height: 15px;
                }
            }
        }
        .ant-badge-count{
            font-size: 10px !important;
            min-width: 17px;
            height: 17px;
            padding: 0 6px;
            line-height: 17px;
        }
    }
}
.news_card{
    border-radius: var(--borderRadius);
    padding: 15px;
    background: #f7f9fc;
    cursor: pointer;
    @media (min-width: 1600px) {
        padding: 20px;
    }
    h2{
        font-weight: 400;
        font-size: 16px;
        margin-bottom: 15px;
        line-height: 22px;
        display: flex;
        align-items: center;
        word-break: break-word;
        .important{
            margin-right: 6px;
            min-width: 15px;
            @media (min-width: 768px) {
                min-width: 20px;
            }
            img{
                max-width: 15px;
                @media (min-width: 768px) {
                    max-width: 20px;
                }
            }
        }
    }
    .created_data{
        color: #888888;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        i{
            margin-right: 10px;
        }
    }
    .main_text{
        font-size: 14px;
        line-height: 22px;
        color: #888888;
        margin-bottom: 12px;
        white-space: pre-line;
        word-break: break-word;
    }
    &__actions{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
    }
}
</style>
