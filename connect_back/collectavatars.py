import os
import shutil
import django
from math import ceil
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bkz3.settings')
django.setup()
from users.models import ProfileModel
from bpms.workgroups.models import WorkgroupModel

from bkz3.settings import AVATAR_ROOT


def main():
    qs = ProfileModel.objects.select_related('user').filter(is_active=True,).order_by('created_at')
    count = ceil(qs.count()/100)
    print(f"start.")
    if not os.path.exists(AVATAR_ROOT):
        os.mkdir(AVATAR_ROOT)
    print(f"Copying profile avatars...")
    for each in range(count):
        profiles = qs[each*100:each*100+100]
        for profile in profiles:
            avatar = profile.avatar
            if avatar:
                avatar_path = f"{AVATAR_ROOT}{avatar.pk}.{avatar.extension}"
                if not os.path.exists(avatar_path):
                    shutil.copyfile(avatar.upload.path, avatar_path)
                    print(f"{profile.user.username}: avatar has been copied.")
                else:
                    print(f"{profile.user.username} avatar already exist.")
            else:
                print(f"{profile.user.username}: avatar does not exist.")
    print(f"Profile avatars has been copied.")
    print(f"Copying workgroup logo...")
    qs = WorkgroupModel.objects.filter(is_active=True,).order_by('created_at')
    for each in range(count):
        instances = qs[each*100:each*100+100]
        for instance in instances:
            avatar = instance.workgroup_logo
            if avatar:
                avatar_path = f"{AVATAR_ROOT}{avatar.pk}.{avatar.extension}"
                if not os.path.exists(avatar_path):
                    shutil.copyfile(avatar.upload.path, avatar_path)
                    print(f"{instance.name} {instance.pk}: workgroup_logo has been copied.")
                else:
                    print(f"{instance.name} {instance.pk} workgroup_logo already exist.")
            else:
                print(f"{instance.name} {instance.pk}: workgroup_logo does not exist.")
    print(f"Workgroup logo has been copied.")
    print("Done.")


if __name__ == "__main__":
    main()
