# 🏗️ Autocode Architecture Overview

**Project Summary:** 28 Classes | 3,097 LOC | 11 Modules

```mermaid
graph TD
    subgraph "🏗️ Autocode Project"
        subgraph "🏗️ Autocode [28 Classes | 3097 LOC]"
            subgraph "🌐 API [14 Classes | 81 LOC]"
                C0["CheckResult<br/>LOC: 8"]
                C1["DaemonStatus<br/>LOC: 6"]
                C2["CheckConfig<br/>LOC: 4"]
                C3["TokenConfig<br/>LOC: 5"]
                C4["DaemonConfig<br/>LOC: 6"]
                C5["ApiConfig<br/>LOC: 4"]
                C6["DocIndexConfig<br/>LOC: 6"]
                C7["DocsConfig<br/>LOC: 6"]
                C8["TestConfig<br/>LOC: 7"]
                C9["CodeToDesignConfig<br/>LOC: 7"]
                C10["AutocodeConfig<br/>LOC: 8"]
                C11["StatusResponse<br/>LOC: 5"]
                C12["CheckExecutionRequest<br/>LOC: 4"]
                C13["CheckExecutionResponse<br/>LOC: 5"]
            end
            subgraph "⚙️ Core [11 Classes | 2392 LOC]"
                subgraph "🤖 AI [2 Classes | 349 LOC]"
                    C14["OpenCodeExecutor<br/>LOC: 226"]
                    C15["TokenCounter<br/>LOC: 123"]
                end
                subgraph "🎨 Design [1 Classes | 705 LOC]"
                    C16["CodeToDesign<br/>LOC: 705"]
                end
                subgraph "📚 Docs [3 Classes | 648 LOC]"
                    C17["DocStatus<br/>LOC: 6"]
                    C18["DocChecker<br/>LOC: 322"]
                    C19["DocIndexer<br/>LOC: 320"]
                end
                subgraph "🔧 Git [3 Classes | 403 LOC]"
                    C20["FileChange<br/>LOC: 8"]
                    C21["GitStatus<br/>LOC: 8"]
                    C22["GitAnalyzer<br/>LOC: 387"]
                end
                subgraph "🧪 Test [2 Classes | 287 LOC]"
                    C23["TestStatus<br/>LOC: 6"]
                    C24["TestChecker<br/>LOC: 281"]
                end
            end
            subgraph "🔄 Orchestration [3 Classes | 624 LOC]"
                C25["AutocodeDaemon<br/>LOC: 460"]
                C26["ScheduledTask<br/>LOC: 12"]
                C27["Scheduler<br/>LOC: 152"]
            end
        end
    end

    %% Module relationships
    API --> Core
    Core --> Orchestration
    Orchestration --> Web

    %% Interactive links to class documentation
    click C0 "./autocode/api/models_class.md#checkresult" "CheckResult - LOC: 8 | Methods: 0"
    click C1 "./autocode/api/models_class.md#daemonstatus" "DaemonStatus - LOC: 6 | Methods: 0"
    click C2 "./autocode/api/models_class.md#checkconfig" "CheckConfig - LOC: 4 | Methods: 0"
    click C3 "./autocode/api/models_class.md#tokenconfig" "TokenConfig - LOC: 5 | Methods: 0"
    click C4 "./autocode/api/models_class.md#daemonconfig" "DaemonConfig - LOC: 6 | Methods: 0"
    click C5 "./autocode/api/models_class.md#apiconfig" "ApiConfig - LOC: 4 | Methods: 0"
    click C6 "./autocode/api/models_class.md#docindexconfig" "DocIndexConfig - LOC: 6 | Methods: 0"
    click C7 "./autocode/api/models_class.md#docsconfig" "DocsConfig - LOC: 6 | Methods: 0"
    click C8 "./autocode/api/models_class.md#testconfig" "TestConfig - LOC: 7 | Methods: 0"
    click C9 "./autocode/api/models_class.md#codetodesignconfig" "CodeToDesignConfig - LOC: 7 | Methods: 0"
    click C10 "./autocode/api/models_class.md#autocodeconfig" "AutocodeConfig - LOC: 8 | Methods: 0"
    click C11 "./autocode/api/models_class.md#statusresponse" "StatusResponse - LOC: 5 | Methods: 0"
    click C12 "./autocode/api/models_class.md#checkexecutionrequest" "CheckExecutionRequest - LOC: 4 | Methods: 0"
    click C13 "./autocode/api/models_class.md#checkexecutionresponse" "CheckExecutionResponse - LOC: 5 | Methods: 0"
    click C14 "./autocode/core/ai/opencode_executor_class.md#opencodeexecutor" "OpenCodeExecutor - LOC: 226 | Methods: 12"
    click C15 "./autocode/core/ai/token_counter_class.md#tokencounter" "TokenCounter - LOC: 123 | Methods: 6"
    click C16 "./autocode/core/design/code_to_design_class.md#codetodesign" "CodeToDesign - LOC: 705 | Methods: 16"
    click C17 "./autocode/core/docs/doc_checker_class.md#docstatus" "DocStatus - LOC: 6 | Methods: 0"
    click C18 "./autocode/core/docs/doc_checker_class.md#docchecker" "DocChecker - LOC: 322 | Methods: 20"
    click C19 "./autocode/core/docs/doc_indexer_class.md#docindexer" "DocIndexer - LOC: 320 | Methods: 10"
    click C20 "./autocode/core/git/git_analyzer_class.md#filechange" "FileChange - LOC: 8 | Methods: 0"
    click C21 "./autocode/core/git/git_analyzer_class.md#gitstatus" "GitStatus - LOC: 8 | Methods: 0"
    click C22 "./autocode/core/git/git_analyzer_class.md#gitanalyzer" "GitAnalyzer - LOC: 387 | Methods: 11"
    click C23 "./autocode/core/test/test_checker_class.md#teststatus" "TestStatus - LOC: 6 | Methods: 0"
    click C24 "./autocode/core/test/test_checker_class.md#testchecker" "TestChecker - LOC: 281 | Methods: 15"
    click C25 "./autocode/orchestration/daemon_class.md#autocodedaemon" "AutocodeDaemon - LOC: 460 | Methods: 11"
    click C26 "./autocode/orchestration/scheduler_class.md#scheduledtask" "ScheduledTask - LOC: 12 | Methods: 1"
    click C27 "./autocode/orchestration/scheduler_class.md#scheduler" "Scheduler - LOC: 152 | Methods: 10"

```

## Module Details

### Autocode
- **Classes:** 28
- **Lines of Code:** 3,097
- **Average LOC per Class:** 110
- **Submodules:** 5

### Autocode > Api
- **Classes:** 14
- **Lines of Code:** 81
- **Average LOC per Class:** 5

### Autocode > Core
- **Classes:** 11
- **Lines of Code:** 2,392
- **Average LOC per Class:** 217
- **Submodules:** 5

### Autocode > Core > Ai
- **Classes:** 2
- **Lines of Code:** 349
- **Average LOC per Class:** 174

### Autocode > Core > Design
- **Classes:** 1
- **Lines of Code:** 705
- **Average LOC per Class:** 705

### Autocode > Core > Docs
- **Classes:** 3
- **Lines of Code:** 648
- **Average LOC per Class:** 216

### Autocode > Core > Git
- **Classes:** 3
- **Lines of Code:** 403
- **Average LOC per Class:** 134

### Autocode > Core > Test
- **Classes:** 2
- **Lines of Code:** 287
- **Average LOC per Class:** 143

### Autocode > Orchestration
- **Classes:** 3
- **Lines of Code:** 624
- **Average LOC per Class:** 208

