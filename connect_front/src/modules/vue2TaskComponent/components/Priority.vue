<template>
    <div class="flex items-center" style="height: 39px">
        <div
            class="priority_block grid grid-cols-5 w-full"
            :class="`active-${value}`">
            <div
                v-if="checkPoints.ultralow"
                class="priority_item p_ultralow"
                @click="change(0)">
                <div class="line"></div>
                <div class="label">
                    {{ $t("task.ultralow") }}
                </div>
            </div>
            <div
                v-if="checkPoints.low"
                class="priority_item p_low"
                @click="change(1)">
                <div class="line"></div>
                <div class="label">
                    {{ $t("task.low") }}
                </div>
            </div>
            <div
                v-if="checkPoints.middle"
                class="priority_item p_middle"
                @click="change(2)">
                <div class="line"></div>
                <div class="label">
                    {{ $t("task.middle") }}
                </div>
            </div>
            <div
                v-if="checkPoints.tall"
                class="priority_item p_tall"
                @click="change(3)">
                <div class="line"></div>
                <div class="label">
                    {{ $t("task.tall") }}
                </div>
            </div>
            <div
                v-if="checkPoints.veryhigh"
                class="priority_item p_veryhigh"
                @click="change(4)">
                <div class="line"></div>
                <div class="label">
                    {{ $t("task.veryhigh") }}
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        value: {
            type: [String, Number],
        },
        points: {
            type: Object,
            default: () => null,
        },
    },
    computed: {
        checkPoints() {
            if (this.points && Object.keys(this.points).length) {
                return this.points;
            } else {
                return {
                    low: true,
                    middle: true,
                    tall: true,
                    ultralow: true,
                    veryhigh: true,
                };
            }
        },
    },
    methods: {
        change(val) {
            if (val !== this.value) this.$emit("input", val);
        },
    },
};
</script>

<style lang="scss" scoped>
.priority_block {
  .priority_item {
    position: relative;
    cursor: pointer;

    &.p_ultralow {
      .line {
        border-radius: var(--borderRadius) 0 0 var(--borderRadius);
        // background-color: var(--bgColor6);
      }
    }

    &.p_low {
      padding-left: 2px;

      // padding-right: 2px;
      .line {
        // border-radius: var(--borderRadius) 0 0 var(--borderRadius);
        // background-color: var(--bgColor6);
      }
    }

    &.p_middle {
      padding-left: 2px;
      padding-right: 2px;
    }

    &.p_tall {
      padding-right: 2px;
    }

    &.p_veryhigh {
      .line {
        border-radius: 0 var(--borderRadius) var(--borderRadius) 0;
      }
    }

    .line {
      background-color: var(--bgColor6);

      height: 10px;
    }

    .label {
      margin-top: 2px;
      line-height: 1rem;
      display: none;
      position: absolute;
      width: 100%;
      text-align: center;
    }
  }

  &.active-0 {
    .p_ultralow {
      .label {
        display: block;
      }

      .line {
        background-color: #434647;
      }
    }
  }

  &.active-1 {
    .p_ultralow {
      .line {
        background-color: #434647;
      }
    }

    .p_low {
      .label {
        display: block;
      }

      .line {
        background-color: #52c41a;
      }
    }
  }

  &.active-2 {
    .p_ultralow {
      .line {
        background-color: #434647;
      }
    }

    .p_low {
      .line {
        background-color: #52c41a;
      }
    }

    .p_middle {
      .label {
        display: block;
      }

      .line {
        background-color: #f7e706;
      }
    }
  }

  &.active-3 {
    .p_ultralow {
      .line {
        background-color: #434647;
      }
    }

    .p_low {
      .line {
        background-color: #52c41a;
      }
    }

    .p_middle {
      .line {
        background-color: #f7e706;
      }
    }

    .p_tall {
      .label {
        display: block;
      }

      .line {
        background-color: #faad14;
      }
    }
  }

  &.active-4 {
    .p_ultralow {
      .line {
        background-color: #434647;
      }
    }

    .p_low {
      .line {
        background-color: #52c41a;
      }
    }

    .p_middle {
      .line {
        background-color: #f7e706;
      }
    }

    .p_tall {
      .line {
        background-color: #faad14;
      }
    }

    .p_veryhigh {
      .label {
        display: block;
      }

      .line {
        background-color: #ff0000;
      }
    }
  }
}
</style>
