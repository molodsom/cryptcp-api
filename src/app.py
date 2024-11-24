from base64 import b64encode
import os
import re
from subprocess import CalledProcessError
from uuid import uuid4
import zipfile

from flask import Flask, request

from src import cmds

app = Flask(__name__)
UPLOAD_FOLDER = '/uploads'
KEYS_FOLDER = '/var/opt/cprocsp/keys/root'


def set_license(license_key: str = None) -> str:
    if license_key:
        try:
            cmds.set_license_key(license_key)
            return f'License key ({license_key}) successfully set.'
        except CalledProcessError as e:
            return f'Failed to set license key: {e}.'
    else:
        return f'No license key found.'


@app.route('/license', methods=['GET'])
def get_license():
    try:
        result = cmds.get_license_info()
        lines = result.strip().split('\n')
        parsed_license = {'key': None, 'expires': None, 'type': None}

        for i, line in enumerate(lines):
            if line.startswith('License validity:'):
                if i + 1 < len(lines):
                    parsed_license['key'] = lines[i + 1].strip()
            elif line.startswith('Expires:'):
                parsed_license['expires'] = line.split(': ', 1)[1].strip() if ': ' in line else None
            elif line.startswith('License type:'):
                parsed_license['type'] = line.split(': ', 1)[1].strip() if ': ' in line else None

        if not all(parsed_license.values()):
            return {
                'success': False,
                'message': 'Incomplete license data retrieved.',
                'license_info': parsed_license
            }, 500

        return {'success': True, 'license_info': parsed_license}, 200
    except CalledProcessError as e:
        return {'success': False, 'message': 'Failed to retrieve license information', 'error': e.output}, 500


@app.route('/keys', methods=['GET'])
def get_keys():
    try:
        result = cmds.get_keys()
        keys = []

        for block in result.split('-------'):
            subject = None
            thumbprint = None
            expire_at = None

            subject_match = re.search(r'Subject\s+:\s+(.+)', block)
            thumbprint_match = re.search(r'SHA1 Thumbprint\s+:\s+([a-fA-F0-9]+)', block)
            expire_at_match = re.search(r'Not valid after\s+:\s+([\d/]+\s[\d:]+\s\w+)', block)

            if subject_match:
                subject = subject_match.group(1).strip()
            if thumbprint_match:
                thumbprint = thumbprint_match.group(1).strip()
            if expire_at_match:
                expire_at = expire_at_match.group(1).strip()

            if subject and thumbprint and expire_at:
                keys.append({
                    'subject': subject,
                    'thumbprint': thumbprint,
                    'expire_at': expire_at
                })

        return {'success': True, 'certificates': keys}, 200
    except CalledProcessError as e:
        return {'success': False, 'message': 'Failed to retrieve certificates', 'error': e.output}, 500


@app.route('/sign', methods=['POST'])
def sign_document():
    thumb = request.form.get('thumb', '').upper()
    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, uuid4().hex)
    file.save(file_path)

    output_path = file_path + '.sgn'

    try:
        cmds.document_sign(file_path, output_path, thumb)
    except CalledProcessError as e:
        return {'success': False, 'message': e.output}, 500

    try:
        with open(file_path, 'rb') as file:
            content = b64encode(file.read()).decode('utf-8')
        with open(output_path, 'rb') as file:
            signature = b64encode(file.read()).decode('utf-8')
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

    os.remove(file_path)
    os.remove(output_path)

    return {
        'success': True,
        'attachment': {
            'Файл': {'Имя': request.files['file'].filename, 'ДвоичныеДанные': content},
            'Подпись': {'Файл': {'ДвоичныеДанные': signature}},
        }
    }


@app.route('/upload-container', methods=['POST'])
def upload_container():
    if 'file' not in request.files:
        return {'success': False, 'message': 'No file part'}, 400

    file = request.files['file']
    if file.filename == '':
        return {'success': False, 'error': 'No selected file'}, 400

    if file and file.filename.endswith('.zip'):
        zip_path = os.path.join(UPLOAD_FOLDER, uuid4().hex + '.zip')
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            container_dir = None
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith('.000/') and file_info.is_dir():
                    container_dir = file_info.filename[:-1]
                    for file_info_2 in zip_ref.infolist():
                        if file_info_2.filename.startswith(container_dir):
                            zip_ref.extract(file_info_2, KEYS_FOLDER)
                    break
        os.remove(zip_path)

        if container_dir:
            try:
                container_name = cmds.get_container_name(container_dir)
                cert_data = cmds.install_from_container(container_name)
                inn = ''.join(re.findall(r'Subject[^\n]+ИНН ЮЛ=(\d+)', cert_data))
                thumb = ''.join(re.findall(r'SHA1 Thumbprint\s+:\s+([a-fA-F0-9]+)', cert_data)).upper()
                return {
                    'success': True,
                    'message': 'File uploaded and unpacked successfully',
                    'inn': inn,
                    'thumb': thumb,
                }, 200
            except CalledProcessError as e:
                return {'success': False, 'message': e.output}, 500
        else:
            return {'success': False, 'message': 'No container found'}, 400
    return {'success': False, 'message': 'Unsupported file type'}, 400


if __name__ == '__main__':
    set_license(os.getenv('LICENSE_KEY'))
    app.run(host='0.0.0.0', port=80)
