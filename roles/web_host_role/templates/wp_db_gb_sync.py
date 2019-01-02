from google.cloud import storage
import os
import glob
from subprocess import Popen
import requests
import time

storage_client = storage.Client()
ts_wp_files_bucket = storage_client.get_bucket('ts-wp-files')
ts_wp_db_dump_bucket = storage_client.get_bucket('ts-wp-db-dump')
test_path = ''

os.chdir('/root')

Popen('mysqldump -h {{ hostvars['localhost']['gce_db_host_1']['instance_data'][0]['private_ip'] }} -u {{ mysql_user }} -p{{ mysql_pass }} --databases ts_tech_db > ts_tech_db.sql', shell=True)

response = requests.request("GET", "http://metadata/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip", headers={"Metadata-Flavor": "Google"})

pub_ip = response.content

time.sleep(5)

with open("ts_tech_db.sql", 'r') as f:
    s = f.read()
    x = s.replace(pub_ip, "XXX.XXX.XXX.XXX")

with open("ts_tech_db.sql", 'w') as f:
    f.write(x)



def copy_local_file_to_gcs(bucket, local_file):
    blob = bucket.blob(local_file)
    blob.upload_from_filename(local_file)

copy_local_file_to_gcs(ts_wp_db_dump_bucket, 'ts_tech_db.sql')

os.chdir('/var/www/')

def copy_local_directory_to_gcs(bucket, local_path):
    """Recursively copy a directory of files to GCS.

    local_path should be a directory and not have a trailing slash.
    """
    assert os.path.isdir(local_path)
    def walk(local_path):
        for path in glob.glob(local_path + '/**'):
            if os.path.isdir(path):
                walk(path)
            else:
                if test_path:
                    remote_path = os.path.join(test_path, path)
                    print remote_path
                    blob = bucket.blob(remote_path)
                    blob.upload_from_filename(path)
                else:
                    remote_path = path
                    print remote_path
                    blob = bucket.blob(remote_path)
                    blob.upload_from_filename(path)

    walk(local_path)

copy_local_directory_to_gcs(ts_wp_files_bucket, 'html')


