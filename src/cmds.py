from subprocess import check_output


def execute(*args) -> str:
    return check_output(list(args), text=True)

def set_license_key(license_key: str) -> str:
    return execute('cpconfig', '-license', '-set', license_key)

def get_license_info() -> str:
    return execute('cpconfig', '-license', '-view')

def get_keys() -> str:
    return execute('certmgr', '-list')

def document_sign(file: str, directory: str, thumb: str) -> str:
    return execute('cryptcp -nochain -norev -cert -der -signf', file, '-dir', directory, '-thumb', thumb)

def get_container_name(directory: str) -> str:
    return execute('csptestf -keys -enum -verifyc -fqcn -un | grep', directory).split('|')[0]

def install_from_container(container_name: str) -> str:
    return execute('certmgr', '-install', '-cont', container_name)
