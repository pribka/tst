export const declOfNum = (n, text_forms) => {
    n = Math.abs(n) % 100; var n1 = n % 10;
    if (n > 10 && n < 20) { return text_forms[2]; }
    if (n1 > 1 && n1 < 5) { return text_forms[1]; }
    if (n1 === 1) { return text_forms[0]; }
    return text_forms[2];
}

export const formModel = {
    name: "",
    description: "",
    founder: null,
    funds_currency: null,
    workgroup_logo: null,
    social_links: [],
    is_project: true,
    with_chat: false,
    dead_line: null,
    program: null,
    counterparty: null,
    costing_object: null,
    date_start_plan: null,
    control_dates: false,
    work_directions: [],
    organization: null,
    template: "",
    use_template: false,
    selectedLocation: null,
    facility_type: null,
    facility_type3: null,
    facility_type2: null,
    location: null,
    is_countryside: false,
    locationRegion: null,
    locationDistrict: null,
    location_akimat: null,
    location_settlement: null,
    location_point: null,
    owner_name: "",
    owner_bin: "",
    ownership_form: null,
    purpose: null,
    purpose3: null,
    purpose2: null,
    building_year: null,
    area: "",
    bandwidth: null,
    storeys_number: null,
    funds: 0,
    members: {
        profile_id: []
    },
    metadata: {
        profile_id: []
    },
}
