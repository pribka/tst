<template>
    <WidgetWrapper 
        :widget="widget" 
        ref="WidgetWrapper"
        :class="isMobile && 'mobile_widget'">
        <template slot="actions">
            <a-button 
                type="ui" 
                ghost 
                flaticon
                shape="circle"
                icon="fi-rr-settings"
                @click="openSetting()" />
        </template>
        <div class="scroll">
            <div v-if="!related_object" class="comment_empty">
                <i class="fi fi-rr-settings-sliders"></i>
                <p>{{ $t('dashboard.commentEmptyMessage') }}</p>
                <a-button type="ui" size="small" @click="openSetting()">
                    {{ $t('dashboard.settings') }}
                </a-button>
            </div>
            <template v-else>
                <div
                    v-if="relatedTitle"
                    class="related_object_link"
                    :title="relatedTitle">
                    <span class="related_object_label">
                        {{ relatedLabel }}
                    </span>
                    <a
                        :title="relatedTitle"
                        @click.prevent="openRelatedObject()">
                        {{ relatedTitle }}
                    </a>
                </div>
                <vue2CommentsComponent 
                    :key="`${related_object}_${related_model || 'default'}`"
                    :modalContainer="false"
                    :related_object="related_object"
                    :model="related_model"
                    :mentionsData="mentionsData" />
            </template>
        </div>
    </WidgetWrapper>
</template>

<script>
import eventBus from '@/utils/eventBus'
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        vue2CommentsComponent: () => import('@apps/vue2CommentsComponent')
    },
    computed: {
        isMobile() {
            return this.$store.state.isMobile
        },
        related_object() {
            const relatedObject = this.widget.random_settings?.related_object
            if(!relatedObject)
                return null
            if(typeof relatedObject === 'object')
                return relatedObject.id || null
            return relatedObject
        },
        related_model() {
            return this.widget.random_settings?.related_model || null
        },
        related_entity() {
            return this.widget.random_settings?.related_object || null
        },
        isTicketModel() {
            return this.related_model === 'help_desk_tickets'
        },
        isEventModel() {
            return this.related_model === 'events'
        },
        isTaskModel() {
            return this.related_model === 'tasks.TaskModel' || this.related_model === 'tasks'
        },
        relatedLabel() {
            if(this.isTicketModel)
                return `${this.$t('dashboard.request')}:`
            if(this.isEventModel)
                return `${this.$t('dashboard.event')}:`
            return `${this.$t('dashboard.task')}:`
        },
        mentionsData() {
            if(!this.isTaskModel || !this.related_entity)
                return []

            const task = this.related_entity
            const list = []

            const pushUser = user => {
                if(user && user.id)
                    list.push(user)
            }

            pushUser(task.author)
            pushUser(task.operator)
            pushUser(task.owner)

            if(Array.isArray(task.visors))
                task.visors.forEach(pushUser)

            if(Array.isArray(task.cooperators)) {
                task.cooperators.forEach(item => {
                    if(item?.user)
                        pushUser(item.user)
                    else
                        pushUser(item)
                })
            }

            const uniq = new Map()
            list.forEach(user => {
                const key = String(user.id)
                if(!uniq.has(key))
                    uniq.set(key, user)
            })

            const currentUserId = this.user?.id

            return Array
                .from(uniq.values())
                .filter(user => String(user.id) !== String(currentUserId))
        },
        relatedTitle() {
            if(!this.related_entity)
                return ''
            if(this.isTicketModel) {
                const number = this.related_entity.number ? `#${this.related_entity.number}` : ''
                return `${number} ${this.related_entity.name || ''}`.trim()
            }
            if(this.isEventModel)
                return `${this.related_entity.name || ''}`.trim()
            const counter = this.related_entity.counter ? `#${this.related_entity.counter}` : ''
            return `${counter} ${this.related_entity.name || ''}`.trim()
        },
        user() {
            return this.$store.state.user.user
        }
    },
    methods: {
        openSetting() {
            eventBus.$emit('openSetting', this.widget)
        },
        openRelatedObject() {
            if(!this.related_object)
                return
            if(this.isTicketModel) {
                const query = { ...this.$route.query }
                if(!query.ticketView) {
                    query.ticketView = this.related_object
                    this.$router.push({ query })
                } else {
                    query.ticketView = this.related_object
                    this.$router.push({ query })
                }
                return
            }
            if(this.isEventModel) {
                const query = { ...this.$route.query }
                query.event = this.related_object
                this.$router.push({ query })
                return
            }

            const query = Object.assign({}, this.$route.query)
            query.task = this.related_object
            if(!this.$route.query.task) {
                this.$router.push({ query })
            } else {
                this.$router.push({ query })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.scroll{
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
}
.mobile_widget{
    .scroll{
        height: 350px;
    }
}
.comment_empty{
    text-align: center;
    padding-top: 20px;
    i{
        font-size: 42px;
        color: var(--gray);
    }
    p{
        margin-top: 15px;
        margin-bottom: 20px;
        max-width: 280px;
        margin-left: auto;
        margin-right: auto;
    }
}
.related_object_link{
    margin-bottom: 12px;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
    .related_object_label{
        color: var(--gray);
        flex-shrink: 0;
    }
    a{
        color: #4777ff;
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        min-width: 0;
    }
}
</style>
