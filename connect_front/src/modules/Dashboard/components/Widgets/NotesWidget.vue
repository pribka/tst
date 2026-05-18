<template>
    <WidgetWrapper 
        :widget="widget" 
        :cardColor="color"
        :class="isMobile && 'mobile_widget'"
        ref="widgetWrap">
        <template slot="actions">
            <ColorPicker 
                v-model="color" 
                :changeColor="changeColor" />
            <a-button 
                v-if="edit" 
                type="primary" 
                flaticon
                shape="circle"
                icon="fi-rr-check"
                @click="saveText()" />
            <a-button 
                v-else 
                type="ui" 
                ghost 
                :loading="loading"
                flaticon
                shape="circle"
                icon="fi-rr-edit"
                @click="openEditor()" />
        </template>
        <div class="notes_wrapper" @click="openTextEditor()">
            <component 
                :is="widgetComponent" 
                ref="widgetComponent"
                :widget="widget"
                :closeEditor="closeEditor"
                :text="text" />
        </div>
    </WidgetWrapper>
</template>

<script>
import { onClickOutside } from '@vueuse/core'
import { errorHandler } from '@/utils/index.js'
export default {
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    components: {
        WidgetWrapper: () => import('../WidgetWrapper.vue'),
        ColorPicker: () => import('../WidgetComponents/ColorPicker.vue')
    },
    computed: {
        widgetComponent() {
            if(this.edit) {
                return () => import('../WidgetComponents/NotesEditor.vue')
            } else {
                return () => import('../WidgetComponents/NotesText.vue')
            }
        },
        text() {
            return this.widgetText || this.widget.random_html
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            edit: false,
            widgetText: '',
            loading: false,
            color: ''
        }
    },
    created() {
        if(this.widget.random_settings?.bgColor) {
            this.color = this.widget.random_settings.bgColor
        }
    },
    methods: {
        async changeColor(color) {
            try {
                this.color = color
                await this.$http.patch(`/widgets/user_widgets_on_desktop/${this.widget.id}/`, {
                    random_settings: {
                        bgColor: color
                    }
                })
            } catch(error) {
                errorHandler({error})
            }
        },
        closeEditor() {
            this.edit = false
        },
        openEditor() {
            this.edit = !this.edit
        },
        openTextEditor() {
            if(!this.edit) {
                this.edit = true
            }
        },
        saveText() {
            this.$nextTick(async () => {
                if(this.$refs.widgetComponent) {
                    try {
                        this.loading = true
                        const random_html = this.$refs.widgetComponent.text
                        this.widgetText = random_html
                        this.$store.commit('dashboard/UPDATE_ACTIVE_WIDGET', {
                            widgetId: this.widget.id, 
                            key: 'random_html', 
                            value: random_html
                        })
                        await this.$http.patch(`/widgets/user_widgets_on_desktop/${this.widget.id}/`, {
                            random_html
                        })
                    } catch(error) {
                        errorHandler({error})
                    } finally {
                        this.loading = false
                    }
                }
                this.edit = false
            })
        }
    },
    mounted() {
        this.$nextTick(() => {
            if(this.$refs.widgetWrap) {
                onClickOutside(this.$refs.widgetWrap, () => {
                    if(this.edit)
                        this.saveText()
                })
            }
        })
    }
}
</script>

<style lang="scss" scoped>
.mobile_widget{
    &::v-deep{
        .ck-editor{
            min-height: 300px;
            max-height: 300px;

        }
    }
}
.notes_wrapper{
    height: 100%;
    &::v-deep{
        .ck-rounded-corners .ck.ck-editor__top .ck-sticky-panel .ck-toolbar, .ck.ck-editor__top .ck-sticky-panel .ck-toolbar.ck-rounded-corners{
            border-bottom-left-radius: var(--ck-border-radius);
            border-bottom-right-radius: var(--ck-border-radius);
            border-bottom-width: 1px;
            background: #ffffff;
        }
        .ck-editor__main,
        .ck-editor{
            height: 100%;
        }
        .ck-editor{
            .ck-editor__main{
                .ck-content{
                    height: calc(100% - 40px);
                    border: 0px;
                    padding-left: 0px;
                    padding-right: 0px;
                    box-shadow: initial;
                    &.ck-editor__editable{
                        background: transparent;
                    }
                }
            }
        }
    }
}
</style>