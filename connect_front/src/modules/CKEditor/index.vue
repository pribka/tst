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
import ClassicEditor from './mixins/ClassicEditor.js'
export default {
    mixins: [ClassicEditor, main]
}
</script>

<style lang="scss">
@import './scss/variables.scss';
.ck-content{
  @include ckeditorStyle;
  border-top: 0 !important;
}
.ck.ck-editor{
    z-index: 5;
}
.ck-toolbar__items{
  flex-wrap: nowrap;
  .ck-dropdown{
    .ck-icon{ z-index: 100; }
  }
}
.ck .ck-sticky-panel .ck-sticky-panel__placeholder{
  height: auto !important;
}
.ck .ck-sticky-panel .ck-sticky-panel__content{
  position: static !important;
  box-shadow: initial !important;
  border-width: initial !important;
  .ck-toolbar_grouping{
    border-bottom-width: initial !important;
  }
}
</style>