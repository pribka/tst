export default class FormValidation {
    constructor(title='', text='', $t) {
        this.title = title
        this.text = text
        this.$t = $t
    }
    validate() {
        let errors = {}
        
        if(!this.titleValidate()) {
            errors['title'] = this.$t('chat.validation.title_empty')
        }
        if(!this.textValidate()) {
            errors['text'] = this.$t('chat.validation.text_empty')
        }
        
        return errors
    }
    titleValidate() {
        return this.title.length > 0 ? true : false
    }
    textValidate() {
        return this.text.length > 0 ? true : false
    }
}