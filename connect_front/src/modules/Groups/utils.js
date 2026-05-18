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
    workgroup_type: "",
    public_or_private: false,
    workgroup_logo: null,
    with_chat: false,
    social_links: [],
    program: null,
    counterparty: null,
    organization: null,
    costing_object: null,
    members: {
        profile_id: []
    },
    metadata: {
        profile_id: []
    },
}