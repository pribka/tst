<template>
    <div 
        class="notes_card" 
        :style="form.color ? `background: ${form.color.oColor};` : ''" 
        :ref="`widgetWrap_${this.note.id}`">
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
            <div v-if="actions && actions.edit" class="ml-2 flex items-center">
                <a-button 
                    type="ui" 
                    shape="circle" 
                    size="small"
                    flaticon 
                    :loading="loading"
                    ghost
                    icon="fi-rr-trash"
                    class="mr-2"
                    @click="deleteNotes()" />
                <ColorPicker 
                    v-if="colorList.length"
                    v-model="form.color" 
                    :changeColor="changeColor"
                    :colorList="colorList" />
            </div>
        </div>
        <div class="notes_card__body" :class="(!edit && actions && actions.edit) && 'cursor-pointer'" @click="openTextEditor()">
            <CKEditor 
                v-if="edit" 
                v-model="form.content" 
                initFocus
                commentEditor
                :enterShifthHand="editNote" />
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
</template>

<script>
import { onClickOutside } from '@vueuse/core'
export default {
    props: {
        note: {
            type: Object,
            required: true
        },
        colorList: {
            type: Array,
            default: () => []
        },
        listReload: {
            type: Function,
            default: () => {}
        },
        actions: {
            type: Object,
            default: () => null
        }
    },
    components: {
        ColorPicker: () => import('./ColorPicker.vue'),
        CKEditor: () => import('@apps/CKEditor'),
        TextViewer: () => import('@apps/CKEditor/TextViewer.vue')
    },
    data() {
        return {
            loading: false,
            editName: false,
            edit: false,
            form: {
                title: "",
                content: "",
                color: null
            }
        }
    },
    created() {
        this.form = {...this.note}
    },
    methods: {
        async deleteNotes() {
            try {
                this.loading = true
                await this.$http.post('/table_actions/update_is_active/', {
                    id: this.note.id,
                    is_active: false
                })
                this.listReload()
            } catch(e) {
                console.log(e)
            } finally {
                this.loading = false
            }
        },
        openTextEditor() {
            if(!this.edit && this.actions?.edit) {
                this.edit = true
            }
        },
        changeColor(color) {
            this.form.color = color
            this.editNote()
        },
        editNameHandler() {
            if(this.actions?.edit) {
                this.editName = true
                this.$nextTick(() => {
                    this.$refs.nameWidget.$el.focus()
                    if(!this.isMobile)
                        this.$refs.nameWidget.$el.select()
                })
            }
        },
        cancelNameEdit() {
            this.editName = false
            this.editNote()
        },
        async editNote() {
            try {
                this.edit = false
                const queryData = {
                    ...this.form
                }
                if(queryData.color)
                    queryData.color = queryData.color.color
                await this.$http.put(`/notes/${queryData.id}/`, queryData)
            } catch(e) {
                console.log(e)
            }
        }
    },
    mounted() {
        this.$nextTick(() => {
            if(this.$refs[`widgetWrap_${this.note.id}`]) {
                onClickOutside(this.$refs[`widgetWrap_${this.note.id}`], () => {
                    if (this.edit) {
                        setTimeout(() => {
                            this.editNote()
                        }, 0)
                    }
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