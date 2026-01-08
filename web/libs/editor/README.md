# Synapse Frontend

Synapse Frontend (SF) is a crucial module of the Synapse ecosystem, pivotal in driving the entire annotation flow. It's a front-end-only module, combining a user interface for annotation creation with a data layer that standardizes the annotation format. Every manual annotation in Synapse has been crafted using SF, making it integral to the system.

### Usage Instructions

SF provides specific scripts for operation and testing:

_Important Note: These scripts must be executed within the web folder or its subfolders. This is crucial for the scripts to function correctly, as they are designed to work within the context of the web directory's structure and dependencies._

- **`yarn sf:watch`: Build SF continuously**
  - Crucial for development, this script continuously builds Synapse Frontend (SF), allowing developers to observe their changes in real-time within the Synapse environment.
- **`yarn sf:serve`: Run SF standalone**
  - To run Synapse Frontend in standalone mode. Visit http://localhost:3000 to use the application in standalone mode.
- **`yarn sf:e2e`: Execute end-to-end (e2e) tests on SF**
  - To run comprehensive e2e tests, ensuring the frontend works as expected from start to finish. The Synapse environment must be running, typically at `http://localhost:8080`.
- **`yarn sf:integration`: Run integration tests**
  - To conduct integration tests using Cypress, verifying that different parts of SF work together correctly. The SF in standalone mode (`yarn sf:serve`) must be running.
- **`yarn sf:integration:ui`: Run integration tests in UI mode**
  - Facilitates debugging during integration tests by running them in a UI mode, allowing you to visually track what is being tested. The SF in standalone mode (`yarn sf:serve`) must be running.
- **`yarn sf:unit`: Run unit tests on SF**
  - Essential for maintaining code quality and reliability, especially in collaborative development.

<img src="https://github.com/Synapse/synapse/blob/develop/images/opossum_looking.png?raw=true" title="Hey everyone!" height="140" width="140" />


