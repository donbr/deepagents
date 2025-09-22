# Architectural Decision Records (ADR) Template

## Purpose

This template standardizes how architectural decisions are documented, ensuring that context, trade-offs, and rationale are captured for future reference and learning.

## When to Create an ADR

Create an ADR for any decision that:
- Affects the architecture or design of the system
- Has significant impact on future development
- Involves trade-offs between different approaches
- Addresses integration patterns or technology choices
- Resolves ambiguity in implementation approach

## ADR Template

```markdown
# ADR-[NUMBER]: [Title]

**Date:** [YYYY-MM-DD]
**Status:** [Proposed | Accepted | Deprecated | Superseded]
**Deciders:** [List of people involved in the decision]
**Consulted:** [List of people consulted]
**Informed:** [List of people informed]

## Context

Describe the forces at play, including technological, political, social, and project context. This section should be neutral and factual.

### Background
What led to this decision being needed?

### Constraints
What limitations or requirements must be considered?

### Requirements
What must the solution achieve?

## Decision

State the decision clearly and concisely.

### What We Will Do
Clear statement of the chosen approach.

### What We Will Not Do
Explicit statements about rejected alternatives.

## Rationale

Explain why this decision was made.

### Pros of Chosen Approach
- Benefit 1
- Benefit 2
- Benefit 3

### Cons of Chosen Approach
- Limitation 1
- Limitation 2
- Limitation 3

### Alternatives Considered
Brief description of other options and why they were rejected.

## Consequences

What are the implications of this decision?

### Positive Consequences
- Expected benefit 1
- Expected benefit 2

### Negative Consequences
- Expected cost 1
- Expected limitation 1

### Risks
- Risk 1 and mitigation strategy
- Risk 2 and mitigation strategy

## Implementation Notes

### Technical Details
Key implementation considerations.

### Dependencies
What must be in place for this to work?

### Timeline
When will this be implemented?

## Validation

How will we know if this decision was correct?

### Success Criteria
- Measurable outcome 1
- Measurable outcome 2

### Monitoring
How will we track the impact of this decision?

### Review Date
When will we evaluate this decision? [YYYY-MM-DD]

## References

- [Link to requirements](./requirements.md)
- [Related ADRs](./adr-001.md)
- [External documentation](https://example.com)

---
*This ADR supersedes: [ADR-XXX]*
*This ADR is superseded by: [ADR-XXX]*
```

## ADR Examples

### Example 1: MCP Session Management Architecture

```markdown
# ADR-001: MCP Session Management Architecture

**Date:** 2025-01-15
**Status:** Accepted
**Deciders:** Engineering Team
**Consulted:** DevOps Team
**Informed:** Product Team

## Context

### Background
DeepAgents integration with MCP servers was experiencing connection storms, with 20+ connections created per research query. The `langchain-mcp-adapters` library creates new sessions for each tool call by default, leading to resource exhaustion and poor performance.

### Constraints
- Must work with existing `langchain-mcp-adapters` library
- Cannot modify third-party MCP servers
- Must maintain compatibility with DeepAgents framework
- Must support concurrent tool calls

### Requirements
- Reduce connection count to single persistent session per MCP server
- Maintain tool call functionality without degradation
- Provide proper session cleanup on application shutdown
- Support graceful error handling and recovery

## Decision

### What We Will Do
Implement application-level session management using explicit session contexts and tool loading from persistent sessions.

### What We Will Not Do
- We will not use `client.get_tools()` which creates per-call sessions
- We will not create new sessions for each tool invocation
- We will not rely on automatic session management

## Rationale

### Pros of Chosen Approach
- Single persistent connection eliminates connection storms
- Better resource utilization and performance
- Explicit lifecycle management provides predictable behavior
- Reusable pattern for other MCP integrations

### Cons of Chosen Approach
- More complex initialization code
- Need to manage session lifecycle explicitly
- Requires application-level state management
- More sophisticated error handling needed

### Alternatives Considered
1. **Use connection pooling** - Rejected due to complexity and library limitations
2. **Modify langchain-mcp-adapters** - Rejected as third-party dependency
3. **Create wrapper tools** - Rejected as insufficient abstraction

## Consequences

### Positive Consequences
- ~95% reduction in connection overhead
- Faster tool call performance
- Cleaner server logs
- More predictable resource usage

### Negative Consequences
- Additional complexity in application startup/shutdown
- Need for proper error handling and recovery
- Testing requires session lifecycle management

### Risks
- Session failure requires application restart - mitigated by error handling and reconnection logic
- Memory leaks if cleanup not performed - mitigated by proper lifecycle management
- Complexity in testing - mitigated by test utilities and fixtures

## Implementation Notes

### Technical Details
```python
# Use explicit session management
mcp_session_context = mcp_client.session("server-name")
session = await mcp_session_context.__aenter__()
tools = await load_mcp_tools(session)
# Always cleanup: await mcp_session_context.__aexit__(None, None, None)
```

### Dependencies
- `langchain-mcp-adapters` library with session support
- Proper async context manager handling in application

### Timeline
- Immediate implementation for existing MCP integrations
- Pattern to be used for all future MCP integrations

## Validation

### Success Criteria
- Connection count reduced from 20+ to 1 per server
- Tool call functionality maintained
- No session leaks in production
- Performance improvement measurable

### Monitoring
- Track connection count via network monitoring
- Monitor session lifecycle via application logs
- Measure tool call performance and success rates

### Review Date
2025-04-15 - Review effectiveness and any issues encountered

## References

- [MCP Session Management Guide](./mcp-session-management-guide.md)
- [langchain-mcp-adapters Documentation](https://github.com/modelcontextprotocol/langchain-mcp-adapters)
- [Connection Storm Issue Analysis](./retrospective-analysis.md#connection-storm-problem)

---
*This ADR supersedes: None*
*This ADR is superseded by: None*
```

### Example 2: Requirements Analysis Process

```markdown
# ADR-002: Requirements-First Development Process

**Date:** 2025-01-15
**Status:** Accepted
**Deciders:** Engineering Team, Product Team
**Consulted:** Stakeholders
**Informed:** All Development Teams

## Context

### Background
Recent project work revealed significant gaps between actual requirements and delivered functionality. In the DeepAgents MCP integration, a sophisticated multi-strategy retrieval platform was required, but only basic API conversion was delivered (~15% of scope).

### Constraints
- Must work with existing development workflows
- Cannot significantly slow down development velocity
- Must be practical for both large and small features
- Must integrate with existing planning and tracking tools

### Requirements
- Ensure technical implementation aligns with business requirements
- Prevent scope misalignment and rework
- Provide traceability from requirements to implementation
- Enable early detection of scope gaps

## Decision

### What We Will Do
Implement a requirements-first development process with mandatory requirements analysis before any technical implementation begins.

### What We Will Not Do
- We will not start coding without documented requirements understanding
- We will not proceed without stakeholder validation of scope
- We will not skip requirements analysis for "quick fixes"

## Rationale

### Pros of Chosen Approach
- Prevents scope misalignment and rework
- Ensures business value is delivered
- Provides clear success criteria
- Enables better effort estimation

### Cons of Chosen Approach
- Additional upfront effort required
- May slow initial development velocity
- Requires discipline to follow process
- More documentation overhead

### Alternatives Considered
1. **Lightweight requirements capture** - Rejected as insufficient to prevent scope gaps
2. **Post-implementation validation** - Rejected as too late to prevent rework
3. **Informal requirements discussion** - Rejected as lacks traceability

## Consequences

### Positive Consequences
- Higher quality deliverables that match expectations
- Reduced rework and emergency fixes
- Better stakeholder confidence
- Improved project predictability

### Negative Consequences
- Slightly longer planning phase
- More process overhead for small changes
- Need for team training on new process
- Additional documentation maintenance

### Risks
- Process becomes bureaucratic if not balanced - mitigated by lightweight templates
- Team resistance to additional process - mitigated by showing value through examples
- Requirements analysis paralysis - mitigated by time-boxing analysis phase

## Implementation Notes

### Technical Details
- Use requirements traceability framework
- Mandatory reading of INSTRUCTIONS.md or equivalent
- Stakeholder confirmation before implementation
- Regular status tracking against requirements

### Dependencies
- Requirements traceability framework implementation
- Team training on new process
- Integration with existing project management tools

### Timeline
- Immediate implementation for all new work
- Retrospective application to in-flight projects
- Process refinement based on initial experience

## Validation

### Success Criteria
- Zero major scope gaps in delivered functionality
- Stakeholder acceptance rate >95%
- Reduced emergency fixes and rework
- Improved project predictability metrics

### Monitoring
- Track requirements coverage for each project
- Measure stakeholder satisfaction with deliverables
- Monitor rework and scope change frequency
- Collect team feedback on process effectiveness

### Review Date
2025-04-15 - Evaluate process effectiveness and refinements needed

## References

- [Requirements Traceability Framework](./requirements-traceability-framework.md)
- [Retrospective Analysis](./retrospective-analysis.md)
- [DeepAgents Requirements Gap Analysis](./retrospective-analysis.md#requirements-analysis-gap)

---
*This ADR supersedes: Informal requirements gathering*
*This ADR is superseded by: None*
```

## ADR Management Process

### Creating ADRs

1. **Number Assignment:** Use sequential numbering (ADR-001, ADR-002, etc.)
2. **File Naming:** `adr-001-title-in-kebab-case.md`
3. **Location:** Store in `references/adrs/` directory
4. **Review Process:** Technical review by 2+ team members before acceptance

### ADR Lifecycle

**Proposed** → **Accepted** → **Deprecated** → **Superseded**

- **Proposed:** Decision is being considered
- **Accepted:** Decision is finalized and being implemented
- **Deprecated:** Decision is no longer recommended but still in use
- **Superseded:** Decision has been replaced by a newer ADR

### ADR Index

Maintain an index file listing all ADRs:

```markdown
# ADR Index

| Number | Title | Status | Date | Review Date |
|--------|-------|--------|------|-------------|
| [ADR-001](./adr-001-mcp-session-management.md) | MCP Session Management Architecture | Accepted | 2025-01-15 | 2025-04-15 |
| [ADR-002](./adr-002-requirements-first-process.md) | Requirements-First Development Process | Accepted | 2025-01-15 | 2025-04-15 |
| [ADR-003](./adr-003-feature-branch-strategy.md) | Feature Branch Strategy | Proposed | 2025-01-15 | TBD |
```

### Review and Updates

1. **Regular Reviews:** Schedule quarterly ADR reviews
2. **Status Updates:** Update status as decisions evolve
3. **Superseding:** When replacing decisions, clearly link old and new ADRs
4. **Learning Integration:** Use ADRs as input for retrospectives and planning

## Tools and Automation

### ADR Creation Script

```bash
#!/bin/bash
# create-adr.sh

ADR_NUMBER=${1:-$(find references/adrs -name "adr-*.md" | wc -l | awk '{print $1+1}')}
ADR_TITLE=${2:-"New Decision"}
ADR_SLUG=$(echo "$ADR_TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')
ADR_FILE="references/adrs/adr-$(printf "%03d" $ADR_NUMBER)-$ADR_SLUG.md"

# Create ADR from template
sed "s/\[NUMBER\]/$ADR_NUMBER/g; s/\[Title\]/$ADR_TITLE/g" references/adr-template.md > "$ADR_FILE"

echo "Created ADR: $ADR_FILE"
echo "Don't forget to update the ADR index!"
```

### ADR Validation

```python
# adr_validator.py
import re
import sys
from pathlib import Path

def validate_adr(file_path):
    """Validate ADR follows template structure"""
    content = Path(file_path).read_text()

    required_sections = [
        "## Context",
        "## Decision",
        "## Rationale",
        "## Consequences",
        "## Implementation Notes",
        "## Validation"
    ]

    for section in required_sections:
        if section not in content:
            print(f"❌ Missing required section: {section}")
            return False

    if not re.search(r"Status.*Proposed|Accepted|Deprecated|Superseded", content):
        print("❌ Invalid or missing status")
        return False

    print("✅ ADR validation passed")
    return True

if __name__ == "__main__":
    validate_adr(sys.argv[1])
```

This ADR template and process ensures that architectural decisions are properly documented, reasoned about, and can be referenced for future learning and decision-making.