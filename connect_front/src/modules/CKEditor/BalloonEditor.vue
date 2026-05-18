<template>
    <ckeditor
        ref="editor"
        :class="editorClassName"
        :editor="editor"
        :config="editorConfig"
        @ready="onReady" />
</template>

<script>
import main from './mixins/main.js'
import BalloonEditor from './mixins/BalloonEditor.js'
export default {
    mixins: [BalloonEditor, main]
}
</script>

<style lang="scss">
@import './scss/variables.scss';
.ck-content{
  @include ckeditorStyle;
  border-top: 0 !important;
}
</style>