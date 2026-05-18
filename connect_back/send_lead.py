import requests

dict = {'fields': {"TITLE": "ИП ПРИБ К.А. Rjgbz",
                   "SOURCE_ID": 'WEB',
                   "NAME": "КОНСТАНТИН",
                   "LAST_NAME": "ПРИБ",
                   "SECOND_NAME": "ОНДРЕИЧ",
                   "PHONE": [
                       {"VALUE": "+77055854999",
                        "VALUE_TYPE": "WORK"
                        }],
                   "EMAIL": [{"VALUE": "pribka@gmail.com", "VALUE_TYPE": "WORK"}],
                   "COMMENTS": "Здравствуйте. Это тестовый лид, загруженный из dpa.it-prst.ru. Обрабатывать меня не нужно."
                   }, 'params': {"REGISTER_SONET_EVENT": "Y"}}


def send_lead_to_prst():
    res = requests.post('https://promsytex.bitrix24.ru/rest/59/ki23ug8rmnphdm5w/crm.lead.add.json', json=dict)
    pass


def first_pull():
    import requests, json
    from users.models import CustomUser, ProfileModelOuterID
    all = ProfileModelOuterID.objects.all().delete()
    starter = 0

    while True:
        check_d = {
            'filter': {'>ID': starter},
            'order': {'ID': 'ASC'}
        }
        res3 = requests.post('https://promsytex.bitrix24.ru/rest/59/ki23ug8rmnphdm5w/crm.contact.list.json',
                             json=check_d).content

        contacts = json.loads(res3)

        if len(contacts['result']) == 0:
            break
        for item in contacts['result']:
            starter = int(item['ID'])
            res4 = requests.get(
                'https://promsytex.bitrix24.ru/rest/59/ki23ug8rmnphdm5w/crm.contact.get.json?ID=' + item['ID']).content

            contact = json.loads(res4)
            print('ID', item['ID'])
            print(contact)
            emails = contact['result'].get('EMAIL')
            if not emails:
                continue
            for em in contact['result']['EMAIL']:
                print('email', em['VALUE'])
                us = CustomUser.objects.filter(email__icontains=em['VALUE']).first()
                if us and us.email.lower() == em['VALUE'].lower():
                    prof = us.profile
                    prof.external_ids.create(outer_id=item['ID'])
                    # rec.outer_id = item['ID']
                    # rec.save()
                    print('profile', prof)



            # print(starter)
