#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "${script_dir}/.." && pwd)"
version="5.0.0~rc1"
package_name="efcalc-pro_${version}_all.deb"
output_dir="${project_root}/dist"
stage_dir="$(mktemp -d -t efcalc-pro-package.XXXXXXXX)"
chmod 0755 "${stage_dir}"

cleanup() {
    rm -rf -- "${stage_dir}"
}
trap cleanup EXIT

install -d \
    "${stage_dir}/DEBIAN" \
    "${stage_dir}/usr/bin" \
    "${stage_dir}/usr/share/applications" \
    "${stage_dir}/usr/share/doc/efcalc-pro/examples" \
    "${stage_dir}/usr/share/efcalc-pro" \
    "${stage_dir}/usr/share/icons/hicolor/scalable/apps" \
    "${stage_dir}/usr/share/metainfo" \
    "${output_dir}"

python3 -m py_compile \
    "${project_root}/main.py" \
    "${project_root}/efcalc.py" \
    "${project_root}/efcalc_engine.py" \
    "${project_root}/efcalc_program.py" \
    "${project_root}/efcalc_gui.py" \
    "${project_root}/efcalc_settings.py"

install -m 0644 "${project_root}/packaging/control" "${stage_dir}/DEBIAN/control"
install -m 0755 "${project_root}/packaging/efcalc-pro" "${stage_dir}/usr/bin/efcalc-pro"
install -m 0644 "${project_root}/packaging/efcalc-pro.desktop" \
    "${stage_dir}/usr/share/applications/efcalc-pro.desktop"
install -m 0644 "${project_root}/packaging/io.github.drericflores.efcalc.metainfo.xml" \
    "${stage_dir}/usr/share/metainfo/io.github.drericflores.efcalc.metainfo.xml"
install -m 0644 "${project_root}/assets/efcalc-pro.svg" \
    "${stage_dir}/usr/share/icons/hicolor/scalable/apps/efcalc-pro.svg"
install -m 0644 "${project_root}/packaging/copyright" \
    "${stage_dir}/usr/share/doc/efcalc-pro/copyright"
install -m 0644 "${project_root}/README.md" \
    "${stage_dir}/usr/share/doc/efcalc-pro/README.md"

for source_file in \
    main.py efcalc.py efcalc_engine.py efcalc_program.py efcalc_gui.py efcalc_settings.py
do
    install -m 0644 "${project_root}/${source_file}" \
        "${stage_dir}/usr/share/efcalc-pro/${source_file}"
done

for example_file in "${project_root}"/examples/*.efp
do
    install -m 0644 "${example_file}" \
        "${stage_dir}/usr/share/doc/efcalc-pro/examples/$(basename -- "${example_file}")"
done

dpkg-deb --build --root-owner-group "${stage_dir}" "${output_dir}/${package_name}"
dpkg-deb --info "${output_dir}/${package_name}"
dpkg-deb --contents "${output_dir}/${package_name}"

printf 'Built %s\n' "${output_dir}/${package_name}"
