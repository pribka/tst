<template>
    <div 
        class="typography-text" 
        :class="[color && `typography-text-${color}`, underline && 'underline']">
        <slot />
    </div>
</template>

<script>
export default {
    props: {
        color: {
            type: String,
            default: ""
        },
        underline: {
            type: Boolean,
            default: false
        }
    }
}
</script>

<style lang="scss" scoped>
.typography-text{
    display: inline-block;
    font-size: 14px;
    color: var(--text);
}
.typography-text-pink {
  color: #eb2f96;
}
.typography-text-magenta {
  color: #eb2f96;
}
.typography-text-red {
  color: #FF5C5C;
}
.typography-text-volcano {
  color: #fa541c;
}
.typography-text-orange {
  color: #FF9A01;
}
.typography-text-yellow {
  color: #fadb14;
}
.typography-text-gold {
  color: #faad14;
}
.typography-text-cyan {
  color: #13c2c2;
}
.typography-text-lime {
  color: #a0d911;
}
.typography-text-green {
  color: #368225;
}
.typography-text-blue {
  color: #4777FF;
}
.typography-text-geekblue {
  color: #2f54eb;
}
.typography-text-purple {
  color: #722ed1;
}
</style>