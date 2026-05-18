<template>
    <div class="note_card rounded-lg select-none" :class="useInject && 'bg_invert'">
        <div class="note_card__wrapper">
            <div class="note_card__header">
                <div class="note_card__meta truncate">
                    <transition name="slide-left">
                        <i v-if="note.is_ai_summary === true" class="fi fi-ai-rr-sparkles status_ai_icon mr-1" v-tippy content="Сгенерировано через AI" />
                    </transition>
                    <component
                        v-if="note?.status?.name && canEdit"
                        :is="statusMenuComponent"
                        :statusName="note?.status?.name || ''"
                        :statusColor="note?.status?.color || 'default'"
                        :isDraftStatus="isDraftStatus"
                        @publish="changePublishStatus('published')"
                        @unpublish="changePublishStatus('draft')" />
                    <a-tag v-else-if="note?.status?.name" class="status_tag mb-0 flex items-center" :color="note?.status?.color || 'default'">
                        {{ note?.status?.name }}
                    </a-tag>
                    <component
                        v-if="note?.category?.name && canChangeCategory"
                        :is="categoryMenuComponent"
                        :categoryName="note?.category?.name || ''"
                        :categoryIcon="note?.category?.icon || 'fi-rr-note-sticky'"
                        :categoryColor="note?.category?.hex_color || '#8a94a6'"
                        :categoryLoading="categoryLoading"
                        :availableCategories="availableCategories"
                        @visible-change="onCategoryVisibleChange"
                        @change-category="changeCategory" />
                    <div v-else-if="note?.category?.name" v-tippy content="Категория" class="note_category">
                        <i class="fi" :class="note?.category?.icon || 'fi-rr-note-sticky'" :style="{ color: note?.category?.hex_color || '#8a94a6' }" />
                        <span v-if="!isMobile" class="truncate">{{ note?.category?.name }}</span>
                    </div>
                </div>
                <div class="note_card__actions">
                    <div v-if="visibleVisors.length" class="note_visors">
                        <div style="display: inline-flex;align-items: center;" v-tippy content="Наблюдатели">
                            <Profiler
                                v-for="visor in visibleVisors"
                                :key="`visor_${visor.id}`"
                                :user="visor"
                                :showUserName="false"
                                :avatarSize="24"
                                class="visor_avatar" />
                        </div>
                        <component
                            v-if="hiddenVisorsCount > 0"
                            :is="visorsMoreComponent"
                            :hiddenVisorsCount="hiddenVisorsCount"
                            :hiddenVisors="hiddenVisors"
                            :getPopupContainer="getPopupContainer" />
                    </div>

                    <UserDrawer
                        v-if="!readonly && canManageVisors"
                        :id="`dayPulseVisors_${note.id}`"
                        multiple
                        :dialog-style="{ top: '15px' }"
                        title="Наблюдатели"
                        v-model="visors"
                        @change="changeVisors">
                        <template #openButton>
                            <a-button
                                type="ui"
                                ghost
                                shape="circle"
                                size="small"
                                class="visor_add_btn"
                                v-tippy
                                content="Добавить наблюдателей">
                                <i class="fi fi-rr-user-add" />
                            </a-button>
                        </template>
                    </UserDrawer>

                    <component
                        v-if="!readonly"
                        :is="actionMenuComponent"
                        :canShowActions="canShowActions"
                        :canEditContent="canEditContent"
                        :canManageStatus="canManageStatus"
                        :canDelete="canDelete"
                        :isDraftStatus="isDraftStatus"
                        @edit="openEditModal"
                        @publish="changePublishStatus('published')"
                        @unpublish="changePublishStatus('draft')"
                        @delete="deleteNote" />
                </div>
            </div>

            <div class="note_card__content">
                <TextViewer :body="formattedContent" />
            </div>

            <div class="note_card__footer">
                <Profiler
                    v-if="author"
                    :user="author"
                    hideSupportTag
                    :showUserName="!isMobile"
                    :avatarSize="20"/>
                <div v-else></div>
                <div class="time">{{ displayTime }}</div>
            </div>
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
import { mapState } from 'vuex'

const listType = 'dayPulseList'

export default {
    components: {
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        UserDrawer: () => import('@apps/DrawerSelect/index.vue')
    },
    props: {
        note: {
            type: Object,
            required: true
        },
        readonly: {
            type: Boolean,
            default: false
        },
        storeKey: {
            type: String,
            required: true
        },
        useInject: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        ...mapState({
            user: state => state.user.user,
            isMobile: state => state.isMobile
        }),
        author() {
            return this.note?.author || this.note?.created_by || null
        },
        canEdit() {
            if (this.readonly) return false
            const authorId = this.author?.id
            const userId = this.user?.id
            if (!authorId || !userId) return false
            return String(authorId) === String(userId)
        },
        canShowActions() {
            return this.canEditContent || this.canManageStatus || this.canDelete
        },
        canEditContent() {
            return this.canEdit && !this.isPublishedStatus
        },
        canManageStatus() {
            return this.canEdit
        },
        canDelete() {
            return this.canEdit && !this.isPublishedStatus
        },
        canChangeCategory() {
            return this.canEdit && !this.isPublishedStatus
        },
        canManageVisors() {
            return this.canEdit && !!this.note?.id
        },
        displayTime() {
            const raw = this.note?.updated_at || this.note?.created_at
            if (!raw) return ''
            return this.$moment(raw).format('DD.MM.YYYY HH:mm')
        },
        formattedContent() {
            return this.formatNoteContent(this.note?.content || '')
        },
        categoryCode() {
            if(this.note?.category?.code)
                return this.note.category.code
            if(typeof this.note?.category === 'string')
                return this.note.category
            return this.note?.category_code || null
        },
        categories() {
            return this.$store.state.workplan.dayPulseCategories?.results || []
        },
        categoriesLoaded() {
            return this.$store.state.workplan.dayPulseCategories?.loaded || false
        },
        availableCategories() {
            if(!Array.isArray(this.categories)) return []
            return this.categories.filter(item => item?.code && item.code !== this.categoryCode)
        },
        visibleVisors() {
            const limit = this.isMobile ? 3 : 5
            return Array.isArray(this.visors) ? this.visors.slice(0, limit) : []
        },
        hiddenVisors() {
            const limit = this.isMobile ? 3 : 5
            return Array.isArray(this.visors) && this.visors.length > limit ? this.visors.slice(limit) : []
        },
        hiddenVisorsCount() {
            return this.hiddenVisors.length
        },
        isDraftStatus() {
            return this.note?.status?.code === 'draft'
        },
        isPublishedStatus() {
            return this.note?.status?.code === 'published'
        },
        statusMenuComponent() {
            return this.isMobile
                ? () => import('./actions/NoteStatusMobile.vue')
                : () => import('./actions/NoteStatusDesktop.vue')
        },
        categoryMenuComponent() {
            return this.isMobile
                ? () => import('./actions/NoteCategoryMobile.vue')
                : () => import('./actions/NoteCategoryDesktop.vue')
        },
        actionMenuComponent() {
            return this.isMobile
                ? () => import('./actions/NoteActionsMobile.vue')
                : () => import('./actions/NoteActionsDesktop.vue')
        },
        visorsMoreComponent() {
            return this.isMobile
                ? () => import('./actions/NoteVisorsMoreMobile.vue')
                : () => import('./actions/NoteVisorsMoreDesktop.vue')
        }
    },
    data() {
        return {
            visors: [],
            categoryLoading: false
        }
    },
    watch: {
        note: {
            immediate: true,
            deep: true,
            handler(value) {
                this.visors = Array.isArray(value?.visors) ? value.visors : []
            }
        }
    },
    methods: {
        hasHtmlContent(value) {
            return /<\/?[a-z][\s\S]*>/i.test(value)
        },
        escapeHtml(value) {
            return String(value)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;')
        },
        renderParagraph(lines, emphasize = false) {
            const content = lines
                .map(line => this.escapeHtml(line.trim()))
                .join('<br>')

            if(!content) return ''

            return emphasize
                ? `<p><strong>${content}</strong></p>`
                : `<p>${content}</p>`
        },
        formatPlainTextContent(value) {
            const normalized = String(value || '')
                .replace(/\r\n?/g, '\n')
                .replace(/\\n/g, '\n')
                .trim()

            if(!normalized) return ''

            const blocks = normalized
                .split(/\n\s*\n/)
                .map(block => block.split('\n').map(line => line.trimRight()).filter(line => line.trim()))
                .filter(block => block.length)

            const html = []

            blocks.forEach(block => {
                const pushParagraph = (lines, emphasize = false) => {
                    if(lines.length)
                        html.push(this.renderParagraph(lines, emphasize))
                }
                const pushList = items => {
                    if(!items.length) return
                    html.push(`<ul>${items.map(item => `<li>${this.escapeHtml(item)}</li>`).join('')}</ul>`)
                }

                let paragraph = []
                let list = []

                block.forEach(line => {
                    const trimmed = line.trim()
                    const bulletMatch = trimmed.match(/^[-*]\s+(.*)$/)

                    if(bulletMatch) {
                        if(paragraph.length) {
                            const isSectionTitle = paragraph.length === 1
                            pushParagraph(paragraph, isSectionTitle)
                            paragraph = []
                        }
                        list.push(bulletMatch[1].trim())
                        return
                    }

                    if(list.length) {
                        pushList(list)
                        list = []
                    }

                    paragraph.push(trimmed)
                })

                if(paragraph.length)
                    pushParagraph(paragraph)
                if(list.length)
                    pushList(list)
            })

            return html.join('')
        },
        formatNoteContent(value) {
            if(!value) return ''

            if(this.hasHtmlContent(value))
                return value

            return this.formatPlainTextContent(value)
        },
        getPopupContainer(trigger) {
            return trigger?.parentNode || document.body
        },
        openEditModal() {
            if (!this.canEditContent) return
            this.$emit('edit-note', this.note)
        },
        async changeVisors(value) {
            if (!this.note?.id) return
            try {
                const data = await this.$store.dispatch('workplan/updateDayPulseVisors', {
                    storeKey: this.storeKey,
                    list: listType,
                    id: this.note.id,
                    note: this.note,
                    visors: value
                })

                if(Array.isArray(data?.visors))
                    this.visors = data.visors
                else
                    this.visors = Array.isArray(value) ? value : []
            } catch (error) {
                errorHandler({ error })
            }
        },
        async onCategoryVisibleChange(visible) {
            if(!visible || this.categoriesLoaded) return

            try {
                this.categoryLoading = true
                await this.$store.dispatch('workplan/getDayPulseCategories')
            } catch (error) {
                errorHandler({ error, show: false })
            } finally {
                this.categoryLoading = false
            }
        },
        async changeCategory(category) {
            if(!this.canChangeCategory || !this.note?.id || !category || category === this.categoryCode) return

            try {
                await this.$store.dispatch('workplan/saveDayPulseNote', {
                    storeKey: this.storeKey,
                    list: listType,
                    edit: true,
                    note: {
                        id: this.note.id,
                        category
                    }
                })
                this.$message.success('Категория изменена')
            } catch (error) {
                errorHandler({ error })
            }
        },
        changePublishStatus(status) {
            if (!this.note?.id || !status) return

            const isPublish = status === 'published'
            this.$confirm({
                title: isPublish ? 'Опубликовать блок?' : 'Отменить публикацию блока?',
                content: isPublish
                    ? 'Вы действительно хотите опубликовать этот блок?'
                    : 'Вы действительно хотите отменить публикацию этого блока?',
                closable: true,
                maskClosable: true,
                cancelText: this.$t('cancel'),
                okText: 'Подтвердить',
                onOk: async () => {
                    try {
                        await this.$store.dispatch('workplan/saveDayPulseNote', {
                            storeKey: this.storeKey,
                            list: listType,
                            edit: true,
                            note: {
                                id: this.note.id,
                                status
                            }
                        })
                        this.$message.success(isPublish ? 'Блок опубликован' : 'Публикация отменена')
                    } catch (error) {
                        errorHandler({ error })
                    }
                }
            })
        },
        deleteNote() {
            if (!this.canDelete || !this.note?.id) return
            this.$confirm({
                title: 'Удалить блок?',
                content: 'Вы действительно хотите удалить этот блок?',
                closable: true,
                maskClosable: true,
                cancelText: this.$t('cancel'),
                okText: this.$t('Delete'),
                okType: 'danger',
                onOk: async () => {
                    try {
                        await this.$http.post('/table_actions/update_is_active/', [{
                            id: this.note.id,
                            is_active: false
                        }])
                        this.$emit('note-deleted', this.note.id)
                        this.$message.success('Блок удален')
                    } catch (error) {
                        errorHandler({ error })
                    }
                }
            })
        }
    }
}
</script>

<style scoped lang="scss">
.note_card {
    background: #fff;
    &.bg_invert {
        background: #f7f9fc;
    }
    &:not(:last-child) {
        margin-bottom: 10px;
        @media (min-width: 768px) {
            margin-bottom: 15px;
        }
    }
}

.note_card__wrapper {
    padding: 15px;
    @media (min-width: 768px) {
        padding: 20px;
    }
}

.note_card__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
}

.note_card__meta {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex-wrap: wrap;
}

.status_ai_icon {
    margin-left: 6px;
    color: var(--blue);
}

.slide-left-enter-active,
.slide-left-leave-active {
    transition: opacity .25s ease, transform .25s ease;
}

.slide-left-enter,
.slide-left-leave-to {
    opacity: 0;
    transform: translateX(-8px);
}

.note_category {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
    color: #6a768d;
    font-size: 13px;
    background: #f0f1f6;
    line-height: 24px;
    padding-left: 10px;
    padding-right: 10px;
    border-radius: 30px;
    min-height: 24px;
}

.note_category_dropdown {
    cursor: pointer;
}

.note_card__actions {
    display: inline-flex;
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
    flex-shrink: 0;
}

.note_visors {
    display: inline-flex;
    align-items: center;
}

.visor_avatar {
    &:not(:first-child) {
        margin-left: -8px;
    }
}

.visor_add_btn {
    min-width: 24px;
    width: 24px;
    height: 24px;
    padding: 0;
}

.note_card__content {
    color: var(--text);
    font-size: 14px;
    line-height: 1.5;
    word-break: break-word;
    padding-bottom: 12px;
    margin-bottom: 12px;
    border-bottom: 1px solid #e8e8e8;

    &::v-deep {
        p:last-child {
            margin-bottom: 0;
        }
        p {
            margin-bottom: 12px;
        }
        ul,
        ol {
            margin: 0 0 12px;
            padding-left: 20px;
        }
        li + li {
            margin-top: 4px;
        }
    }
}

.note_card__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    min-width: 0;
    .time{
        color: #8a94a6;
    }
}

.note_author {
    min-width: 0;
    max-width: 70%;
}

.time {
    font-weight: 400;
    white-space: nowrap;
}

.status_tag {
    margin-right: 0;
    line-height: 24px;
    padding-left: 10px;
    padding-right: 10px;
    border-radius: 30px;
    font-size: 13px;
}

.status_tag_dropdown {
    cursor: pointer;
}

.note_author::v-deep {
    .user_profile {
        min-width: 0;
        max-width: 100%;
    }
    .name_user {
        max-width: 100%;
    }
}
</style>
