<template>
    <div 
        class="widget_card select-none" 
        :class="[cardColor && 'anim', isMobile && 'm']"
        :style="cardColor && `background: ${cardColor};`">
        <i v-if="!isMobile && widget.static" class="fi fi-rr-thumbtack widget_card__static" />
        <div class="widget_card__header">
            <div v-if="!isMobile && !widget.static" class="vue-draggable-handle">
                <div class="line"></div>
            </div>
        </div>
        <div class="widget_card__body no-drag">
            <div class="body_head">
                <div v-if="editName" class="w-full">
                    <a-input 
                        v-model="name" 
                        ref="nameWidget"
                        :placeholder="$t('dashboard.enter_title')"
                        @blur="cancelNameEdit"
                        @pressEnter="cancelNameEdit" />
                </div>
                <div v-else class="flex items-center truncate" @click="editNameHandler()">
                    <h3 class="truncate" :title="$t('dashboard.title_change', { name: widgetName })">
                        {{ widgetName }}
                    </h3>
                    <sup v-if="!isMobile" class="ml-1 cursor-pointer edit_btn">
                        <i 
                            class="fi fi-rr-pencil blue_color" 
                            v-tippy
                            :content="$t('dashboard.title_edit')"
                            style="font-size: 13px;" />
                    </sup>
                </div>
                <div class="actions gap-2">
                    <div v-if="$slots.actions" class="flex items-center gap-2">
                        <slot name="actions" />
                    </div>
                    <Actions 
                        :widget="widget" 
                        :editNameHandler="editNameHandler">
                        <template v-if="$slots.dropdown">
                            <slot name="dropdown" />
                        </template>
                    </Actions>
                </div>
            </div>
            <div class="body_content">
                <div v-if="$slots.contentbefore">
                    <slot name="contentbefore" />
                </div>
                <slot />
                <div v-if="$slots.contentafter">
                    <slot name="contentafter" />
                </div>
            </div>
            <div v-if="$slots.footer" class="body_footer">
                <slot name="footer" />
            </div>
        </div>
    </div>
</template>

<script>
import { errorHandler } from '@/utils/index.js'
export default {
    components: {
        Actions: () => import('./Actions/ActionSwitch.vue')
    },
    props: {
        widget: {
            type: Object,
            required: true
        },
        widgetReload: {
            type: Function,
            default: () => {}
        },
        cardColor: {
            type: String,
            default: ''
        }
    },
    computed: {
        widgetName() {
            return this.widget.name || this.widget.widget.name
        },
        isMobile() {
            return this.$store.state.isMobile
        }
    },
    data() {
        return {
            actions: null,
            loading: false,
            editName: false,
            actionLoading: false,
            name: ''
        }
    },
    methods: {
        async cancelNameEdit() {
            if(this.name !== this.widgetName) {
                try {
                    this.actionLoading = true
                    //this.$message.loading({ content: 'Обновление', key: updateKey })
                    this.editName = false
                    this.$store.commit('dashboard/UPDATE_ACTIVE_WIDGET', {
                        widgetId: this.widget.id,
                        key: 'name',
                        value: this.name
                    })
                    await this.$http.patch(`/widgets/user_widgets_on_desktop/${this.widget.id}/`, {
                        name: this.name
                    })
                    this.name = ''
                    //this.$message.success({ content: 'Обновлено', key: updateKey, duration: 2 })
                } catch(error) {
                    errorHandler({error})
                } finally {
                    this.actionLoading = false
                }
            } else {
                this.editName = false
                this.name = ''
            }
        },
        editNameHandler() {
            this.name = this.widgetName
            this.editName = true
            this.$nextTick(() => {
                this.$refs.nameWidget.$el.focus()
                if(!this.isMobile)
                    this.$refs.nameWidget.$el.select()
            })
        }
    }
}
</script>

<style lang="scss" scoped>
.widget_card{
    position: relative;
    display: flex;
    flex-direction: column;
    height: 100%;
    border-radius: var(--borderRadius);
    background: #fff;
    .edit_btn{
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &:hover{
        .edit_btn{
            opacity: 0.7;
        }
    }
    &::v-deep{
        .kanban-card.ant-card{
            cursor: default;
        }
    }
    &.anim{
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    }
    &__static{
        position: absolute;
        top: 5px;
        left: 6px;
        z-index: 5;
        border-radius: 50%;
        font-size: 8px;
    }
    &__body{
        padding-left: 20px;
        padding-right: 20px;
        padding-bottom: 20px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        .body_head{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
            h3{
                font-weight: 400;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                font-size: 18px;
                -webkit-user-select: none;
                -moz-user-select: none;
                user-select: none;
                cursor: pointer;
            }
            /*&::v-deep{
                .ant-input{
                    border: 0px;
                    box-shadow: initial;
                    font-size: 18px;
                    font-weight: 600;
                    padding: 0px;
                    color: rgba(0, 0, 0, 0.85);
                }
            }*/
            &::v-deep{
                .ant-input{
                    background: #eff2f5;
                    border: 0px;
                    box-shadow: initial;
                }
            }
            .actions{
                padding-left: 15px;
                margin-right: -10px;
                display: flex;
                align-items: center;
            }
        }
        .body_content{
            flex-grow: 1;
            overflow: hidden;
        }
        .body_footer{
            padding-top: 15px;
        }
    }
    &__header{
        display: flex;
        justify-content: center;
        align-items: center;
        height: 16px;
        min-height: 16px;
        .vue-draggable-handle{
            cursor: move;
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
            height: 16px;
            display: flex;
            justify-content: center;
            align-items: center;
            .line{
                width: 30px;
                height: 2px;
                background: #000000;
                border-radius: 2px;
                background: var(--gray);
                transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
                opacity: 0.6;
            }
            &:hover{
                .line{
                    opacity: 1;
                }
            }
        }
    }
}
</style>