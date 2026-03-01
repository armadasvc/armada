---
title: Armada
---

{{< blocks/cover title="Armada" image_anchor="top" height="full" color="dark" >}}
<p class="lead mt-5">A Kubernetes-native orchestration platform for scalable, distributed web automation.</p>
<p class="mt-2">Define a project. Armada distributes the work. Agents execute it in parallel — at any scale.</p>
<a class="btn btn-lg btn-primary me-3 mb-4" href="docs/getting-started/">
Get Started <i class="fas fa-arrow-alt-circle-right ms-2"></i>
</a>
<a class="btn btn-lg btn-secondary me-3 mb-4" href="docs/">
Browse the Docs <i class="fas fa-book ms-2"></i>
</a>
{{< blocks/link-down id="td-block-1" >}}
{{< /blocks/cover >}}


{{% blocks/lead color="primary" %}}
**One script. Hundreds of parallel workers. Full observability.**

Armada takes your automation code and runs it across a fleet of containerized agents — each with its own browser, proxy, and identity — while you monitor everything from a real-time dashboard.
{{% /blocks/lead %}}


{{% blocks/section color="white" type="container" %}}

{{% blocks/feature icon="fas fa-rocket" title="Getting Started" url="docs/getting-started/" %}}
Understand the core concepts — projects, orchestrator, agents, jobs — and launch your first run in minutes.
{{% /blocks/feature %}}

{{% blocks/feature icon="fas fa-book" title="Guides" url="docs/guides/" %}}
Step-by-step walkthroughs for installation, project configuration, the workbench, and CI/CD integration.
{{% /blocks/feature %}}

{{% blocks/feature icon="fas fa-drafting-compass" title="Architecture" url="docs/architecture/" %}}
Deep dive into how Armada is built: microservices, data flow, Redis, RabbitMQ, and Kubernetes orchestration.
{{% /blocks/feature %}}

{{% /blocks/section %}}


{{% blocks/section color="light" type="container" %}}

{{% blocks/feature icon="fas fa-cubes" title="Services" url="docs/services/" %}}
Documentation for every microservice: backend API, orchestrator, agent, frontend, and provider services.
{{% /blocks/feature %}}

{{% blocks/feature icon="fas fa-mask" title="Fantomas" url="docs/fantomas/" %}}
Anti-detection browser automation library built on undetected Chrome — stealth fingerprinting, proxy rotation, and more.
{{% /blocks/feature %}}

{{% blocks/feature icon="fas fa-cogs" title="Reference" url="docs/reference/" %}}
API endpoints, configuration parameters, database schema, security model, and glossary.
{{% /blocks/feature %}}

{{% /blocks/section %}}


{{% blocks/section color="dark" type="container" %}}

{{% blocks/feature icon="fas fa-file-alt" title="Specs" url="docs/specs/" %}}
Technical specifications, original design documents, and detailed tutorials from the project's foundation.
{{% /blocks/feature %}}

{{% blocks/feature icon="fas fa-terminal" title="Quick Start" url="docs/specs/quickstart-guide/" %}}
Go from zero to a running Armada instance with Docker Compose in a single guide.
{{% /blocks/feature %}}

{{% blocks/feature icon="fas fa-dharmachakra" title="Kubernetes Deploy" url="docs/specs/quickstart-kubernetes/" %}}
Deploy Armada on a real Kubernetes cluster with Helm charts and production-ready configuration.
{{% /blocks/feature %}}

{{% /blocks/section %}}


{{% blocks/section color="white" type="container" %}}

## How It Works

<div class="row justify-content-center">
<div class="col-lg-10">

| Step | What Happens |
|------|-------------|
| **1. Define** | You create a project folder with your automation script, a config template, and optional CSV overrides. |
| **2. Launch** | The frontend bundles everything and sends it to the Orchestrator. |
| **3. Distribute** | The Orchestrator merges configs into Redis (one per agent) and dispatches jobs into RabbitMQ. |
| **4. Execute** | Agent pods start, each reads its config, initializes a browser & proxy, and consumes jobs from the queue. |
| **5. Monitor** | Every agent reports progress via WebSocket to a real-time dashboard. |

</div>
</div>

{{% /blocks/section %}}


{{% blocks/section color="primary" %}}

<div class="col text-center">
<h2 class="mb-4">Ready to get started?</h2>
<a class="btn btn-lg btn-light me-3 mb-4" href="docs/getting-started/">
Read the Tutorial <i class="fas fa-graduation-cap ms-2"></i>
</a>
<a class="btn btn-lg btn-outline-light me-3 mb-4" href="docs/specs/quickstart-guide/">
Quick Start Guide <i class="fas fa-play ms-2"></i>
</a>
</div>

{{% /blocks/section %}}
