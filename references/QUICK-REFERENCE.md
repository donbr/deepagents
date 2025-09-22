# Quick Reference Guide for Claude Code

## When to Use Each Document

### Starting New Work
**\u2192 READ FIRST: [Process Improvements & Checklists](./process-improvements-checklists.md#pre-development-checklist)**
- Pre-development checklist
- Requirements analysis checklist
- Technical planning checklist

### Understanding Requirements
**\u2192 USE: [Requirements Traceability Framework](./requirements-traceability-framework.md)**
- When you see INSTRUCTIONS.md or specifications
- Before implementing any feature
- To understand scope and priorities
- To validate with stakeholders

### Implementing MCP Integration
**\u2192 USE: [MCP Session Management Guide](./mcp-session-management-guide.md)**
- **CRITICAL**: Avoid connection storms
- Proper session lifecycle management
- Testing strategies
- Performance monitoring

### Adding or Modifying Features
**\u2192 USE: [Feature Branch Strategy](./feature-branch-strategy.md)**
- Determine: Additive vs Enhancement vs Replacement
- Preserve working functionality
- Migration paths and deprecation

### Making Architectural Decisions
**\u2192 USE: [ADR Template](./adr-template.md)**
- Document significant technical decisions
- Capture context and trade-offs
- Record rationale for future reference

### Learning from Past Mistakes
**\u2192 USE: [Retrospective Analysis](./retrospective-analysis.md)**
- Understand the 85% scope gap issue
- Learn from connection storm problem
- See feature development failures

## Common Scenarios

### "I need to add MCP support to an existing feature"
1. Read: [MCP Session Management Guide](./mcp-session-management-guide.md#best-practices)
2. Follow: [Feature Branch Strategy](./feature-branch-strategy.md#additive-features)
3. Use: Additive pattern - create new file alongside existing

### "I need to fix a performance issue"
1. Read: [Feature Branch Strategy](./feature-branch-strategy.md#enhancement-features)
2. Document: Use [ADR Template](./adr-template.md) for approach
3. Test: Both old and new performance

### "I need to replace existing functionality"
1. Read: [Feature Branch Strategy](./feature-branch-strategy.md#replacement-features)
2. Implement: Feature flags for gradual migration
3. Document: Migration timeline and deprecation

### "I'm getting connection errors with MCP"
1. **STOP**: You likely have a connection storm
2. Read: [MCP Session Management Guide](./mcp-session-management-guide.md#anti-patterns)
3. Fix: Use explicit session management pattern

### "I'm not sure what the requirements are"
1. **STOP**: Don't code without requirements
2. Read: [Requirements Traceability Framework](./requirements-traceability-framework.md)
3. Find: INSTRUCTIONS.md or ask for requirements
4. Validate: Understanding with stakeholder

## Critical Anti-Patterns

### \u274c NEVER DO THESE:
```python
# Connection Storm Anti-Pattern
client = MultiServerMCPClient({...})
tools = await client.get_tools()  # Creates new session per tool call!
```

```python
# Direct Modification Anti-Pattern
# DON'T modify working research_agent.py
# DO create research_agent_mcp.py alongside it
```

```python
# Requirements-Last Anti-Pattern
# DON'T start coding then figure out requirements
# DO read requirements first, validate scope, then code
```

### \u2705 ALWAYS DO THESE:
```python
# Proper Session Management
session_ctx = client.session("server-name")
session = await session_ctx.__aenter__()
tools = await load_mcp_tools(session)
```

```python
# Additive Development
# Keep: research_agent.py (working)
# Add: research_agent_mcp.py (new feature)
```

```python
# Requirements-First Development
# 1. Read INSTRUCTIONS.md
# 2. Create traceability matrix
# 3. Validate with stakeholder
# 4. Then implement
```

## Process Flow

```
START
  \u2193
Read Requirements (requirements-traceability-framework.md)
  \u2193
Classify Feature Type (feature-branch-strategy.md)
  \u2193
Document Architecture Decision (adr-template.md)
  \u2193
Follow Implementation Checklist (process-improvements-checklists.md)
  \u2193
For MCP: Use Session Management (mcp-session-management-guide.md)
  \u2193
Test Both Old and New
  \u2193
Follow Pre-Merge Checklist
  \u2193
DONE
```

## Emergency Procedures

### Connection Storm Active
1. See: [MCP Session Management Guide](./mcp-session-management-guide.md#connection-storm-issue)
2. Implement: Emergency response procedures
3. Fix: Session management pattern

### Scope Misalignment Detected
1. See: [Retrospective Analysis](./retrospective-analysis.md#requirements-analysis-gap)
2. Stop: Current development
3. Reassess: Requirements with stakeholder

### Breaking Existing Functionality
1. See: [Feature Branch Strategy](./feature-branch-strategy.md#anti-patterns)
2. Restore: Original functionality
3. Implement: Additive pattern instead

## Remember

**Documentation without integration is wasted effort.**

These guides exist because of painful lessons learned. Use them proactively to avoid repeating mistakes. When in doubt, check the retrospective analysis to understand why these patterns matter.