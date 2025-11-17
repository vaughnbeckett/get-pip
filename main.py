import os

all_versions = [v.strip() for v in """
2.7
3.2
3.3
3.4
3.5
3.6
3.7
3.8
3.9
3.10
3.11
3.12
3.13
3.14
""".splitlines() if v.strip()]

tag_suffix = "-slim"

if __name__ == "__main__":
    cwd = os.getcwd()
    for version in all_versions:
        os.system("docker run --rm python:{version}{suffix} -m pip install Hello-World-Package".format(version=version, suffix=tag_suffix))
