<template>
    <div class="notes_list">
        <div class="notes_grid grid gap-4 grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
            <div v-if="actions && actions.edit" class="notes_card" :style="form.color ? `background: ${form.color.oColor};` : ''" ref="widgetWrap">
                <div class="flex items-center justify-between notes_card__header">
                    <div v-if="editName" class="w-full">
                        <a-input 
                            v-model="form.title" 
                            ref="nameWidget"
                            :placeholder="$t('helpdesk.enter_name')"
                            @blur="cancelNameEdit"
                            @pressEnter="cancelNameEdit" />
                    </div>
                    <h3 v-else class="w-full" @click="editNameHandler()">{{ form.title || $t('helpdesk.new_note') }}</h3>
                    <div class="ml-2">
                        <ColorPicker 
                            v-if="colorList.length"
                            v-model="form.color" 
                            :changeColor="changeColor"
                            :colorList="colorList" />
                    </div>
                </div>
                <div class="notes_card__body" :class="!edit && 'cursor-pointer'" @click="openTextEditor()">
                    <CKEditor 
                        v-if="edit" 
                        v-model="form.content" 
                        initFocus
                        commentEditor
                        :enterShifthHand="createNote" />
                    <template v-else>
                        <TextViewer 
                            v-if="form.content"
                            :body="form.content" 
                            class="text_view" />
                        <div v-else style="opacity: 0.6;" class="select-none">
                            {{ $t('helpdesk.enter_note_text') }}
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
    methods: {
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
                    this.$message.error(this.$t('helpdesk.error'))
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
                }
            } catch(e) {
                console.log(e)
            }
        },
        clearForm() {
            this.editName = false
            this.edit = false
            this.form = {
                title: "",
                content: "",
                color: null
            }
        },
        openTextEditor() {
            if(!this.edit) {
                this.edit = true
            }
        },
        changeColor(color) {
            this.form.color = color
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
            this.editName = false
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
            if(this.form.content?.length) {
                try {
                    const queryData = {
                        ...this.form,
                        related_object: this.client.id
                    }
                    if(queryData.color)
                        queryData.color = queryData.color.color
                    const { data } = await this.$http.post('/notes/', queryData)
                    if(data) {
                        this.clearForm()
                        this.listReload()
                    }
                } catch(error) {
                    errorHandler({error})
                }
            }
            this.edit = false
        }
    },
    mounted() {
        this.getColor()
        this.$nextTick(() => {
            if(this.$refs.widgetWrap) {
                onClickOutside(this.$refs.widgetWrap, () => {
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
        cursor: pointer;
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
</style>