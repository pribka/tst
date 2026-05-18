import { Plugin } from '@ckeditor/ckeditor5-core';
class MentionCustomization extends Plugin {
    init() {
        const editor = this.editor;

        editor.conversion.for( 'upcast' ).elementToAttribute( {
            view: {
                name: 'span',
                key: 'data-mention',
                classes: 'mention',
                attributes: {
                    'data-id': true,
                    'data-type': true,
                }
            },
            model: {
                key: 'mention',
                value: viewItem => {
                    const mentionAttribute = editor.plugins.get( 'Mention' ).toMentionAttribute( viewItem, {
                        objectId: viewItem.getAttribute('data-id'),
                        objectType: viewItem.getAttribute('data-type')
                    } );

                    return mentionAttribute;
                }
            },
            converterPriority: 'high'
        } );

        editor.conversion.for( 'downcast' ).attributeToElement( {
            model: 'mention',
            view: ( modelAttributeValue, { writer } ) => {
                if ( !modelAttributeValue ) {
                    return;
                }
                return writer.createAttributeElement( 'span', {
                    class: `mention ${modelAttributeValue.objectClass || ""}`,
                    'data-mention': modelAttributeValue.id,
                    'data-id': modelAttributeValue.objectId,
                    'data-type': modelAttributeValue.objectType
                }, {
                    priority: 20,
                    id: modelAttributeValue.uid
                } );
            },
            converterPriority: 'high'
        } );
    }
}

export default MentionCustomization