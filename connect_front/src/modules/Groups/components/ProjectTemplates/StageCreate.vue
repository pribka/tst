<template>
    <a-modal 
        :footer="null"
        :title="$t('wgr.create_stage')" 
        :visible="visible"
        @cancel="close">
        <a-form-model 
            ref="formRef"
            :model="form"
            :rules="rules">
            <a-form-model-item prop="name" :label="$t('wgr.stage_name')">
                <a-input
                    v-model="form.name"
                    size="large"
                    :placeholder="$t('wgr.stage_name')" />
            </a-form-model-item>
            <a-button
                block
                :loading="loader"
                @click="submit"
                size="large"
                type="primary"
                htmlType="submit">
                {{$t('create')}}
            </a-button>
        </a-form-model>
    </a-modal>
</template>

<script>
export default {
    props: {
        template: {
            type: String,
            required: true,
        }
    },
    data() {
        return {
            visible: false,
            loader: false,
            form: {
                name: '',
            },
            rules: {
                name: [
                    { required: true, message: this.$t('chat.field_require'), trigger: 'blur' },
                ],
            }
        };
    },
    computed: {
        driwerTitle() {
            return this.title || this.$t("task.select_user");
        },
        drawerWidth() {
            const baseWidth = 720;
            const offset = 40;
            return this.windowWidth > baseWidth + offset
                ? baseWidth
                : this.windowWidth;
        },
        windowWidth() {
            return this.$store.state.windowWidth;
        },
    },
    methods: {
        open() {
            this.visible = true
        },
        close() {
            this.form.name = ''
            this.visible = false
        },
        submit() {
            this.$refs.formRef.validate(async (valid) =>  {
                if (valid) {
                    this.createStage()
                } else {
                    console.error('Не заполнены обязательные поля');
                }
            });
        },
        async createStage() {
            const url = '/work_groups/stage_templates/'
            const payload = {
                ...this.form,
                template: this.template,
            }
            this.loader = true
            this.$http.post(url, payload)
                .then(() => {
                    this.$message.success(this.$t('wgr.stage_created'));
                    this.$emit('created')
                    this.close()
                })
                .catch(error => {
                    console.error(error)
                    this.$notification.error({
                        message: this.$t('wgt.error'),
                    })
                })
                .finally(() => {
                    this.loader = false
                })
        },
    },
};
</script>

<style lang="scss" scoped>
.drawer_body {
  display: flex;
  flex-direction: column;
  padding: 40px;
  height: calc(100% - 40px);
}

.search_wrap {
  margin-bottom: 25px;
  border: 1px solid #e9ecf5;
}

.user_tree {
  min-height: 0;

  padding-bottom: 30px;
  overflow: auto;
}

.user_popup_item {
  &:not(:last-child) {
    margin-bottom: 8px;
  }
}

.user_pop_scroll {
  max-height: 150px;
  overflow-y: auto;
  overflow-x: hidden;
}

.user_draw_input {
  .remove_users {
    right: 0;
    top: 50%;
    position: absolute;
    margin-top: -16px;
  }
}

.user_select_drawer {
  &:not(.multiple_select) {
    .drawer_body {
      height: calc(100% - 40px);
    }
  }

  &.multiple_select {
    .drawer_body {
      height: calc(100% - 40px);
    }
  }

  &::v-deep {
    .ant-drawer-content,
    .ant-drawer-wrapper-body {
      overflow: initial;
    }

    .filter_pop_wrapper {
      min-width: 100%;
      max-width: 100%;

      .filter_input {
        border: 0px;
      }
    }

    .ant-drawer-body {
      padding: 0px;
      height: calc(100% - 40px);
    }

    .drawer_header {
      border-bottom: 1px solid var(--borderColor);
    }

    .drawer_footer {
      border-top: 1px solid var(--borderColor);
      height: 40px;
      background: var(--bgColor);
      padding: 0 15px;
      align-items: center;
    }

    .drawer_body {
      .drawer_scroll {
        height: 100%;
        overflow-y: auto;
        overflow-x: hidden;

        .item {
          &:not(:last-child) {
            border-bottom: 1px solid var(--borderColor);
          }

          &:hover {
            background: var(--hoverBg);
          }

          .name {
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
          }
        }
      }
    }
  }
}
</style>
