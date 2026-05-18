import moment from 'moment'

moment.updateLocale('kk', {
    months: ['қаңтар','ақпан','наурыз','сәуір','мамыр','маусым','шілде','тамыз','қыркүйек','қазан','қараша','желтоқсан'],
    monthsShort: ['қаң','ақп','нау','сәу','мам','мау','шіл','там','қыр','қаз','қар','жел'],
    weekdays: ['жексенбі','дүйсенбі','сейсенбі','сәрсенбі','бейсенбі','жұма','сенбі'],
    weekdaysShort: ['жс','дс','сс','ср','бс','жм','сн'],
    weekdaysMin: ['жс','дс','сс','ср','бс','жм','сн'],
    longDateFormat: {
        LT: 'HH:mm',
        LTS: 'HH:mm:ss',
        L: 'DD.MM.YYYY',
        LL: 'D MMMM YYYY',
        LLL: 'D MMMM YYYY HH:mm',
        LLLL: 'dddd, D MMMM YYYY HH:mm'
    },
    calendar: {
        sameDay: '[Бүгін сағат] LT',
        nextDay: '[Ертең сағат] LT',
        nextWeek: 'dddd [сағат] LT',
        lastDay: '[Кеше сағат] LT',
        lastWeek: '[Өткен] dddd [сағат] LT',
        sameElse: 'L'
    },
    relativeTime: {
        future: '%s ішінде',
        past: '%s бұрын',
        s: 'бірнеше секунд',
        m: 'бір минут',
        mm: '%d минут',
        h: 'бір сағат',
        hh: '%d сағат',
        d: 'бір күн',
        dd: '%d күн',
        M: 'бір ай',
        MM: '%d ай',
        y: 'бір жыл',
        yy: '%d жыл'
    },
    week: { dow: 1, doy: 7 }
})
