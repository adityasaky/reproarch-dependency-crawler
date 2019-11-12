#!/usr/bin/env python3
import glob
import sys
import os
import tarfile
import datetime
import json


PLATFORMS = ["x86_64", "any"]
EXTENSIONS = ["xz", "zst"]


def find_tarfiles(path):
    all_files = []
    for extension in EXTENSIONS:
        all_files.extend(glob.glob(os.path.join(path,
            "*.{}".format(extension))))
    return all_files


def read_pkginfo(path):
    if not os.path.exists(path) or not os.path.isfile(path):
        raise Exception("This is not a valid path!")

    with tarfile.open(path, "r:*") as fp:
        try:
            pkginfo = fp.extractfile(".PKGINFO").read()
        except:
            return ""
    
    return pkginfo.decode()


def decode_pkginfo(pkginfo):
    result_pkg = []
    pkgname = ""
    arch = ""
    pkgver = ""
    
    for line in pkginfo.splitlines():
        if line.startswith("makedepend"):
            pkg = line.split(" = ")[1]
            result_pkg.append(pkg)
        elif line.startswith("pkgname"):
            pkgname = line.split(" = ")[1]
        elif line.startswith("arch"):
            arch = line.split(" = ")[1]
        elif line.startswith("pkgver"):
            pkgver = line.split(" = ")[1]
    
    return {"pkgname": pkgname, "pkgver": pkgver, "arch": arch}, result_pkg


def add_package_to_dict(dictionary, key, value):
    if key not in dictionary:
        dictionary[key] = [value]

    elif value not in dictionary[key]:
        dictionary[key].append(value)


def main(path=".", out="."):
    package_paths = []
    now = datetime.datetime.now()
    today = "-".join([str(now.year), str(now.month), str(now.day)])
    database_file_name = "makedepends_" + today
    packages_to_makedepends_file_name = "packages_makedepends_" + today + ".json"
    makedepends_to_packages_file_name = "makedepends_packages_" + today + ".json"

    # database_file_pkg = os.path.join(out, database_file_name + "_pkg.json")
    # database_file_pkg_ver = os.path.join(out, database_file_name + "_pkg-ver.json")
    # database_file_pkg_ver_pfm = os.path.join(out, database_file_name + "_pkg-ver-pfm.json")

    packages_to_makedepends_file_path = os.path.join(out, packages_to_makedepends_file_name)
    makedepends_to_packages_file_path = os.path.join(out, makedepends_to_packages_file_name)

    try:
        with open(packages_to_makedepends_file_path) as fp:
            packages_to_makedepends = json.load(fp)
    except Exception:
        packages_to_makedepends = {}

    try:
        with open(makedepends_to_packages_file_path) as fp:
            makedepends_to_packages = json.load(fp)
    except Exception:
        makedepends_to_packages = {}

    package_paths = find_tarfiles(path)

    for package_path in package_paths:
        pkginfo = read_pkginfo(package_path)
        pkgdetails, makedepends = decode_pkginfo(pkginfo)

        pkgname = pkgdetails["pkgname"]

        packages_to_makedepends[pkgname] = makedepends

        for makedepend in makedepends:
            add_package_to_dict(makedepends_to_packages, makedepend, pkgname)
        
    for makedepend in makedepends_to_packages:
        for consumer in makedepends_to_packages[makedepend]:
            if consumer in makedepends_to_packages:
                makedepends_to_packages[makedepend].extend(makedepends_to_packages[consumer])
                makedepends_to_packages[makedepend] = list(set(makedepends_to_packages[makedepend]))
    
    with open(packages_to_makedepends_file_path, "wt") as fp:
        json.dump(packages_to_makedepends, fp)

    with open(makedepends_to_packages_file_path, "wt") as fp:
        json.dump(makedepends_to_packages, fp)
    

if __name__ == "__main__":
    path = "."
    out = "."
    if len(sys.argv) > 2:
        path = sys.argv[1]
        out = sys.argv[2]
    
    main(path, out)
