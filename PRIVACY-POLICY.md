# Privacy Policy and Terms of Use for LUCK

**Last Updated:** February 2026

## 1. Introduction and Scope
This document governs the use of **LUCK** ("the Application"), a database client tool for executing SQL queries and managing data exports. By installing and using the Application, you acknowledge that you have read, understood, and consented to these terms.

**Scope:** This policy applies solely to the Application itself and does not cover data processing performed by the operating system, app store (Microsoft Store), or platform services (GitHub), which are governed by their own respective privacy policies and terms of service.

## 2. Data Access and Declarations
The Application uses the `runFullTrust` restricted capability for the following functional purposes:
*   **ODBC Connectivity:** Accesses the Windows Registry to identify and utilize existing Data Source Names (DSN).
*   **File System Integration:** Accesses local directories solely to save exported query results (e.g., CSV, Excel) at the user's request.

## 3. Data Storage and Privacy Safeguards
*   **Strictly Local Storage:** Session data, execution logs, configuration settings, and query results are stored exclusively on the user's local machine. **This data is never shared externally, transmitted to the developer, or sent to any third parties.**
*   **Security Disclaimer:** Since all data remains on the local system, the prevention of data leaks or unauthorized access depends entirely on the user's own operating system security, local encryption settings, and device protection protocols.
*   **DSN Credentials:** The Application utilizes existing DSN configurations but does not edit, modify, or manage them. Credential security and encryption are governed by the user's local Windows DSN settings and the database driver's protocols.
*   **No Personal Data Collection:** We do not collect, harvest, or transmit any personally identifiable information (PII).

## 4. Software Updates
The update process is designed to respect user privacy:
*   **Microsoft Store Version:** Updates are managed exclusively through the Microsoft Store infrastructure.
*   **GitHub/Standalone Version:** The Application may connect to GitHub APIs to check for and download updates. GitHub may receive standard technical data (such as IP addresses) per their own privacy policy.
*   **No Telemetry:** **No telemetry, usage analytics, or behavioral data are collected or transmitted during the update process or during regular application usage.**

## 5. Disclaimer of Warranty and Liability
*   **"As Is" Basis:** The Application is provided "as is" without any warranties of any kind. This agreement is governed by applicable international principles and the user's local laws.
*   **Database Responsibility:** The Application allows execution of powerful SQL commands (e.g., `DROP`, `DELETE`, `TRUNCATE`). The user is solely responsible for all commands executed. 
*   **Exclusion of Liability:** The developer is **not responsible** for data loss, database corruption, misuse, or any damages resulting from the use of this tool. Users should always maintain current backups of their databases.

## 6. Policy Updates
This policy may be updated periodically to reflect new features or changes in compliance. Continued use of the Application constitutes acceptance of the revised policy.

## 7. Acceptance and Uninstallation
If you do not agree with any part of this policy or the risks involved in database management, you must not use the Application and should **uninstall it immediately**.

## 8. Licensing and Official Distribution
*   **License:** This Application is licensed under the **GNU General Public License v3.0**. You may inspect, modify, and redistribute the source code according to the terms of the GPL v3.
*   **Official Versions:** To ensure security and integrity, users should only install the Application from official sources: the **Microsoft Store** or the **Releases** section of our [GitHub Repository](https://github.com/jlondohi/Luck/releases). 
*   **Third-Party Forks:** The developer is not responsible for modified versions, unofficial "forks," or distributions provided by third-party websites. Such versions are not verified by the original author and may contain unauthorized changes or malicious code.

## 9. Contact and Support
For questions regarding this Privacy Policy, technical support, or to report issues, please use our official GitHub repository channels:
*   **Issue Tracker:** [GitHub Issues](https://github.com/jlondohi/Luck/issues)
*   **Discussions/Project Home:** [GitHub Discussions](https://github.com/jlondohi/Luck/discussions)

We do not collect or store contact information; all support interactions are handled publicly through the GitHub platform according to your own profile settings.