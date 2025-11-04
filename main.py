from dataclasses import dataclass
import logging
import zipfile
import sys
import pandas as pd
import numpy as np
import os
import shutil
from tqdm.auto import tqdm
import zipfile
import subprocess
from deps.chenxiaolong.avbroot import fetchAvbrootReleases, AvbrootRelease
from deps.chenxiaolong.afsr import fetchAfsrReleases, AfsrRelease
from deps.chenxiaolong.custota import fetchCustotaReleases, CustotaRelease
from deps.magisk import fetchMagiskReleases, MagiskRelease
from deps.ota import fetchAllOTA, OTAInfo
from loguru import logger

logger.debug("Debug log test")
logger.info("Info log test")
logger.warning("Warning log test")
logger.error("Error log test")
logger.critical("Critical log test")

@dataclass
class Dependencies:
    selected_ota: OTAInfo
    ota_path: str
    selected_magisk: MagiskRelease
    magisk_path: str
    selected_avbroot: AvbrootRelease
    avbroot_path: str
    selected_afsr: AfsrRelease
    afsr_path: str
    selected_custota: CustotaRelease
    custota_path: str

def fetchDependencies(
    download_dir: str = "downloads",
    ota_android_version: str = None,
    ota_build_id: str = None,
    ota_build_branch: str = None,
    ota_build_date: str = None,
    ota_build_number: str = None,
    ota_build_variant: str = None,
    ota_carrier: str = None,
    ota_device: str = None,
    ota_checksum: str = None,
    magisk_version: str = None,
    magisk_debug: bool = False,
    magisk_prerelease: bool = False,
    avbroot_version: str = None,
    avbroot_debug: bool = False,
    avbroot_prerelease: bool = False,
    afsr_version: str = None,
    afsr_debug: bool = False,
    afsr_prerelease: bool = False,
    custota_version: str = None,
    custota_debug: bool = False,
    custota_prerelease: bool = False,
) -> Dependencies:
    
    os.makedirs(download_dir, exist_ok=True)

    # download ota
    if True:
        otas = fetchAllOTA()
        ota_df = pd.DataFrame(otas)
        ota_df['obj'] = otas
        ota_df.fillna(value="", inplace=True)
        logger.info(f"Fetched {len(otas)} OTA releases")

        filtered_releases_mask = np.ones(len(ota_df), dtype=bool)
        if ota_android_version is not None:
            filtered_releases_mask &= ota_df['android_version'] == ota_android_version
        if ota_build_id is not None:
            filtered_releases_mask &= ota_df['build_id'] == ota_build_id
        if ota_build_branch is not None:
            filtered_releases_mask &= ota_df['build_branch'] == ota_build_branch
        if ota_build_date is not None:
            filtered_releases_mask &= ota_df['build_date'] == ota_build_date
        if ota_build_number is not None:
            filtered_releases_mask &= ota_df['build_number'] == ota_build_number
        if ota_build_variant is not None:
            filtered_releases_mask &= ota_df['build_variant'] == ota_build_variant
        if ota_carrier is not None:
            filtered_releases_mask &= ota_df['carrier'] == ota_carrier
        if ota_device is not None:
            filtered_releases_mask &= ota_df['device'] == ota_device
        if ota_checksum is not None:
            filtered_releases_mask &= ota_df['checksum'] == ota_checksum
        filtered_releases = ota_df[filtered_releases_mask].copy()
        filtered_releases.sort_values(by=['build_date', 'build_number', 'build_variant'], ascending=[False, False, False], inplace=True)
        filtered_releases

        assert len(filtered_releases) > 0, "No OTA releases found for the specified criteria"
        
        logger.info(f"{len(filtered_releases)} OTA releases found for the specified criteria, selecting the latest one")

        selected_ota = filtered_releases.iloc[0].obj
        ota_path = selected_ota.download(download_dir=download_dir, overwrite=False)
        logger.info(f"Selected OTA: {selected_ota.android_version}, {selected_ota.build_id}, {selected_ota.device}, {selected_ota.url}")

    # download magisk
    if True:
        magisk_releases = fetchMagiskReleases()
        magisk_df = pd.DataFrame(magisk_releases)
        magisk_df['obj'] = magisk_releases
        magisk_df.fillna(value="", inplace=True)
        logger.info(f"Fetched {len(magisk_releases)} Magisk releases")

        filtered_magisk_mask = np.ones(len(magisk_df), dtype=bool)
        if magisk_version is not None:
            filtered_magisk_mask &= (magisk_df['tag_name'] == magisk_version) | (magisk_df['tag_name'] == f"v{magisk_version}")
        if magisk_debug is not None:
            filtered_magisk_mask &= magisk_df['debug'] == magisk_debug
        if magisk_prerelease is not None:
            filtered_magisk_mask &= magisk_df['prerelease'] == magisk_prerelease
        
        filtered_magisk_releases = magisk_df[filtered_magisk_mask]

        assert len(filtered_magisk_releases) > 0, f"No matching Magisk releases found for criteria: version {magisk_version}, debug {magisk_debug}, prerelease {magisk_prerelease}"
        logger.info(f"{len(filtered_magisk_releases)} Magisk releases found for the specified criteria, selecting the first one (should be the latest)")

        selected_magisk = filtered_magisk_releases.iloc[0].obj
        magisk_path = selected_magisk.download(download_dir=download_dir, overwrite=False)
        logger.info(f"Selected Magisk: {selected_magisk.tag_name}, {selected_magisk.url}")

    # download avbroot
    if True:
        avbroot_releases = fetchAvbrootReleases()
        avbroot_df = pd.DataFrame(avbroot_releases)
        avbroot_df['obj'] = avbroot_releases
        avbroot_df.fillna(value="", inplace=True)
        logger.info(f"Fetched {len(avbroot_releases)} Avbroot releases")

        filtered_avbroot_mask = np.ones(len(avbroot_df), dtype=bool)
        if avbroot_version is not None:
            filtered_avbroot_mask &= (avbroot_df['tag_name'] == avbroot_version) | (avbroot_df['tag_name'] == f"v{avbroot_version}")
        if avbroot_debug is not None:
            filtered_avbroot_mask &= avbroot_df['debug'] == avbroot_debug
        if avbroot_prerelease is not None:
            filtered_avbroot_mask &= avbroot_df['prerelease'] == avbroot_prerelease

        filtered_avbroot_mask &= avbroot_df['filename'].str.contains('linux', case=False, na=False)
        filtered_avbroot_mask &= avbroot_df['filename'].str.contains('x86_64', case=False, na=False)

        filtered_avbroot = avbroot_df[filtered_avbroot_mask]

        assert len(filtered_avbroot) > 0, f"No matching avbroot releases found for criteria: version {avbroot_version}, debug {avbroot_debug}, prerelease {avbroot_prerelease}"

        logger.info(f"{len(filtered_avbroot)} Avbroot releases found for the specified criteria, selecting the first one (should be the latest)")

        selected_avbroot = filtered_avbroot.iloc[0].obj
        download_dir = os.path.join(os.getcwd(), 'downloads')
        avbroot_path = selected_avbroot.download(download_dir, overwrite=False)
        logger.info(f"Selected Avbroot: {selected_avbroot.tag_name}, {selected_avbroot.url}")

        # So we can run avbroot, it needs to be decompressed and made executable
        # decompress avbroot so that it can be used
        with zipfile.ZipFile(avbroot_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(download_dir, "avbroot"))

        assert os.path.exists(os.path.join(download_dir, "avbroot")) and os.path.isdir(os.path.join(download_dir, "avbroot"))
        assert os.path.exists(os.path.join(download_dir, "avbroot", "avbroot")) and os.path.isfile(os.path.join(download_dir, "avbroot", "avbroot"))
        avbroot_path = os.path.join(download_dir, "avbroot", "avbroot")

        import subprocess
        if not os.access(avbroot_path, os.X_OK):
            # make it executable
            subprocess.run(["chmod", "+x", avbroot_path], check=True)
        if not os.access(avbroot_path, os.X_OK):
            raise Exception(f"avbroot is not executable: {avbroot_path}")
        
    # download custota
    if True:
        custota_releases = fetchCustotaReleases()
        custota_df = pd.DataFrame(custota_releases)
        custota_df['obj'] = custota_releases
        custota_df.fillna(value="", inplace=True)
        logger.info(f"Fetched {len(custota_releases)} Custota releases")

        filtered_custota_mask = np.ones(len(custota_df), dtype=bool)
        if custota_version is not None:
            filtered_custota_mask &= (custota_df['tag_name'] == custota_version) | (custota_df['tag_name'] == f"v{custota_version}")
        if custota_debug is not None:
            filtered_custota_mask &= custota_df['debug'] == custota_debug
        if custota_prerelease is not None:
            filtered_custota_mask &= custota_df['prerelease'] == custota_prerelease

        filtered_custota_mask &= custota_df['filename'].str.contains('linux', case=False, na=False)
        filtered_custota_mask &= custota_df['filename'].str.contains('x86_64', case=False, na=False)

        filtered_custota = custota_df[filtered_custota_mask]

        assert len(filtered_custota) > 0, f"No matching custota releases found for criteria: version {custota_version}, debug {custota_debug}, prerelease {custota_prerelease}"

        logger.info(f"{len(filtered_custota)} Custota releases found for the specified criteria, selecting the first one (should be the latest)")

        selected_custota = filtered_custota.iloc[0].obj
        download_dir = os.path.join(os.getcwd(), 'downloads')
        custota_path = selected_custota.download(download_dir, overwrite=False)
        logger.info(f"Selected Custota: {selected_custota.tag_name}, {selected_custota.url}")

        # So we can run custota, it needs to be decompressed and made executable
        # decompress custota so that it can be used
        with zipfile.ZipFile(custota_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(download_dir, "custota"))

        assert os.path.exists(os.path.join(download_dir, "custota")) and os.path.isdir(os.path.join(download_dir, "custota"))
        assert os.path.exists(os.path.join(download_dir, "custota", "custota-tool")) and os.path.isfile(os.path.join(download_dir, "custota", "custota-tool"))
        custota_path = os.path.join(download_dir, "custota", "custota-tool")

        import subprocess
        if not os.access(custota_path, os.X_OK):
            # make it executable
            subprocess.run(["chmod", "+x", custota_path], check=True)
        if not os.access(custota_path, os.X_OK):
            raise Exception(f"custota is not executable: {custota_path}")

    # download afsr
    if True:
        afsr_releases = fetchAfsrReleases()
        afsr_df = pd.DataFrame(afsr_releases)
        afsr_df['obj'] = afsr_releases
        afsr_df.fillna(value="", inplace=True)
        logger.info(f"Fetched {len(afsr_releases)} Afsr releases")

        filtered_afsr_mask = np.ones(len(afsr_df), dtype=bool)
        if afsr_version is not None:
            filtered_afsr_mask &= (afsr_df['tag_name'] == afsr_version) | (afsr_df['tag_name'] == f"v{afsr_version}")
        if afsr_debug is not None:
            filtered_afsr_mask &= afsr_df['debug'] == afsr_debug
        if afsr_prerelease is not None:
            filtered_afsr_mask &= afsr_df['prerelease'] == afsr_prerelease

        filtered_afsr_mask &= afsr_df['filename'].str.contains('linux', case=False, na=False)
        filtered_afsr_mask &= afsr_df['filename'].str.contains('x86_64', case=False, na=False)
        filtered_afsr = afsr_df[filtered_afsr_mask]

        assert len(filtered_afsr) > 0, f"No matching afsr releases found for criteria: version {afsr_version}, debug {afsr_debug}, prerelease {afsr_prerelease}"

        logger.info(f"{len(filtered_afsr)} Afsr releases found for the specified criteria, selecting the first one (should be the latest)")

        selected_afsr = filtered_afsr.iloc[0].obj
        download_dir = os.path.join(os.getcwd(), 'downloads')
        afsr_path = selected_afsr.download(download_dir, overwrite=False)
        logger.info(f"Selected Afsr: {selected_afsr.tag_name}, {selected_afsr.url}")

        # So we can run afsr, it needs to be decompressed and made executable
        # decompress afsr so that it can be used
        with zipfile.ZipFile(afsr_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(download_dir, "afsr"))

        assert os.path.exists(os.path.join(download_dir, "afsr")) and os.path.isdir(os.path.join(download_dir, "afsr"))
        assert os.path.exists(os.path.join(download_dir, "afsr", "afsr")) and os.path.isfile(os.path.join(download_dir, "afsr", "afsr"))
        afsr_path = os.path.join(download_dir, "afsr", "afsr")

        import subprocess
        if not os.access(afsr_path, os.X_OK):
            # make it executable
            subprocess.run(["chmod", "+x", afsr_path], check=True)
        if not os.access(afsr_path, os.X_OK):
            raise Exception(f"afsr is not executable: {afsr_path}")

    logger.info("All dependencies downloaded successfully")
    logger.info(f"OTA path: {ota_path}")
    logger.info(f"Magisk path: {magisk_path}")
    logger.info(f"Avbroot path: {avbroot_path}")
    logger.info(f"Afsr path: {afsr_path}")
    logger.info(f"Custota path: {custota_path}")

    return Dependencies(
        selected_ota=selected_ota,
        ota_path=ota_path,
        selected_magisk=selected_magisk,
        magisk_path=magisk_path,
        selected_avbroot=selected_avbroot,
        avbroot_path=avbroot_path,
        selected_afsr=selected_afsr,
        afsr_path=afsr_path,
        selected_custota=selected_custota,
        custota_path=custota_path
    )


if __name__ == "__main__":
    KEY_AVB = "keys/avb.key"
    PASSPHRASE_AVB = os.getenv("PASSPHRASE_AVB")
    assert PASSPHRASE_AVB is not None, "PASSPHRASE_AVB environment variable is not set"
    KEY_OTA = "keys/ota.key"
    PASSPHRASE_OTA = os.getenv("PASSPHRASE_OTA")
    assert PASSPHRASE_OTA is not None, "PASSPHRASE_OTA environment variable is not set"
    CERT_OTA = "keys/ota.crt"
    AVB_PK = "keys/avb_pkmd.bin"

    extract_patched_ota = True
    enable_magisk = True

    dependencies = fetchDependencies(
        # ota_android_version="15.0.0",
        ota_device="lynx", # Pixel 7a
        ota_carrier="", # global
        magisk_version="29.0",
        avbroot_version="3.22.0",
        afsr_version="1.0.3",
        custota_version="5.17",

    )

    patched_dir = "patched"
    os.makedirs(patched_dir, exist_ok=True)

    os.environ["PASSPHRASE_AVB"] = PASSPHRASE_AVB
    os.environ["PASSPHRASE_OTA"] = PASSPHRASE_OTA
    command = [
        dependencies.avbroot_path,
        "ota",
        "patch",
        "--input", dependencies.ota_path,
        "--key-avb", KEY_AVB,
        "--pass-avb-env-var", "PASSPHRASE_AVB",
        "--key-ota", KEY_OTA,
        "--pass-ota-env-var", "PASSPHRASE_OTA",
        "--cert-ota", CERT_OTA,
        ]
    
    if enable_magisk:
        from deps.magisk import preinit_device_map
        preinit_partition = preinit_device_map.get(dependencies.selected_ota.device)
        assert preinit_partition is not None, f"Device {dependencies.selected_ota.device} is not supported for Magisk preinit"
        command.extend([
            "--magisk", dependencies.magisk_path,
            "--magisk-preinit-device", preinit_partition
        ])
        logger.info(f"Magisk integration enabled! device {dependencies.selected_ota.device} preinit partition: {preinit_partition}")
    else:
        logger.info("Magisk integration is disabled")
        command.extend([
            "--rootless"
        ])

    output_filename = f"{os.path.splitext(os.path.basename(dependencies.ota_path))[0]}"

    if enable_magisk:
        output_filename += f"-magisk-{dependencies.selected_magisk.tag_name}.zip"
    else:
        output_filename += f"-rootless.zip"
    

    output_path = os.path.join(patched_dir, f"{output_filename}")

    command.extend([
        "--output", output_path
    ])

    ### DEBUG
    # command = ["python3", "-c", "import os; print(os.environ)"]

    logger.info(f"Running command: {' '.join(command)}")
    subprocess.run(command, check=True)
    shutil.copyfile(AVB_PK, os.path.join(patched_dir, "avb_pkmd.bin"))

    logger.info(f"Patched OTA created at {output_path}")

    if extract_patched_ota:

        extracted_dir = os.path.join(patched_dir, "extracted")
        command = [
            dependencies.avbroot_path,
            "ota",
            "extract",
            "--input", output_path,
            "--directory", extracted_dir,
            "--fastboot",
            "--all"
        ]

        logger.info(f"Extracting patched OTA with command: {' '.join(command)}")
        subprocess.run(command, check=True)
        logger.info(f"Patched OTA extracted to {extracted_dir}")

        # the commands needed to install the extracted files via fastboot
        logger.info(f"""To install the extracted files via fastboot, use the following commands:
export ANDROID_PRODUCT_OUT={extracted_dir}
fastboot flashall --skip-reboot
fastboot reboot-bootloader
fastboot erase avb_custom_key
fastboot flash avb_custom_key {os.path.join(patched_dir, 'avb_pkmd.bin')}
fastboot flashing lock
""")

        logger.info("Since I didn't want to add modules to the ota updates, please install the modules manually")
    

    # make an ota
    ota_dir = "ota"
    os.makedirs(ota_dir, exist_ok=True)
    # move the patched ota to ota directory
    ota_path = os.path.join(ota_dir, os.path.basename(output_path))
    shutil.copyfile(output_path, ota_path)

    # prepare custota signature
    command = [
        dependencies.custota_path,
        "gen-csig",
        "--input", ota_path,
        "--key", KEY_OTA,
        "--cert", CERT_OTA,
        "--passphrase-env-var", "PASSPHRASE_OTA",
    ]

    logger.info(f"Generating Custota signature with command: {' '.join(command)}")
    subprocess.run(command, check=True)
    logger.info(f"Custota signature generated at {output_path}.csig")

    # making update info
    command = [
        dependencies.custota_path,
        "gen-update-info",
        "--file", os.path.join(ota_dir, f"{dependencies.selected_ota.device}.json"),
        "--location", ota_path,
        # "--csig-location", ota_path + ".csig",
    ]
    logger.info(f"Generating Custota update info with command: {' '.join(command)}")
    subprocess.run(command, check=True)
    logger.info(f"Custota update info generated at {os.path.join(ota_dir, f'{dependencies.selected_ota.device}.json')}")
    with open(os.path.join(ota_dir, f"release_info"), 'w') as f:
        f.write(f"device={dependencies.selected_ota.device}\n")
        f.write(f"android_version={dependencies.selected_ota.android_version}\n")
        f.write(f"build_id={dependencies.selected_ota.build_id}\n")
        f.write(f"build_branch={dependencies.selected_ota.build_branch}\n")
        f.write(f"build_date={dependencies.selected_ota.build_date}\n")
        f.write(f"build_number={dependencies.selected_ota.build_number}\n")
        f.write(f"build_variant={dependencies.selected_ota.build_variant}\n")
        f.write(f"ota={os.path.basename(ota_path)}\n")
        f.write(f"magisk_enabled={enable_magisk}\n")
    logger.info(f"Release info written to {os.path.join(ota_dir, 'release_info')}")

