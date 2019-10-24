#!/usr/bin/env python3
import tarfile
import os
import glob
import json
import sys
import datetime


PLATFORMS = ["x86_64", "any"]
EXTENSIONS = ["xz", "zst"]
package_paths = []


def read_buildinfo(path):
    if not os.path.exists(path) or not os.path.isfile(path):
        # XXX
        raise Exception("This is not a valid path!")

    with tarfile.open(path, "r:*") as fp:
        try:
            buildinfo = fp.extractfile(".BUILDINFO").read()
        except:
            return ""

    return buildinfo.decode()


def build_full_pkg_from_package_name(path):
    return os.path.basename(path).rsplit(".", 3)[0].lstrip("./").rsplit("-", 3)


def find_platform(pkg):
    global package_paths
    for package_path in package_paths:
        if pkg in package_path:
            return build_full_pkg_from_package_name(package_path)


def decode_buildinfo_lines(buildinfo):
    result_pkg = []
    result_pkg_ver = []
    result_pkg_ver_pfm = []

    # FIXME: what about epochs? we probably need to care about packages
    for line in buildinfo.splitlines():
        if line.startswith("installed"):
            pkg = line.split(" = ")[1]
            pkg_split = pkg.rsplit("-", 3)
            if len(pkg_split) < 4 or pkg_split[3] not in PLATFORMS:
                pkg_split = find_platform(pkg)
                if pkg_split is None:
                    continue
            name, pkgver, build, pfm = pkg_split
            result_pkg.append("{}".format(name))
            result_pkg_ver.append("{}-{}-{}".format(name, pkgver, build))
            result_pkg_ver_pfm.append("{}-{}-{}-{}".format(name, pkgver, build, pfm))

    return result_pkg, result_pkg_ver, result_pkg_ver_pfm


# XXX I opted for this ugly-looking dict update solution rather than something
# more pythonic/elegant for this first sketch. It'd make sense to use something
# smarter in the future...
def add_package_to_dict(pkgdict, package, dependent_package):
    if package not in pkgdict:
        pkgdict[package] = [dependent_package]

    elif dependent_package not in pkgdict[package]:
        pkgdict[package].append(dependent_package)


def find_tarfiles(path="."):
    all_files = []
    for extension in EXTENSIONS:
        all_files.extend(glob.glob(os.path.join(path,
            "*.{}".format(extension))))
    return all_files


def main(path=".", out="."):
    global package_paths
    now = datetime.datetime.now()
    today = "-".join([str(now.year), str(now.month), str(now.day)])
    database_file_name = "data_" + today

    database_file_pkg = os.path.join(out, database_file_name + "_pkg.json")
    database_file_pkg_ver = os.path.join(out, database_file_name + "_pkg-ver.json")
    database_file_pkg_ver_pfm = os.path.join(out, database_file_name + "_pkg-ver-pfm.json")

    try:
        with open(database_file_pkg) as fp:
            all_packages_pkg = json.load(fp)
    except Exception:
        all_packages_pkg = {}

    try:
        with open(database_file_pkg_ver) as fp:
            all_packages_pkg_ver = json.load(fp)
    except Exception:
        all_packages_pkg_ver = {}

    try:
        with open(database_file_pkg_ver_pfm) as fp:
            all_packages_pkg_ver_pfm = json.load(fp)
    except Exception:
        all_packages_pkg_ver_pfm = {}

    package_paths = find_tarfiles(path)

    for package_path in package_paths:
        buildinfo = read_buildinfo(package_path)
        thispackage = build_full_pkg_from_package_name(package_path)

        packages_pkg, packages_pkg_ver, packages_pkg_ver_pfm = \
            decode_buildinfo_lines(buildinfo)

        for package in packages_pkg:
            add_package_to_dict(all_packages_pkg, package, thispackage[0])

        for package in packages_pkg_ver:
            current_package = "-".join([thispackage[0], thispackage[1],
                thispackage[2]])
            add_package_to_dict(all_packages_pkg_ver, package, current_package)

        for package in packages_pkg_ver_pfm:
            current_package = "-".join([thispackage[0], thispackage[1],
                thispackage[2], thispackage[3]])
            add_package_to_dict(all_packages_pkg_ver_pfm, package,
                current_package)

    with open(database_file_pkg, 'wt') as fp:
        json.dump(all_packages_pkg, fp)

    with open(database_file_pkg_ver, 'wt') as fp:
        json.dump(all_packages_pkg_ver, fp)

    with open(database_file_pkg_ver_pfm, 'wt') as fp:
        json.dump(all_packages_pkg_ver_pfm, fp)

    with open("package-dependencies.txt", "wt") as fp:
        for line in all_packages_pkg_ver_pfm.keys():
            fp.write("{}\n".format(line))


# FIXME: should populate a dictionary for fast lookup of all the package names,
# and versions
if __name__ == "__main__":
    path = "."
    if len(sys.argv) > 2:
        path = sys.argv[1]
        out = sys.argv[2]

    main(path, out)
