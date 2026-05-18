<template>
    <div class="notes_list">
        <div class="notes_grid grid gap-4 grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
            <div v-if="actions && actions.edit" class="notes_card" :style="getCardStyle(form.color)" ref="widgetWrap">
                <div class="flex items-center justify-between notes_card__header">
                    <div v-if="isEditMode" class="w-full">
                        <a-input
                            v-model="form.title"
                            ref="nameWidget"
                            :placeholder="$t('directories.enter_name')"
                            @blur="cancelNameEdit"
                            @pressEnter="cancelNameEdit" />
                    </div>
                    <div v-else class="w-full">
                        <h3 class="w-full">{{ form.title || $t('directories.new_note') }}</h3>
                    </div>
                    <div class="ml-2 flex items-center notes_card__actions">
                        <a-button
                            type="ui"
                            shape="circle"
                            size="small"
                            flaticon
                            ghost
                            icon="fi-rr-edit"
                            class="mr-2"
                            @click="enterEditMode()" />
                        <ColorPicker
                            v-if="isEditMode && colorList.length"
                            v-model="form.color"
                            :changeColor="changeColor"
                            :colorList="colorList" />
                        <div
                            v-else-if="form.color"
                            class="notes_color_preview"
                            :style="`background: ${getColorCss(form.color)};`" />
                    </div>
                </div>
                <div class="notes_card__body">
                    <CKEditor
                        ref="contentEditor"
                        v-if="edit"
                        v-model="form.content"
                        commentEditor
                        :enterShifthHand="createNote" />
                    <template v-else>
                        <TextViewer
                            v-if="form.content"
                            :body="form.content"
                            class="text_view" />
                        <div v-else style="opacity: 0.6;" class="select-none">
                            {{ $t('directories.enter_note_text') }}
                        </div>
                    </template>
                </div>
            </div>
            <Notes v-for="note in list.results" :key="note.id" :note="note" :colorList="colorList" :actions="actions" :listReload="listReload" />
        </div>
        <div class="w-full">
            <infinite-loading
                @infinite="getList"
                v-bind:distance="50"
                ref="notes_infinity">
                <div
                    slot="spinner"
                    class="flex items-center justify-center inf_spinner mt-3">
                    <a-spin />
                </div>
                <div slot="no-more"></div>
                <div slot="no-results"></div>
            </infinite-loading>
        </div>
    </div>
</template>

<script>
import { onClickOutside } from '@vueuse/core'
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        ColorPicker: () => import('../../ColorPicker.vue'),
        CKEditor: () => import('@apps/CKEditor'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue'),
        InfiniteLoading: () => import('vue-infinite-loading'),
        Notes: () => import('../../Notes.vue')
    },
    props: {
        client: {
            type: Object,
            required: true
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    data() {
        return {
            loading: false,
            page: 0,
            empty: false,
            list: {
                next: true,
                count: 0,
                results: []
            },
            editName: false,
            edit: false,
            colorList: [],
            form: {
                title: "",
                content: "",
                color: null
            }
        }
    },
    computed: {
        isEditMode() {
            return this.edit || this.editName
        }
    },
    methods: {
        getColorCss(color) {
            if(!color) return ''
            if(typeof color === 'string') return color
            return color.oColor || color.color || ''
        },
        getColorPayload(color) {
            if(!color) return null
            if(typeof color === 'string') return color
            return color.color || color.oColor || null
        },
        getCardStyle(color) {
            const colorCss = this.getColorCss(color)
            return colorCss ? `background: ${colorCss};` : ''
        },
        async getList($state) {
            if(!this.loading && this.list.next) {
                try {
                    this.loading = true
                    this.page += 1
                    const params = {
                        page: this.page,
                        page_size: 8,
                        related_object: this.client.id
                    }
                    const { data } = await this.$http.get('/notes/', { params })

                    if(data) {
                        this.list.count = data.count
                        this.list.next = data.next
                    }

                    if(data.results?.length) {
                        this.list.results = this.list.results.concat(data.results)
                    }

                    if(this.page === 1 && !this.list.results.length) {
                        this.empty = true
                    }

                    if (!data.next) {
                        $state.complete()
                    } else {
                        $state.loaded()
                    }
                } catch (error) {
                    this.$message.error(this.$t('directories.error'))
                } finally {
                    this.loading = false
                }
            } else {
                $state.complete()
            }
        },
        async getColor() {
            try {
                const { data } = await this.$http.get('/notes/colors/')
                if(data) {
                    this.colorList = data.results
                    if(!this.form.color) {
                        this.form.color = this.getDefaultColor()
                    }
                }
            } catch(e) {
                console.log(e)
            }
        },
        getDefaultColor() {
            return this.colorList.find(f => f.color === '#ffffff') || this.colorList[0] || null
        },
        clearForm() {
            const preserveColor = this.form.color || this.getDefaultColor()
            this.editName = false
            this.edit = false
            this.form = {
                title: "",
                content: "",
                color: preserveColor
            }
        },
        openTextEditor() {
            if(!this.edit) {
                this.edit = true
            }
        },
        enterEditMode() {
            if(this.isEditMode) {
                this.createNote()
                return
            }
            this.editNameHandler()
            this.openTextEditor()
        },
        changeColor(color) {
            this.form.color = color
        },
        syncContentFromEditor() {
            const editorContent = this.$refs.contentEditor?.editorRef?.getData?.()
            if(typeof editorContent === 'string') {
                this.form.content = editorContent
            }
        },
        editNameHandler() {
            this.editName = true
            this.$nextTick(() => {
                this.$refs.nameWidget.$el.focus()
                if(!this.isMobile)
                    this.$refs.nameWidget.$el.select()
            })
        },
        cancelNameEdit() {
            if(!this.edit) {
                this.editName = false
            }
        },
        listReload() {
            this.page = 0
            this.list = {
                next: true,
                count: 0,
                results: []
            }
            this.$nextTick(() => {
                this.$refs['notes_infinity'].stateChanger.reset()
            })
        },
        async createNote() {
            await this.$nextTick()
            this.syncContentFromEditor()
            if(this.form.content?.length) {
                try {
                    const queryData = {
                        ...this.form,
                        related_object: this.client.id
                    }
                    if(queryData.color)
                        queryData.color = this.getColorPayload(queryData.color)
                    const { data } = await this.$http.post('/notes/', queryData)
                    if(data) {
                        this.clearForm()
                        this.listReload()
                    }
                } catch(error) {
                    errorHandler({error})
                }
            }
            this.editName = false
            this.edit = false
        }
    },
    mounted() {
        this.getColor()
        this.$nextTick(() => {
            if(this.$refs.widgetWrap) {
                onClickOutside(this.$refs.widgetWrap, (event) => {
                    if(event?.target?.closest?.('.drop_color_picker')) {
                        return
                    }
                    if(this.edit)
                        this.createNote()
                })
            }
        })
    }
}
</script>

<style lang="scss" scoped>
.notes_card{
    border: 1px solid #eaeaea;
    padding: 15px;
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    h3{
        font-weight: 600;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 18px;
        -webkit-user-select: none;
        -moz-user-select: none;
        user-select: none;
        cursor: default;
    }
    &__body{
        min-height: 300px;
        max-height: 300px;
        overflow-y: auto;
        &::v-deep{
            .ck-content{
                min-height: 260px;
            }
            .ck.ck-editor__main>.ck-editor__editable{
                background: transparent;
            }
        }
    }
    &__header{
        padding-bottom: 15px;
        &::v-deep{
            .ant-input{
                background: #eff2f5;
                border: 0px;
                box-shadow: initial;
                max-height: 27px;
            }
        }
    }
}
.notes_card__actions{
    flex-shrink: 0;
}
.notes_color_preview{
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 1px solid var(--border2);
}
</style>
