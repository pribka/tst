export default {
    computed: {
        priorityList() { 
            return [
                {
                    icon: 'fi-rr-hourglass-start',
                    color: '#444648',
                    name: this.$t('helpdesk.priority_very_low'),
                    value: 0
                },
                {
                    icon: 'fi-rr-clock',
                    color: '#A8C985',
                    name: this.$t('helpdesk.priority_low'),
                    value: 1
                },
                {
                    icon: 'fi-rr-exclamation',
                    color: '#FF9A01',
                    name: this.$t('helpdesk.priority_medium'),
                    value: 2
                },
                {
                    icon: 'fi-rr-bolt',
                    color: '#FF9A01',
                    name: this.$t('helpdesk.priority_high'),
                    value: 3
                },
                {
                    icon: 'fi-rr-flame',
                    color: '#FF5C5C',
                    name: this.$t('helpdesk.priority_very_high'),
                    value: 4
                }
            ]}

    }
}