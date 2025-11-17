import os
import sys
import tempfile
import shutil
import subprocess
import tarfile
import zipfile
from collections import OrderedDict

python_major_begin = 2
python_major_max_step = 2
python_minor_max_step = 10
target_package = "pip"
official_index_url = "https://pypi.python.org/simple"


def download_and_extract_package(package_name, package_version, index_url=None):
    path_downloaded = tempfile.mkdtemp()
    cmd = [
        "pip", "download",
        "--no-deps",
        "--only-binary=:all:",
        "--dest", path_downloaded,
        *(("--index-url", index_url) if index_url else ()),
        f"{package_name}=={package_version}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise subprocess.SubprocessError(result.stderr)
    filename = os.listdir(path_downloaded)[0]
    filepath = os.path.join(path_downloaded, filename)
    path_extracted = tempfile.mkdtemp()
    filename = filename.lower()
    if filename.endswith(".whl"):
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(path_extracted)
    elif filename.endswith(".tar.gz"):
        with tarfile.open(filepath, "r:gz") as tar_ref:
            tar_ref.extractall(path_extracted)
        path_extracted2 = tempfile.mkdtemp()
        p = os.path.join(path_extracted, os.listdir(path_extracted)[0])
        for file in (package_name, f"{package_name}.egg-info"):
            shutil.copyfile(os.path.join(p, file), os.path.join(path_extracted2, file))
        shutil.rmtree(path_downloaded)
        path_extracted = path_extracted2
    else:
        raise ValueError(f"Unknown file format: {filepath}")
    shutil.rmtree(path_downloaded)
    return path_extracted


def getstatusoutput(command, error=True, env=None, encode=None):
    try:
        data = subprocess.check_output(
            command, env=env, shell=True,
            stderr=subprocess.STDOUT if error else subprocess.DEVNULL)
        exitcode = 0
    except subprocess.CalledProcessError as ex:
        data = ex.output
        exitcode = ex.returncode
    data = data.decode(encode or 'utf-8')
    if data[-1:] == '\n':
        data = data[:-1]
    return exitcode, data


def get_package_versions(name, index_url=None):
    if index_url:
        args = f' --index-url {index_url}'
    else:
        args = ''
    command = f"pip index versions {name}{args}"
    rc, content = getstatusoutput(command)
    if rc:
        raise subprocess.CalledProcessError(rc, command, content)
    marker = "Available versions: "
    sep = ', '
    index = content.find(marker)
    if index == -1:
        return []
    s = content[index + len(marker):]
    index = s.find('\n')
    if index != -1:
        s = s[:index]
    return list(reversed(s.strip().split(sep)))


def is_compatible(package_name, package_version, python_version):
    return getstatusoutput(
        f"{sys.executable} -m pip install {package_name}=={package_version} "
        f"--dry-run --python-version {python_version} --no-deps"
    )[0] == 0


def main():
    target_versions = OrderedDict()
    package_versions = get_package_versions(target_package, official_index_url)
    major = python_major_begin
    minor = 0
    step_major = 0
    while True:
        step_minor = 0
        while True:
            python_version = f"{major}.{minor}"
            is_hit = False
            for package_version in package_versions:
                if is_compatible(target_package, package_version, python_version):
                    is_hit = True
                    target_versions[python_version] = package_version
            if not is_hit:
                step_minor += 1
            if step_minor >= python_minor_max_step:
                step_major += 1
                break
            minor += 1
        if step_major >= python_major_max_step:
            break
        major += 1
        minor = 0

    import json
    print(json.dumps(target_versions, indent=2))

    for python_version, package_version in target_versions.items():
        for path in download_and_extract_package(target_package, package_version, official_index_url):
            pass


if __name__ == "__main__":
    main()
