# Local runtime configuration

`local.yaml` is the discoverable, committed configuration for the initial local filesystem content-artifact store. A fresh checkout must be able to start the local artifact store without exporting storage environment variables or creating a `.env` file.

The configured `./content/` directory contains runtime artifact bytes and is ignored by Git. Do not put passwords, tokens, cloud credentials, or production endpoints in this directory. Future cloud adapters may use platform secret stores and provider-specific deployment configuration when they are implemented.
