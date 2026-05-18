export const numberWithSpaces = (x) => {
    let parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    return parts.join(".");
}

export const statusTextSwitch = (status) => {
    switch (status) {
    case "new":
        return 'Новая'
        break;
    case "in_process":
        return 'В процессе'
        break;
    case "rejected":
        return 'Отклонена'
        break;
    case "on_rework":
        return 'На переделке'
        break;
    case "approved":
        return 'Принята'
        break;
    default:
        return 'Новая'
    }
}

export const statusColorSwitch = (status) => {
    switch (status) {
    case "new":
        return 'blue'
        break;
    case "in_process":
        return 'purple'
        break;
    case "rejected":
        return 'red'
        break;
    case "on_rework":
        return 'orange'
        break;
    case "approved":
        return 'green'
        break;
    default:
        return 'blue'
    }
}