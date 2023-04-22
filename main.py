import os
import json
import sys
import base64
import gzip


def find_latest_revision(release: str):
    js = get_python_from_command("helm history " + release + " -o json")
    return find_max_field(js, "revision")


def get_secret_as_json(release: str, revision: int):
    return get_python_from_command("kubectl get secret -o json sh.helm.release.v1." + release + ".v" + str(revision))


def get_manifest_from_secret(secret):
    release = json.loads(decode(secret["data"]["release"]))
    return release["manifest"]


def put_manifest_to_secret(manifest: str, secret):
    release = json.loads(decode(secret["data"]["release"]))
    release["manifest"] = manifest
    secret["data"]["release"] = encode(json.dumps(release, separators=(',', ':')))
    return secret


def remove_kind_from_manifest(man: str, kind: str):
    entities = man.split("---")
    filtered = ""
    for entity in entities:
        if ("kind: " + kind) not in entity and entity != "":
            filtered = filtered + "---" + entity
    return filtered


def encode(string: str):
    return base64.b64encode(base64.b64encode(gzip.compress(string.encode('utf-8')))).decode('utf-8')


def decode(base64_string):
    return gzip.decompress(base64.b64decode(base64.b64decode(base64_string))).decode('utf-8')


def get_python_from_command(command: str):
    return json.loads(os.popen(command).read())


def apply_object(js):
    os.popen("echo " + str(json.dumps(js, separators=(',', ':'))) + " > tmp.json").read()
    os.popen("kubectl apply -f tmp.json").read()
    os.remove("tmp.json")


def create_backup_and_delete(js):
    name = js["metadata"]["name"]
    #js["metadata"]["name"] = name + ".backup"
    #os.popen("echo " + str(json.dumps(js, separators=(',', ':'))) + " > tmp.json").read()
    os.popen("kubectl delete secrets/" + name).read()
    #os.popen("kubectl create -f tmp.json").read()
    #os.remove("tmp.json")


def find_max_field(objects, field_name):
    if not objects and field_name not in objects[0]:
        return None

    return max(objects, key=lambda x: x[field_name])[field_name]


rev = find_latest_revision(sys.argv[1])
secret = get_secret_as_json(sys.argv[1], rev)
create_backup_and_delete(secret)


manifest = get_manifest_from_secret(secret)
filtered_manifest = remove_kind_from_manifest(manifest, sys.argv[2])
edited_secret = put_manifest_to_secret(filtered_manifest, secret)
apply_object(edited_secret)


