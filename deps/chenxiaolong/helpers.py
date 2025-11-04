from loguru import logger


_chenxiaolong_trusted_key = "chenxiaolong ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDOe6/tBnO7xZhAWXRj3ApUYgn+XZ0wnQiXM8B7tPgv4"

def verifySignature(file_data: bytes, signature_path: str) -> bool:
    trusted_key_path = "chenxiaolong_trusted_key.pub"
    with open(trusted_key_path, 'w') as f:
        f.write(_chenxiaolong_trusted_key + "\n")

    import subprocess
    verify_cmd = ["ssh-keygen", "-Y", "verify", "-f", trusted_key_path, "-I", "chenxiaolong", "-n", "file", "-s", signature_path]
    proc = subprocess.run(verify_cmd, input=file_data, capture_output=True)
    if proc.returncode != 0:
        logger.error(f"Signature verification failed: {proc.stderr.decode()}")
        raise ValueError("Signature verification failed")
        return False # never reached
    else:
        logger.info(f"Signature verification succeeded: {proc.stdout.decode()}")
        return True