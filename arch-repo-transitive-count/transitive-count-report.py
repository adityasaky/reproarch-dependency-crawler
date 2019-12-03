#!/usr/bin/env python3
import glob
import sys
import os
import tarfile
import datetime
import json


PLATFORMS = ["x86_64", "any"]
EXTENSIONS = ["xz", "zst"]
VERSION_OPERATORS = [">", ">=", "==", "<=", "<"]


def find_tarfiles(path):
    all_files = []
    for extension in EXTENSIONS:
        all_files.extend(glob.glob(os.path.join(path,
            "*.{}".format(extension))))
    return all_files


def read_pkginfo_buildinfo(path):
    if not os.path.exists(path) or not os.path.isfile(path):
        raise Exception("This is not a valid path!")

    with tarfile.open(path, "r:*") as fp:
        try:
            pkginfo = fp.extractfile(".PKGINFO").read()
            buildinfo = fp.extractfile(".BUILDINFO").read()
        except:
            return "", ""
    
    return pkginfo.decode(), buildinfo.decode()


def decode_pkginfo(pkginfo):
    explicit_dependencies = []
    pkgname = ""
    arch = ""
    pkgver = ""
    
    for line in pkginfo.splitlines():
        # can this just be "depend" in line?
        if line.startswith("depend") or line.startswith("makedepend"):
            pkg = line.split(" = ")[1]
            for operator in VERSION_OPERATORS:
                if operator in pkg:
                    pkg = pkg.split(operator)[0]
                    break
            explicit_dependencies.append(pkg)
        elif line.startswith("optdepend"):
            pkg = line.split(" = ")[1].split(":")[0]
            for operator in VERSION_OPERATORS:
                if operator in pkg:
                    pkg = pkg.split(operator)[0]
                    break
            explicit_dependencies.append(pkg)
        elif line.startswith("pkgname"):
            pkgname = line.split(" = ")[1]
        # elif line.startswith("arch"):
        #     arch = line.split(" = ")[1]
        # elif line.startswith("pkgver"):
        #     pkgver = line.split(" = ")[1]
    
    return {"pkgname": pkgname, "pkgver": pkgver, "arch": arch}, explicit_dependencies


def decode_buildinfo(buildinfo):
    exhaustive_dependencies = []

    for line in buildinfo.splitlines():
        if line.startswith("installed"):
            pkg = line.split(" = ")[1]
            pkg_split = pkg.rsplit("-", 3)
            if len(pkg_split) < 4:
                pkg_split.append("x86_64")
            elif pkg_split[3] not in PLATFORMS:
                pkg_split[3] = "x86_64"
                # pkg_split = find_platform(pkg)
                # if pkg_split is None:
                #     continue
            name, pkgver, build, pfm = pkg_split
            exhaustive_dependencies.append(name)
    
    return exhaustive_dependencies


def add_package_to_dict(dictionary, key, value):
    if key not in dictionary:
        dictionary[key] = [value]

    elif value not in dictionary[key]:
        dictionary[key].append(value)


def find_transitive_count(explicit_dependencies, exhaustive_dependencies):
    explicit_dependencies = set(explicit_dependencies)
    exhaustive_dependencies = set(exhaustive_dependencies)

    return len(exhaustive_dependencies - explicit_dependencies)


def main(path=".", out="."):
    package_paths = []
    now = datetime.datetime.now()
    today = "-".join([str(now.year), str(now.month), str(now.day)])
    explicit_transitive_count_file_name = "transitive_count_" + today + ".json"

    explicit_transitive_count_file_path = os.path.join(out, explicit_transitive_count_file_name)

    try:
        with open(explicit_transitive_count_file_path) as fp:
            explicit_transitive_count = json.load(fp)
    except Exception:
        explicit_transitive_count = {}

    package_paths = find_tarfiles(path)

    for package_path in package_paths:
        pkginfo, buildinfo = read_pkginfo_buildinfo(package_path)
        pkgdetails, explicit_dependencies = decode_pkginfo(pkginfo)
        exhaustive_dependencies = decode_buildinfo(buildinfo)

        pkgname = pkgdetails["pkgname"]

        transitive_count = find_transitive_count(explicit_dependencies, exhaustive_dependencies)
        explicit_count = len(set(explicit_dependencies))

        explicit_transitive_count[pkgname] = {
            "explicit_dependencies": explicit_count,
            "transitive_dependencies": transitive_count
        }

    with open(explicit_transitive_count_file_path, "wt") as fp:
        json.dump(explicit_transitive_count, fp)


if __name__ == "__main__":
    path = "."
    out = "."
    if len(sys.argv) > 2:
        path = sys.argv[1]
        out = sys.argv[2]
    
    main(path, out)
