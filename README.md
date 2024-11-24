# cryptcp-api
This project provides a containerized service for signing documents using cryptcp.
The service is intended for use in secure, access-restricted infrastructures.

## Prerequisites
- Docker installed on the host machine.

## Environment Variables
- **`LICENSE_KEY`**: (Optional) License key for cryptcp. If omitted, a 3-month trial is active by default.

## Usage
1. **Build the Container**:
   ```bash
   docker build -t cryptcp-api .
   ```

2. **Run the Container**:
   ```bash
   docker run -d -p 80:80 \
       -v ./cprocsp:/var/opt/cprocsp \
       -e LICENSE_KEY=your_license_key \
       cryptcp-api
   ```

3. **Endpoints**:

   - **`GET /license`**: Retrieve current license information.
   - **`GET /keys`**: List installed certificates and details.
   - **`POST /sign`**: Sign a document with the specified certificate.
     - Form data: `thumb` (certificate thumbprint), `file` (file to sign).
   - **`POST /upload-container`**: Upload and install keys/certificates from a `.zip` container.

## Security Notice

> This service is intended for use in secure, access-restricted infrastructures only. It should not be exposed to the public internet. Ensure that the environment and files are adequately secured to prevent unauthorized access.

## Example
- **Sign a Document**:
  ```bash
  curl -X POST -F "thumb=<CERT_THUMBPRINT>" -F "file=@path/to/document.pdf" http://<host>:<port>/sign
  ```
- **Upload a Container**:
  ```bash
  curl -X POST -F "file=@path/to/container.zip" http://<host>:<port>/upload-container
  ```
- **Expected `.zip` file structure:**
    ```text
    container.zip
    ├── 12345678.000/
    │   ├── header.key
    │   ├── masks.key
    │   ├── name.key
    │   ├── primary.key
    ```

## License
This project uses cryptcp, which requires a valid license key or trial mode.
