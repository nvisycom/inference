# Nvisy Inference

[![Build](https://img.shields.io/github/actions/workflow/status/nvisycom/inference/build.yml?branch=main&label=build%20%26%20test&style=flat-square)](https://github.com/nvisycom/inference/actions/workflows/build.yml)

Externalized model inference for the [Nvisy runtime](https://github.com/nvisycom/runtime).

Hosts each model as a standalone HTTP service so the runtime calls inference
over the network instead of loading ML runtimes in-process. Each model category
ships as its own independently scalable, independently deployable service behind
a stable wire contract.

## Features

- **Contract-first, swappable engines**: services implement a versioned wire contract, not a specific model — the engine behind each contract can be replaced without touching the runtime
- **Model categories**: detection OCR (text + word-level geometry), vision-language OCR (high-accuracy transcription and layout), and named-entity recognition over a shared entity taxonomy
- **Layered OCR**: traditional OCR provides precise geometry while an optional GPU vision-language service refines text accuracy; the runtime reconciles the two
- **Independent services**: each model runs as its own image with independent scaling and failure domains, and any service can be opted out of
- **Bring your own inference**: any service that reproduces the wire contract is a drop-in replacement, including self-hosted or custom models and weights
- **Lockstep versioning**: inference releases track the runtime version so the contract stays in sync

## Quick Start

The fastest way to get started is with [Nvisy Cloud](https://nvisy.com).

For self-hosted deployments, the services are published as container images and
run alongside the [Nvisy runtime](https://github.com/nvisycom/runtime); see
[`docs/`](docs/) for the wire contract and deployment guidance.

## Documentation

See [`docs/`](docs/) for architecture, contract, and API documentation.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes and version history.

## License

Apache 2.0 License, see [LICENSE.txt](LICENSE.txt)

## Support

- **Documentation**: [docs.nvisy.com](https://docs.nvisy.com)
- **Issues**: [GitHub Issues](https://github.com/nvisycom/inference/issues)
- **Email**: [support@nvisy.com](mailto:support@nvisy.com)
