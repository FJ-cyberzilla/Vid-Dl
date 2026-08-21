# Infrastructure Operational Best Practices: Firebase DRM Adapter

This document outlines the operational and security requirements for the `RemoteFirebaseDRMService`.

## 1. Authentication
- The adapter injects `Authorization: Bearer <ACCESS_TOKEN>`.
- **Requirement**: The destination Firebase Function MUST validate this token against Firebase Auth to ensure unauthorized requests are rejected immediately.

## 2. Network & Timeouts
- The system defaults to a 30s timeout (`settings.TIMEOUT`).
- **Requirement**: For heavy cryptographic tasks, ensure the Firebase Function timeout is configured to be *longer* than the local client timeout (e.g., set the Function to 120s if the client expects a 60s max response).

## 3. Error Handling
- The adapter strictly expects a 200 HTTP status code.
- **Requirement**: The Firebase Function MUST return specific HTTP error codes (400 for bad manifest, 401 for auth failure, 500 for decryption error) so the client can log appropriate diagnostic info.

## 4. CORS
- Currently unused as this is a server-to-server request.
- **Requirement**: If this endpoint is ever exposed to a browser-based frontend, you must explicitly enable CORS in Firebase Function settings for your production domain.
