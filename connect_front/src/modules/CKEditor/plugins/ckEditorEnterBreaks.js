export function ckEditorEnterBreaks(editor) {
    editor.editing.view.document.on( 'enter', ( evt, data ) => {
        data.preventDefault();
        evt.stop();
    
        // Do something here
        console.log( 'Enter key stopped.' );
    }, { priority: 'high' } );
}