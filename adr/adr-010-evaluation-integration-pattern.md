# ADR-010: Evaluation Integration Pattern

## Status
✅ **ACCEPTED** - 2025-09-21

## Context

The DeepAgents ecosystem requires **comprehensive evaluation** to measure the quality and performance of agent workflows that integrate RAG capabilities from adv-rag. The rag-eval-foundations repository provides a complete 3-stage RAGAS evaluation pipeline that must integrate seamlessly with DeepAgents to provide continuous quality measurement and optimization feedback.

### Evaluation Requirements Analysis

#### **DeepAgents Evaluation Needs**
- **Agent Workflow Quality**: Measure end-to-end agent performance including planning, RAG usage, and synthesis
- **RAG Integration Effectiveness**: Evaluate how well agents use adv-rag MCP tools/resources
- **Performance Benchmarking**: Validate <2s/<8s performance targets across the ecosystem
- **Quality Metrics**: Quantify answer relevancy, context precision/recall, and faithfulness

#### **rag-eval-foundations Capabilities**
**Status**: ✅ **95% Complete** - Fully operational 3-stage evaluation pipeline

**3-Stage Pipeline**:
1. **Infrastructure Stage**: Docker services, PostgreSQL, Phoenix observability
2. **Golden Dataset Stage**: RAGAS test set generation with financial aid documents
3. **Automated Metrics Stage**: Comprehensive evaluation with visualizations

**Validated Performance** (July 2025):
- **269 PDF documents** processed and evaluated
- **6 retrieval strategies** comprehensively benchmarked
- **Full Phoenix observability** with experiment tracking
- **Complete validation scripts** ensuring pipeline reliability

#### **Integration Challenge**
**Gap**: rag-eval-foundations evaluates RAG strategies in isolation, but DeepAgents workflows involve:
- **Agent Planning**: `write_todos` tool usage and task breakdown
- **Sub-agent Orchestration**: Multi-agent coordination and communication
- **MCP Integration**: Tool selection and usage patterns
- **Context Management**: Virtual file system and state management

**Solution**: Extend evaluation pipeline to measure **complete agent workflows** rather than just RAG components.

## Decision

### **Comprehensive Agent Workflow Evaluation**

We will **extend the rag-eval-foundations pipeline** to evaluate complete DeepAgents workflows that integrate with adv-rag, providing end-to-end quality measurement and performance optimization feedback.

#### **Extended 4-Stage Evaluation Pipeline**

##### **Stage 1: Infrastructure + Agent Framework**
```yaml
# Extended infrastructure requirements
Infrastructure:
  - PostgreSQL: Evaluation data storage
  - Qdrant: Vector database for RAG
  - Redis: Caching for performance
  - Phoenix: Unified observability across DeepAgents + adv-rag

Agent_Framework:
  - DeepAgents: Agent orchestration ready
  - adv-rag: MCP server operational
  - MCP_Integration: DeepAgents → adv-rag connectivity validated
```

##### **Stage 2: Agent Workflow Dataset Generation**
```python
# Generate agent-specific evaluation datasets
async def generate_agent_evaluation_dataset():
    """Create evaluation dataset for agent workflows"""

    # 1. Agent task scenarios
    agent_scenarios = [
        {
            "task": "Research quantum computing applications in healthcare",
            "expected_planning": ["write_todos", "research", "synthesis"],
            "expected_rag_usage": ["semantic_retriever", "ensemble_retriever"],
            "complexity": "multi_step_research"
        },
        {
            "task": "Compare machine learning frameworks",
            "expected_planning": ["comparative_analysis", "criteria_definition"],
            "expected_rag_usage": ["multi_query_retriever", "contextual_compression"],
            "complexity": "comparative_analysis"
        }
    ]

    # 2. Generate golden test cases
    golden_agent_dataset = await generate_ragas_agent_testset(
        agent_scenarios,
        test_size=20,
        distributions={
            "simple_research": 0.3,
            "multi_step_research": 0.4,
            "comparative_analysis": 0.3
        }
    )

    return golden_agent_dataset
```

##### **Stage 3: Agent Workflow Execution**
```python
# Execute complete agent workflows for evaluation
async def execute_agent_workflows_for_evaluation():
    """Run agent workflows and capture comprehensive metrics"""

    # 1. Create DeepAgents with adv-rag integration
    agent = await create_deep_agent_with_rag_integration()

    # 2. Execute workflow with full tracing
    with phoenix_tracer.span("agent_workflow_evaluation") as span:
        # Planning phase
        with phoenix_tracer.span("agent_planning"):
            planning_result = await agent.planning_phase(task)

        # Execution phase with RAG integration
        with phoenix_tracer.span("agent_execution"):
            rag_calls = []
            for step in planning_result.steps:
                with phoenix_tracer.span("rag_integration"):
                    rag_result = await agent.use_rag_tool(step.query)
                    rag_calls.append(rag_result)

        # Synthesis phase
        with phoenix_tracer.span("agent_synthesis"):
            final_result = await agent.synthesize_results(rag_calls)

    return {
        "workflow_result": final_result,
        "planning_metrics": planning_result.metrics,
        "rag_usage_metrics": analyze_rag_usage(rag_calls),
        "performance_metrics": extract_timing_data(span)
    }
```

##### **Stage 4: Comprehensive Agent Evaluation**
```python
# RAGAS + Agent-specific metrics
async def comprehensive_agent_evaluation():
    """Evaluate agent workflows with extended metrics"""

    # 1. Traditional RAGAS metrics (from rag-eval-foundations)
    ragas_metrics = await evaluate_rag_quality(
        dataset=agent_golden_dataset,
        strategies=["semantic", "ensemble", "multi_query"]
    )

    # 2. Agent-specific metrics
    agent_metrics = await evaluate_agent_workflows(
        workflows=executed_workflows,
        metrics=[
            "planning_effectiveness",
            "rag_tool_selection_accuracy",
            "workflow_completion_rate",
            "context_utilization_efficiency"
        ]
    )

    # 3. Performance metrics
    performance_metrics = await evaluate_performance_targets(
        raw_retrieval_target="<2s",
        full_workflow_target="<8s",
        agent_workflow_target="<15s"  # New target for complete workflows
    )

    # 4. Integration metrics
    integration_metrics = await evaluate_mcp_integration(
        session_management="connection_storms_prevented",
        tool_vs_resource_usage="optimal_pattern_selection",
        error_handling="graceful_degradation"
    )

    return {
        "ragas_scores": ragas_metrics,
        "agent_effectiveness": agent_metrics,
        "performance_compliance": performance_metrics,
        "integration_quality": integration_metrics
    }
```

### **Agent-Specific Evaluation Metrics**

#### **1. Planning Effectiveness Metrics**
```python
def evaluate_planning_effectiveness(planning_result):
    """Measure quality of agent planning phase"""
    return {
        "todo_breakdown_quality": assess_todo_granularity(planning_result.todos),
        "task_dependency_accuracy": validate_dependency_graph(planning_result),
        "resource_estimation_accuracy": compare_estimated_vs_actual(planning_result),
        "planning_time_efficiency": measure_planning_overhead(planning_result)
    }
```

#### **2. RAG Integration Quality Metrics**
```python
def evaluate_rag_integration_quality(rag_usage_data):
    """Measure effectiveness of agent RAG tool usage"""
    return {
        "tool_selection_accuracy": analyze_optimal_tool_choice(rag_usage_data),
        "query_formulation_quality": assess_query_effectiveness(rag_usage_data),
        "context_utilization_rate": measure_context_usage(rag_usage_data),
        "cqrs_pattern_optimization": evaluate_tools_vs_resources_usage(rag_usage_data)
    }
```

#### **3. Workflow Completion Metrics**
```python
def evaluate_workflow_completion(workflow_results):
    """Measure end-to-end workflow success"""
    return {
        "task_completion_rate": calculate_successful_completions(workflow_results),
        "accuracy_vs_golden_standard": compare_with_expected_results(workflow_results),
        "error_recovery_effectiveness": analyze_error_handling(workflow_results),
        "resource_efficiency": measure_computational_resources(workflow_results)
    }
```

### **Performance Target Integration**

#### **Extended Performance Hierarchy**
```yaml
Performance_Targets:
  # Inherited from adv-rag (CQRS pattern)
  raw_retrieval: "<2 seconds"     # MCP Resources
  full_rag_pipeline: "<8 seconds" # MCP Tools

  # New agent workflow targets
  agent_planning: "<3 seconds"    # write_todos + planning
  agent_execution: "<12 seconds"  # planning + RAG + synthesis
  complete_workflow: "<15 seconds" # end-to-end agent task

Measurement_Points:
  - "MCP Resource calls": Direct vector retrieval
  - "MCP Tool calls": Complete RAG with synthesis
  - "Agent planning phase": Todo breakdown and strategy
  - "Agent execution phase": Multi-step RAG integration
  - "Agent synthesis phase": Final result compilation
```

#### **Performance Monitoring Integration**
```python
# Phoenix tracing for complete ecosystem performance
async def monitor_ecosystem_performance():
    """Monitor performance across entire DeepAgents ecosystem"""

    with phoenix_tracer.span("ecosystem_performance_measurement") as span:
        # Component-level performance
        adv_rag_performance = await measure_adv_rag_performance()
        deepagents_performance = await measure_deepagents_performance()
        integration_performance = await measure_integration_performance()

        # Cross-component optimization
        bottlenecks = identify_performance_bottlenecks([
            adv_rag_performance,
            deepagents_performance,
            integration_performance
        ])

        optimization_recommendations = generate_optimization_plan(bottlenecks)

        span.set_attributes({
            "ecosystem_health": calculate_overall_health(),
            "performance_grade": grade_against_targets(),
            "optimization_opportunities": len(optimization_recommendations)
        })

    return {
        "component_performance": {
            "adv_rag": adv_rag_performance,
            "deepagents": deepagents_performance,
            "integration": integration_performance
        },
        "ecosystem_metrics": {
            "overall_latency": calculate_p95_latency(),
            "success_rate": calculate_workflow_success_rate(),
            "resource_utilization": measure_resource_efficiency()
        },
        "recommendations": optimization_recommendations
    }
```

## Implementation Patterns

### **1. Agent Workflow Evaluation Pattern**

```python
# Complete agent workflow evaluation
async def evaluate_agent_workflow(task_description: str):
    """Evaluate complete DeepAgents workflow with RAGAS integration"""

    # 1. Setup evaluation environment
    evaluation_session = create_evaluation_session()
    agent = await create_deep_agent_with_rag()

    # 2. Execute workflow with comprehensive tracing
    with evaluation_session.trace("complete_agent_workflow"):
        # Planning evaluation
        planning_start = time.time()
        planning_result = await agent.planning_phase(task_description)
        planning_time = time.time() - planning_start

        # Execution evaluation
        execution_start = time.time()
        workflow_result = await agent.execute_workflow(planning_result)
        execution_time = time.time() - execution_start

        # Synthesis evaluation
        synthesis_start = time.time()
        final_answer = await agent.synthesize_final_answer(workflow_result)
        synthesis_time = time.time() - synthesis_start

    # 3. Comprehensive evaluation
    evaluation_results = {
        # Traditional RAGAS metrics
        "ragas_scores": await evaluate_with_ragas(final_answer),

        # Agent-specific metrics
        "planning_quality": evaluate_planning_effectiveness(planning_result),
        "execution_efficiency": evaluate_execution_quality(workflow_result),
        "synthesis_accuracy": evaluate_synthesis_quality(final_answer),

        # Performance metrics
        "timing_compliance": {
            "planning_time": planning_time,
            "execution_time": execution_time,
            "synthesis_time": synthesis_time,
            "total_workflow_time": planning_time + execution_time + synthesis_time,
            "meets_15s_target": (planning_time + execution_time + synthesis_time) < 15.0
        },

        # Integration metrics
        "mcp_usage_quality": evaluate_mcp_integration_patterns(workflow_result)
    }

    # 4. Store results in rag-eval-foundations PostgreSQL
    await store_evaluation_results(evaluation_results, evaluation_session.id)

    return evaluation_results
```

### **2. Continuous Evaluation Pattern**

```python
# Continuous evaluation integration
class ContinuousAgentEvaluation:
    """Continuous evaluation of agent workflows"""

    def __init__(self):
        self.evaluation_pipeline = create_evaluation_pipeline()
        self.quality_thresholds = {
            "ragas_answer_relevancy": 0.85,
            "ragas_context_precision": 0.80,
            "ragas_context_recall": 0.90,
            "agent_planning_effectiveness": 0.85,
            "workflow_completion_rate": 0.95
        }

    async def evaluate_agent_workflow(self, agent_workflow):
        """Evaluate single workflow and compare to thresholds"""
        results = await self.evaluation_pipeline.evaluate(agent_workflow)

        # Check quality gates
        quality_issues = []
        for metric, threshold in self.quality_thresholds.items():
            if results[metric] < threshold:
                quality_issues.append({
                    "metric": metric,
                    "actual": results[metric],
                    "threshold": threshold,
                    "severity": calculate_severity(results[metric], threshold)
                })

        return {
            "evaluation_results": results,
            "quality_gate_status": "PASS" if not quality_issues else "FAIL",
            "quality_issues": quality_issues,
            "recommendations": generate_improvement_recommendations(quality_issues)
        }

    async def batch_evaluation(self, agent_workflows):
        """Evaluate multiple workflows and generate trends"""
        results = []
        for workflow in agent_workflows:
            result = await self.evaluate_agent_workflow(workflow)
            results.append(result)

        # Trend analysis
        trends = analyze_quality_trends(results)

        return {
            "individual_results": results,
            "aggregate_metrics": calculate_aggregate_metrics(results),
            "quality_trends": trends,
            "ecosystem_health": assess_overall_ecosystem_health(results)
        }
```

### **3. Integration with Phoenix Observability**

```python
# Phoenix experiment tracking for agent evaluation
async def create_phoenix_agent_experiment():
    """Create Phoenix experiment for agent workflow evaluation"""

    experiment = px.Experiment(
        name="deepagents_rag_integration_evaluation",
        description="Comprehensive evaluation of DeepAgents with adv-rag integration",
        metadata={
            "evaluation_date": datetime.now().isoformat(),
            "deepagents_version": get_deepagents_version(),
            "adv_rag_version": get_adv_rag_version(),
            "evaluation_framework": "rag-eval-foundations-v2",
            "performance_targets": {
                "raw_retrieval": "2s",
                "full_workflow": "15s",
                "quality_threshold": "0.85"
            }
        }
    )

    # Track both component and integration metrics
    component_experiments = {
        "adv_rag_evaluation": await create_adv_rag_experiment(),
        "deepagents_evaluation": await create_deepagents_experiment(),
        "integration_evaluation": await create_integration_experiment()
    }

    return {
        "main_experiment": experiment,
        "component_experiments": component_experiments,
        "experiment_id": experiment.id
    }
```

## Evaluation Data Flow

### **Data Storage Strategy**
```sql
-- Extended PostgreSQL schema for agent evaluation
-- Extends existing rag-eval-foundations schema

-- Agent workflow evaluation results
CREATE TABLE agent_workflow_evaluations (
    id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(255),
    workflow_description TEXT,
    planning_metrics JSONB,
    execution_metrics JSONB,
    synthesis_metrics JSONB,
    ragas_scores JSONB,
    performance_metrics JSONB,
    integration_metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent planning effectiveness
CREATE TABLE agent_planning_analysis (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER REFERENCES agent_workflow_evaluations(id),
    todo_breakdown_quality FLOAT,
    dependency_accuracy FLOAT,
    resource_estimation_accuracy FLOAT,
    planning_time_seconds FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- MCP integration quality
CREATE TABLE mcp_integration_analysis (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER REFERENCES agent_workflow_evaluations(id),
    tool_selection_accuracy FLOAT,
    query_formulation_quality FLOAT,
    context_utilization_rate FLOAT,
    cqrs_pattern_optimization FLOAT,
    session_management_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **Cross-Repository Data Integration**
```python
# Integrate data from all three repositories
async def integrate_ecosystem_evaluation_data():
    """Combine evaluation data from entire ecosystem"""

    # DeepAgents: Agent planning and orchestration metrics
    deepagents_data = await extract_deepagents_metrics()

    # adv-rag: RAG performance and quality metrics
    adv_rag_data = await extract_adv_rag_metrics()

    # rag-eval-foundations: RAGAS scores and infrastructure metrics
    eval_foundations_data = await extract_evaluation_metrics()

    # Integration: Cross-repository performance and quality
    integration_data = await extract_integration_metrics()

    # Unified dataset for comprehensive analysis
    unified_dataset = {
        "ecosystem_performance": combine_performance_metrics([
            deepagents_data["performance"],
            adv_rag_data["performance"],
            eval_foundations_data["performance"],
            integration_data["performance"]
        ]),
        "quality_analysis": combine_quality_metrics([
            deepagents_data["quality"],
            adv_rag_data["quality"],
            eval_foundations_data["quality"],
            integration_data["quality"]
        ]),
        "trend_analysis": analyze_historical_trends([
            deepagents_data["trends"],
            adv_rag_data["trends"],
            eval_foundations_data["trends"]
        ])
    }

    return unified_dataset
```

## Consequences

### ✅ **Positive Outcomes**
- **Comprehensive Quality Measurement**: End-to-end agent workflow evaluation beyond just RAG
- **Performance Optimization**: Clear targets and measurement for all ecosystem components
- **Continuous Improvement**: Automated quality gates and trend analysis
- **Integration Validation**: Quantified measurement of MCP integration effectiveness

### ⚠️ **Implementation Complexity**
- **Extended Evaluation Pipeline**: More complex than RAG-only evaluation
  - *Mitigation*: Incremental implementation, reuse existing rag-eval-foundations infrastructure
- **Cross-Repository Coordination**: Evaluation spans all three repositories
  - *Mitigation*: Centralized evaluation orchestration in rag-eval-foundations
- **Performance Overhead**: Comprehensive evaluation adds latency
  - *Mitigation*: Async evaluation, separate evaluation environments

### 📋 **Implementation Requirements**
1. **Extended Dataset Generation**: Agent-specific test scenarios and golden datasets
2. **Performance Target Validation**: Automated checking of <2s/<8s/<15s targets
3. **Cross-Repository Metrics**: Unified data collection from all ecosystem components
4. **Continuous Evaluation Infrastructure**: Automated quality gates and trend monitoring

## Examples

### **✅ Complete Agent Workflow Evaluation**
```python
# Evaluate complete DeepAgents workflow
evaluation_result = await evaluate_agent_workflow(
    task="Research quantum computing applications in healthcare",
    expected_quality_threshold=0.85,
    performance_target_seconds=15
)

# Results include:
# - RAGAS scores (answer relevancy, context precision/recall, faithfulness)
# - Agent planning effectiveness
# - RAG tool selection accuracy
# - Performance compliance (raw retrieval <2s, full workflow <15s)
# - Integration quality (session management, CQRS usage)
```

### **✅ Continuous Quality Monitoring**
```python
# Continuous evaluation with quality gates
evaluation_pipeline = ContinuousAgentEvaluation()

# Batch evaluation of multiple workflows
batch_results = await evaluation_pipeline.batch_evaluation([
    "Research task 1",
    "Comparative analysis task 2",
    "Multi-step research task 3"
])

# Quality gate enforcement
if batch_results["quality_gate_status"] == "FAIL":
    alert_quality_regression(batch_results["quality_issues"])
    trigger_optimization_workflow(batch_results["recommendations"])
```

### **❌ Incorrect Evaluation Approach**
```python
# Don't evaluate RAG components in isolation
rag_only_evaluation = await evaluate_rag_strategies_only()  # ❌ Incomplete

# Don't skip performance measurement
evaluation_without_timing = await evaluate_quality_only()  # ❌ Missing performance

# Don't ignore integration quality
evaluation_without_mcp = await evaluate_agent_only()  # ❌ Missing integration metrics
```

## References
- [Repository Separation Pattern](./adr-004-repository-separation-pattern.md)
- [MCP Integration Triangle Pattern](./adr-005-mcp-integration-triangle-pattern.md)
- [CQRS MCP Implementation Pattern](./adr-009-cqrs-mcp-implementation-pattern.md)
- [Infrastructure Centralization Pattern](./adr-008-infrastructure-centralization-pattern.md)
- [RAGAS Framework Documentation](https://docs.ragas.io/)
- [Phoenix Experiments Documentation](https://docs.arize.com/phoenix)

---

**Key Principle**: Evaluation integration extends beyond RAG component testing to measure complete agent workflows, including planning effectiveness, RAG integration quality, and ecosystem performance against <2s/<8s/<15s targets.