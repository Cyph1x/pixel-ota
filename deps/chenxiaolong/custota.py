from loguru import logger
import requests
import os
from tqdm.auto import tqdm
from dataclasses import dataclass
from .helpers import verifySignature

@dataclass
class CustotaRelease:
    tag_name: str
    release_name: str
    prerelease: bool
    debug: bool
    filename: str
    url: str

    def download(self, download_dir: str, filename: str = None, overwrite: bool = False) -> str:
        if filename is None:
            filename = self.filename

        os.makedirs(download_dir, exist_ok=True)
        out_path = os.path.join(download_dir, filename)

        if not overwrite and os.path.exists(out_path):
            logger.warning(f"File {out_path} already exists, skipping download.")
            return out_path

        logger.info(f"Downloading Custota {self.tag_name} to {out_path}")
        temp_path = out_path + ".part"
        with requests.get(self.url, stream=True) as r:
            total_size = int(r.headers.get('content-length', 0))
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                with open(temp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            assert total_size == os.path.getsize(temp_path), f"Downloaded file size {os.path.getsize(temp_path)} does not match expected size {total_size}"

        signature_path = out_path + ".sig"
        logger.info(f"Downloading Custota signature to {signature_path}")
        with requests.get(self.url + ".sig", stream=True) as r:
            total_size = int(r.headers.get('content-length', 0))
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=self.filename + ".sig") as pbar:
                with open(signature_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            assert total_size == os.path.getsize(signature_path), f"Downloaded signature file size {os.path.getsize(signature_path)} does not match expected size {total_size}"

        # verify the signature
        file_data = open(temp_path, 'rb').read()
        try:
            verifySignature(file_data, signature_path, logger=logger)
        except ValueError as e:
            os.remove(temp_path)
            os.remove(signature_path)
            raise

        os.remove(signature_path)
        os.rename(temp_path, out_path)

        return out_path

def fetchCustotaReleases() -> list[CustotaRelease]:
    with requests.Session() as s:
        headers = {
            'X-GitHub-Api-Version': '2022-11-28',
            'Accept': 'application/vnd.github+json',
        }

        res = s.get("https://api.github.com/repos/chenxiaolong/Custota/releases", headers=headers)

    assert res.status_code == 200, f"Failed to fetch releases page: {res.status_code}"

    releases = res.json()
    logger.info(f"Found {len(releases)} releases")
    available_releases = []
    for release in releases:
        tag_name = release['tag_name']
        release_name = release['name']
        prerelease = release['prerelease']
        for asset in release['assets']:
            filename = asset['name']

            url = asset['browser_download_url']
            if not filename.endswith('.zip'):
                logger.debug(f"Skipping non-zip asset: {filename}")
                continue

            # check if the asset is a debug build
            debug = 'debug' in filename.lower() or 'dbg' in filename.lower()

            release_info = CustotaRelease(
                tag_name=tag_name,
                release_name=release_name,
                prerelease=prerelease,
                debug=debug,
                filename=filename,
                url=url
            )
            available_releases.append(release_info)
            logger.info(f"Found Custota release: {release_info}")

    return available_releases