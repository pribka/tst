import BalloonEditor from '@ckeditor/ckeditor5-editor-balloon/src/ballooneditor'
import Essentials from '@ckeditor/ckeditor5-essentials/src/essentials'
import Autoformat from '@ckeditor/ckeditor5-autoformat/src/autoformat'
import Bold from '@ckeditor/ckeditor5-basic-styles/src/bold'
import Italic from '@ckeditor/ckeditor5-basic-styles/src/italic'
import strikethrough from '@ckeditor/ckeditor5-basic-styles/src/strikethrough'
import underline from '@ckeditor/ckeditor5-basic-styles/src/underline'
import subscript from '@ckeditor/ckeditor5-basic-styles/src/subscript'
import superscript from '@ckeditor/ckeditor5-basic-styles/src/superscript'
import Heading from '@ckeditor/ckeditor5-heading/src/heading'
import Indent from '@ckeditor/ckeditor5-indent/src/indent'
import Link from '@ckeditor/ckeditor5-link/src/link'
import List from '@ckeditor/ckeditor5-list/src/list'
import MediaEmbed from '@ckeditor/ckeditor5-media-embed/src/mediaembed'
import Paragraph from '@ckeditor/ckeditor5-paragraph/src/paragraph'
import { Table, TableCellProperties, TableProperties, TableCaption, TableToolbar } from '@ckeditor/ckeditor5-table'
import BlockQuote from '@ckeditor/ckeditor5-block-quote/src/blockquote'
import Image from '@ckeditor/ckeditor5-image/src/image'
import ImageToolbar from '@ckeditor/ckeditor5-image/src/imagetoolbar'
import Font from '@ckeditor/ckeditor5-font/src/font'
import ImageCaption from '@ckeditor/ckeditor5-image/src/imagecaption'
import ImageStyle from '@ckeditor/ckeditor5-image/src/imagestyle'
import ImageResize from '@ckeditor/ckeditor5-image/src/imageresize'
import LinkImage from '@ckeditor/ckeditor5-link/src/linkimage'
import SimpleUploadAdapter from '@ckeditor/ckeditor5-upload/src/adapters/simpleuploadadapter'
import ImageInsert from '@ckeditor/ckeditor5-image/src/imageinsert'
import Alignment from '@ckeditor/ckeditor5-alignment/src/alignment'
import RemoveFormat from '@ckeditor/ckeditor5-remove-format/src/removeformat'
import PasteFromOffice from '@ckeditor/ckeditor5-paste-from-office/src/pastefromoffice.js'
import Clipboard from '@ckeditor/ckeditor5-clipboard/src/clipboard'
import CodeBlock from '@ckeditor/ckeditor5-code-block/src/codeblock'
import AutoLink from '@ckeditor/ckeditor5-link/src/autolink'
import { SelectAll } from '@ckeditor/ckeditor5-select-all'
import { Mention } from '@ckeditor/ckeditor5-mention'
import { PageBreak } from '@ckeditor/ckeditor5-page-break'
import FGenerate from '../plugins/FGenerate.js'
import MentionCustomization from '../plugins/MentionCustomization'

BalloonEditor.builtinPlugins = [
    PasteFromOffice,
    Clipboard,
    Essentials,
    Autoformat,
    Bold,
    Italic,
    Heading,
    RemoveFormat,
    Font,
    Indent,
    Link,
    List,
    MediaEmbed,
    TableCaption,
    Paragraph,
    Table,
    TableToolbar,
    TableProperties,
    TableCellProperties,
    BlockQuote,
    Image,
    ImageToolbar,
    ImageCaption,
    ImageStyle,
    ImageResize,
    LinkImage,
    SimpleUploadAdapter,
    ImageInsert,
    Alignment,
    CodeBlock,
    AutoLink,
    Mention,
    PageBreak,
    MentionCustomization,
    FGenerate,
    strikethrough,
    underline,
    subscript,
    superscript,
    SelectAll
]

export default BalloonEditor
