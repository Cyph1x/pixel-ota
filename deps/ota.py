from loguru import logger
import requests
import re
import os
from tqdm.auto import tqdm
from dataclasses import dataclass

@dataclass
class OTAInfo:
    android_version: str
    build_id: str
    build_branch: str
    build_date: str
    build_number: str
    build_variant: str | None
    carrier: str | None
    device: str
    url: str
    checksum: str

    @property
    def filename(self) -> str:
        return f"{self.device}-ota-{self.build_id}.zip"

    def download(self, download_dir: str, filename: str = None, overwrite: bool = False) -> str:
        if filename is None:
            filename = self.filename

        os.makedirs(download_dir, exist_ok=True)
        out_path = os.path.join(download_dir, filename)

        if not overwrite and os.path.exists(out_path):
            logger.warning(f"File {out_path} already exists, skipping download.")
        else:
            logger.info(f"Downloading OTA {self.android_version}, {self.build_id} for {self.device} to {out_path}")
            temp_path = out_path + ".part"
            with requests.get(self.url, stream=True) as r:
                total_size = int(r.headers.get('content-length', 0))
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    with open(temp_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))
                assert total_size == os.path.getsize(temp_path), f"Downloaded file size {os.path.getsize(temp_path)} does not match expected size {total_size}"

            os.rename(temp_path, out_path)
        
        # verify checksum
        import hashlib
        sha256 = hashlib.sha256()
        with open(out_path, 'rb') as f:
            with tqdm(total=os.path.getsize(out_path), unit='B', unit_scale=True, desc="Verifying checksum") as pbar:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
                    pbar.update(len(chunk))
        calculated_checksum = sha256.hexdigest()
        if calculated_checksum != self.checksum:
            logger.error(f"Checksum mismatch for {out_path}: expected {self.checksum}, got {calculated_checksum}")
            os.remove(out_path)
            raise ValueError(f"Checksum mismatch for {out_path}: expected {self.checksum}, got {calculated_checksum}")
        else:
            logger.info(f"Checksum verified for {out_path}")
        return out_path

def fetchAllOTA() -> list[OTAInfo]:
    with requests.Session() as s:
        cookies = {
            "devsite_wall_acks": "nexus-ota-tos",
        }

        s.cookies.update(cookies)
        res = s.get("https://developers.google.com/android/ota")

    assert res.status_code == 200, f"Failed to fetch OTA page: {res.status_code}"

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(res.text, 'html.parser')

    # find all table rows
    rows = soup.find_all('tr')
    logger.info(f"Found {len(rows)} rows in the OTA table")

    available_otas = []
    for row in rows:
        # There should be 3 columns: Version, Download, and checksum
        cols = row.find_all('td')

        if len(cols) != 3:
            logger.warning(f"Skipping row with {len(cols)} columns")
            continue
        version_col, download_col, checksum_col = cols

        # extract the version data
        version_text = version_col.get_text(strip=True)
        match = re.match(r'^(\d+\.\d+\.\d+)\s+\(([^,]+),\s+([^,]+)(?:,\s+([^)]+))?\)$', version_text)
        if not match:
            logger.warning(f"Skipping row with unrecognized version format: {version_text}")
            continue
        android_ver, build_id, security_level, carrier  = match.groups()

        split_build_id = build_id.split('.')
        try:
            build_branch_code, build_date, build_number = split_build_id[:3]
        except Exception as e:
            logger.error(f"Error parsing build ID '{build_id}' (most likely due to old version format): {e}")
            continue
        build_variant = split_build_id[3] if len(split_build_id) > 3 else None

        # get the device name from the row using the build_id
        row_id = row.get('id')
        # the format is <device>-<build_id>
        device = row_id.lower().replace(f"{build_id.lower()}", "")

        logger.info(f"Parsed version: Android {android_ver}, Build {build_id}, Security {security_level}, Carrier {carrier}")
        logger.debug(f"Device: {device}")
        logger.debug(f"Build details: Branch {build_branch_code}, Date {build_date}, Number {build_number}, Variant {build_variant}")


        # extract the download link
        a_tag = download_col.find('a', href=True)
        if not a_tag:
            logger.warning("Skipping row with no download link")
            continue
        dl_link = a_tag['href']
        logger.info(f"Found download link: {dl_link}")

        checksum_text = checksum_col.get_text(strip=True)
        logger.info(f"Checksum: {checksum_text}")
        ota_info = OTAInfo(
            android_version=android_ver,
            build_id=build_id,
            build_branch=build_branch_code,
            build_date=build_date,
            build_number=build_number,
            build_variant=build_variant,
            carrier=carrier,
            device=device,
            url=dl_link,
            checksum=checksum_text
        )
        available_otas.append(ota_info)

    return available_otas