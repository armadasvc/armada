---
title: 4.6. Next Steps
linkTitle: 4.6. Next Steps
weight: 6
description: Planned improvements and upcoming features for the Armada platform
---

This page outlines the areas we have identified for future development. They are grouped by component and roughly ordered by theme rather than strict priority. Each item represents a meaningful improvement that would bring Armada closer to a production-grade, fully observable, and developer-friendly platform.

---

## Fantomas

### Intelligent Page Waiter

Implement a robust, smart waiting mechanism that pauses execution until a given page element is fully loaded and interactive. The current approach can be fragile when dealing with dynamically rendered content. A proper waiter should support configurable timeouts, polling strategies, and clear failure messages when an element never appears.

### Scroll-to-Element

Add the ability to programmatically scroll to a specific element on a page. This is essential for interacting with content that is rendered below the fold or inside scrollable containers, and it should work reliably regardless of the page layout.

### MonkeyPatch Support

Add a mechanism to MonkeyPatch Fantomas, allowing users to override or extend internal behaviors at runtime without modifying the core library. This enables quick experimentation, custom workarounds, and project-specific adjustments without forking the codebase.

### Secondary Flow

Support running two Fantomas processes in parallel within a single agent. This enables secondary flows such as handling a separate browser session for verification, authentication refresh, or auxiliary data collection alongside the primary navigation.

### Secondary Screen

Add the ability to manage a secondary screen or virtual display within Fantomas.

### Microservice Realtime Input for Debugging

Introduce a microservice that captures realtime input events (keyboard presses, mouse movements) and streams them into a running Fantomas session inside Kubernetes. This would provide a powerful debugging tool, allowing developers to interact live with a headless browser running in a pod.

### Autocapture Screenshot

Automatically capture screenshots of the browser screen at a configurable interval (every X seconds) and stream or store them so they can be displayed in the frontend. This provides a visual timeline of execution, making it much easier to understand what happened during a run and to spot issues.

---

## Orchestrator

### More advanced External Output System

Provide an alternative output mechanism so that run results and collected data can be exported through channels other than the database — for example, writing to files, exporting to a CSV, streaming to an external API, or pushing to a message queue. This would make Armada more flexible for integration into diverse data pipelines.

### More robust advanced orchestration mechanism : centralized Error Management (Circuit Breaker), retry-backoff logic

Introduce a centralized mechanism that tracks consecutive errors across pods and across the entire run. For example, if a single pod accumulates 5 consecutive errors, that pod should be automatically stopped; if the run as a whole reaches 15 consecutive errors, the entire run should be terminated gracefully. This prevents wasting resources on runs that are clearly failing. Add also and advanced retry-backoff logic at pod/agent level.

### Pod-Based Execution

Add a new mode besides the job-mode with long-lived pods that pull work items from a queue. This would be usefull for very long-lived task.

### Dynamic Queue Refill Module

Build a module that can dynamically refill work queues during a run. Instead of requiring all work items to be enqueued before launch, this would allow the system to feed new items into the queue based on external triggers, API calls, or the results of previously completed tasks.

### Orchestrator Control Methods from Frontend

Expose orchestrator management actions (such as cleaning queues, viewing run status, and controlling execution) through the frontend interface. This removes the need for direct backend access and gives operators a convenient way to monitor and manage runs from the web UI.

---

## Agent

### Launch a Job from Within a Job

Enable a running job to programmatically spawn a child job. This opens the door to multi-step workflows where one task can trigger follow-up tasks, enabling more complex orchestration patterns without external intervention.

### Conditional Dependencies in the Agent Image

Make heavy dependencies like Chrome or `xdotool` optional in the agent container image. If a project only performs HTTP requests, there is no need to include a full browser stack. Additionally, allow users to specify an alternative Chromium-based browser if needed.

### Better Intellisense for the Agent Module

Improve IDE intellisense and autocompletion support for the agent module. This includes proper type hints, stub files, and package metadata so that developers get accurate suggestions, documentation tooltips, and error detection when writing scripts that use the agent API.

### Load Static Files at Container Creation

Allow users to specify static files or directories to be loaded into the agent container at creation time. This covers use cases such as loading a Chrome addon folder into the browser, importing a browser profile with saved preferences, or including any other assets that a project needs available from the start.

### Load Private Libraries at Container Creation

Add the ability to load private libraries into the agent container during its initialization — for example, by cloning a private Git repository. This enables projects to depend on proprietary or internal packages without baking them into the base image.

---

## Architecture

### Logging and Observability

Add a structured logging system and integrate an observability stack (metrics, traces, and logs) so that operators can monitor cluster health, debug issues in real time, and gain insight into run performance at scale.

### Volume-Based Code Loading

Load user code from a mounted volume instead of using `exec` to inject it at runtime. This is a meaningful security improvement as it eliminates the risk of remote code execution through the exec pathway.

### Migrate to SQLAlchemy

Replace the current `pymssql`-based database layer with SQLAlchemy. This provides a more robust ORM, better connection management, support for migrations, and improved portability across database backends.

### Expose an External API

Expose a public-facing API so that external systems can interact with Armada — for example, to trigger runs, query status, or retrieve results. This will also require a thorough security review and the implementation of proper authentication and authorization mechanisms.

### Human-Readable Run Names

Allow users to assign a descriptive `run_name` alongside the automatically generated `run_uuid`. This makes it much easier to identify and discuss specific runs without having to refer to opaque identifiers.

### Automated Cluster Provisioning

Automate the provisioning and configuration of Kubernetes clusters using infrastructure-as-code tools such as Ansible. This reduces manual setup, ensures consistency across environments, and makes it easier to reproduce deployments.

### More comprehensive End-to-End Testing Automation

Build a comprehensive end-to-end testing framework that validates the full Armada workflow — from project configuration to run execution and result collection — in an automated and reproducible way, and at least partially, integrated into CI/CD.

### Installable Agent SDK

Extract the agent's shared modules into a standalone, installable SDK package. Projects would then import the SDK as a regular dependency rather than relying on namespace sharing and exec-based code injection. This improves developer experience, versioning, and testability.

### Karpenter Integration for AWS Scaling

Integrate Karpenter as the node autoscaler for AWS-based deployments. Karpenter provides faster, more flexible, and cost-efficient node provisioning compared to the traditional Cluster Autoscaler, making it well suited for Armada's bursty workload patterns.

### CLI Toolset

Build a dedicated CLI toolset to control Armada more easily from the terminal. This would provide commands for launching runs, checking status, managing configuration, tailing logs, and interacting with the orchestrator — offering a fast, scriptable alternative to the web interface.

---

## Frontend

### CSV Upload from the Web Interface

Allow users to upload CSV files directly through the web interface to populate the database. This removes the need for manual database operations and makes data import accessible to non-technical users.

---

## Proxy Provider

### Accept Lists for Proxy Parameters

Update `proxy_location`, `proxy_provider_name`, and `proxy_type` to accept lists of acceptable values rather than a single value. This gives users more flexibility when defining proxy requirements and allows the system to select the best available option.

### Configurable Proxy Rotation Interval

Add a configurable rotation interval for proxies so that users can control how frequently the proxy provider cycles to a new proxy. Different use cases have different rotation needs, and a one-size-fits-all approach is too limiting.

### IP-per-Site Verification Layer

Introduce a verification layer that tracks proxy usage at the IP-per-site level. Before assigning a proxy, the system would check whether a given IP address has already been used too frequently on the target site, reducing the risk of detection and blocking.
