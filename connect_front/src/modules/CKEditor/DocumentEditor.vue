<template>
    <ckeditor
        :value="value"
        :editor="editor"
        :config="editorConfig"
        @input="changeHandler" />
</template>

<script>
import mixins from './mixins/mixins.js'
import ClassicEditor from './utils/editor.js'
import { colors } from './utils/index.js'

export default {
    name: "CKEditor",
    mixins: [mixins],
    data() {
        return {
            editor: ClassicEditor,
            editorConfig: {
                language: 'ru',
                fontBackgroundColor: {
                    colors,
                    colorPicker: true
                },
                fontColor: {
                    colorPicker: {
                        format: 'hex'
                    },
                    colors
                },
                fontFamily: {
                    supportAllValues: true
                },
                fontSize: {
                    options: [
                        8,
                        9,
                        11,
                        13,
                        'default',
                        17,
                        19,
                        21,
                        24,
                        26,
                        30
                    ],
                    supportAllValues: true
                },
                heading: {
                    options: [
                        { model: 'paragraph', title: 'Paragraph', class: 'ck-heading_paragraph' },
                        { model: 'heading1', view: 'h1', title: 'Heading 1', class: 'ck-heading_heading1' },
                        { model: 'heading2', view: 'h2', title: 'Heading 2', class: 'ck-heading_heading2' },
                        { model: 'heading3', view: 'h3', title: 'Heading 3', class: 'ck-heading_heading3' },
                        { model: 'heading4', view: 'h4', title: 'Heading 4', class: 'ck-heading_heading4' },
                        { model: 'heading5', view: 'h5', title: 'Heading 5', class: 'ck-heading_heading5' },
                        { model: 'heading6', view: 'h6', title: 'Heading 6', class: 'ck-heading_heading6' }
                    ]
                },
                table: {
                    contentToolbar: [
                        'toggleTableCaption',
                        '|',
                        'tableColumn',
                        'tableRow',
                        'mergeTableCells',
                        '|',
                        'tableProperties',
                        'tableCellProperties'
                    ],
                    tableProperties: {
                        borderColors: colors,
                        backgroundColors: colors
                    },
                    tableCellProperties: {
                        borderColors: colors,
                        backgroundColors: colors
                    }
                },
                toolbar: {
                    viewportTopOffset: 0, 
                    items: [
                        'heading',
                        'fontFamily',
                        'fontSize',
                        'alignment',
                        '|',
                        'bold',
                        'italic',
                        'underline',
                        'strikethrough',
                        'subscript',
                        'superscript',
                        'link',
                        'bulletedList',
                        'numberedList',
                        'blockQuote',
                        'fontColor',
                        'fontBackgroundColor',
                        'indent',
                        'outdent',
                        'pageBreak',
                        'removeFormat',
                        'selectAll',
                        '|',
                        'imageInsert',
                        'insertTable',
                        'mediaEmbed',
                        'undo',
                        'redo'
                    ]
                },
                link: {
                    addTargetToExternalLinks: true
                },
                image: {
                    toolbar: [
                        'imageStyle:inline',
                        'imageStyle:block',
                        'imageStyle:side',
                        '|',
                        'imageTextAlternative',
                        '|',
                        'linkImage'
                    ]
                },
                simpleUpload: {
                    uploadUrl: this.uploadUrl,
                    withCredentials: true,
                    headers: {
                        'X-CSRFToken': this.$cookies.get('csrftoken')
                    }
                },
                mention: {
                    feeds: [
                        {                    
                            marker: '#',
                            feed: this.getFeedItems,
                            itemRenderer: this.customItemRenderer
                        }
                    ]
                }

            }
        }
    }
}
</script>

<style lang="scss">
@import './scss/variables.scss';
.ck-content{
    @include ckeditorStyle;
}
.ck-toolbar__items{
    .ck-dropdown{
        .ck-icon{
            z-index: 100;
        }
    }
}
</style>