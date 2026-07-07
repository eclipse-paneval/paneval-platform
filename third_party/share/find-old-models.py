import os
import time
import uuid

exit(0)   # Disabled for now

OLD_MODEL_SECS = 30 * 24 * 3600
ROOT_PATH = "/share/project"

DATASET_DOWNLOAD_IDS = []
for key in os.environ:
    if key.endswith('DOWNLOAD_ID'):
        DATASET_DOWNLOAD_IDS.append(os.environ[key])


for name in os.listdir(ROOT_PATH):
    try:
        uuid.UUID(name)
    except ValueError:
        continue

    if name in DATASET_DOWNLOAD_IDS:
        continue

    pth = os.path.join(ROOT_PATH, name)
    if not os.path.isdir(pth):
        continue

    st = os.stat(pth)
    delta = time.time() - st.st_ctime
    if delta > OLD_MODEL_SECS:
        print(f'{pth}\t{int(delta/(24 * 3600))}d')

with open('/share/project/DONT-CLEAN-THOSE.txt', 'w') as f:
    f.write('\n'.join(DATASET_DOWNLOAD_IDS))
