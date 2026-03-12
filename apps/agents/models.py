"""
apps/agents/models.py

AI agent infrastructure for the ERP (backed by LangChain + GPT-4o).

Built-in agent types:
  1. inventory_monitor    — detects low stock, expiry, reorder needs
  2. sales_analyst        — forecasts, pipeline insights, upsell suggestions
  3. finance_auditor      — anomaly detection, budget alerts, reconciliation
  4. hr_assistant         — leave management, payroll anomalies, headcount planning
  5. crm_manager          — prospect scoring, deal nudges, campaign optimisation
  6. procurement_advisor  — vendor scoring, price benchmarking, demand forecasting
  7. general_assistant    — free-form Q&A over all ERP data

Covers:
  - AgentDefinition (config, tool list, LLM params)
  - AgentTask (single invocation: prompt → response)
  - AgentAction (individual LangChain tool calls inside a task)
  - AgentMemory (persistent key-value + vector store metadata)
  - AgentAlert (condition-triggered automated notifications)
  - AgentSchedule (cron-driven periodic tasks)
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantAwareModel


# ─────────────────────────────────────────────────────────────────────────────
# Agent Definition  (one per agent-type per tenant)
# ─────────────────────────────────────────────────────────────────────────────

class AgentDefinition(TenantAwareModel):
    AGENT_TYPE_CHOICES = [
        ("inventory_monitor", _("Inventory Monitor")),
        ("sales_analyst", _("Sales Analyst")),
        ("finance_auditor", _("Finance Auditor")),
        ("hr_assistant", _("HR Assistant")),
        ("crm_manager", _("CRM Manager")),
        ("procurement_advisor", _("Procurement Advisor")),
        ("general_assistant", _("General Assistant")),
        ("custom", _("Custom")),
    ]

    name = models.CharField(_("Agent Name"), max_length=100)
    agent_type = models.CharField(_("Agent Type"), max_length=30, choices=AGENT_TYPE_CHOICES)
    description = models.TextField(blank=True)

    # LLM configuration
    llm_provider = models.CharField(
        _("LLM Provider"), max_length=30, default="openai",
        choices=[("openai", "OpenAI"), ("anthropic", "Anthropic"), ("google", "Google"), ("local", "Local")]
    )
    llm_model = models.CharField(_("Model"), max_length=60, default="gpt-4o")
    temperature = models.FloatField(_("Temperature"), default=0.1)
    max_tokens = models.PositiveIntegerField(_("Max Tokens"), default=2048)
    system_prompt = models.TextField(
        _("System Prompt"),
        blank=True,
        help_text=_("The system-level instruction prepended to every conversation.")
    )

    # LangChain tools this agent is allowed to use (list of tool names)
    tool_list = models.JSONField(
        _("Allowed Tools"), default=list, blank=True,
        help_text=_("List of LangChain/custom tool names the agent can invoke.")
    )
    # Extra config (e.g. temperature overrides, retriever config)
    extra_config = models.JSONField(_("Extra Config"), default=dict, blank=True)
    # Vector store / embedding config
    vector_store_namespace = models.CharField(
        _("Vector Store Namespace"), max_length=100, blank=True,
        help_text=_("Pin-econe/Chroma namespace for this agent's retrieval memory.")
    )

    class Meta:
        verbose_name = _("Agent Definition")
        verbose_name_plural = _("Agent Definitions")
        unique_together = ("agent_type",)  # one of each type per tenant schema
        ordering = ["agent_type"]

    def __str__(self):
        return f"{self.name} ({self.agent_type})"


# ─────────────────────────────────────────────────────────────────────────────
# Agent Task  (single invocation / conversation turn)
# ─────────────────────────────────────────────────────────────────────────────

class AgentTask(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("running", _("Running")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
        ("cancelled", _("Cancelled")),
    ]

    agent = models.ForeignKey(AgentDefinition, on_delete=models.CASCADE, related_name="tasks")
    initiated_by = models.ForeignKey(
        "party.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="agent_tasks"
    )
    # Triggered by a schedule or an alert → nullable
    schedule = models.ForeignKey(
        "AgentSchedule", on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )
    alert = models.ForeignKey(
        "AgentAlert", on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )

    input_prompt = models.TextField(_("Input Prompt"))
    output = models.TextField(_("Output"), blank=True)
    status = models.CharField(_("Status"), max_length=15, choices=STATUS_CHOICES, default="pending")

    started_at = models.DateTimeField(_("Started At"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    execution_time_ms = models.PositiveIntegerField(_("Execution Time (ms)"), null=True, blank=True)

    # Token usage
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True)
    # Conversation history (list of {"role": ..., "content": ...})
    conversation_history = models.JSONField(_("Conversation History"), default=list, blank=True)

    class Meta:
        verbose_name = _("Agent Task")
        verbose_name_plural = _("Agent Tasks")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.agent} task @ {self.created_at:%Y-%m-%d %H:%M} [{self.status}]"


# ─────────────────────────────────────────────────────────────────────────────
# Agent Action  (individual tool call within a task)
# ─────────────────────────────────────────────────────────────────────────────

class AgentAction(TenantAwareModel):
    """
    One ReAct thought-action-observation step inside a AgentTask.
    Mirrors LangChain's AgentAction structure for full traceability.
    """
    task = models.ForeignKey(AgentTask, on_delete=models.CASCADE, related_name="actions")
    sequence = models.PositiveSmallIntegerField(_("Sequence"), default=0)
    thought = models.TextField(_("Thought / Reasoning"), blank=True)
    tool_name = models.CharField(_("Tool Name"), max_length=100)
    tool_input = models.JSONField(_("Tool Input"), default=dict)
    tool_output = models.TextField(_("Tool Output"), blank=True)
    is_final_answer = models.BooleanField(_("Final Answer"), default=False)
    latency_ms = models.PositiveIntegerField(_("Latency (ms)"), null=True, blank=True)

    class Meta:
        verbose_name = _("Agent Action")
        verbose_name_plural = _("Agent Actions")
        ordering = ["task", "sequence"]

    def __str__(self):
        return f"{self.task} — step {self.sequence}: {self.tool_name}"


# ─────────────────────────────────────────────────────────────────────────────
# Agent Memory  (persistent key-value, scoped per agent)
# ─────────────────────────────────────────────────────────────────────────────

class AgentMemory(TenantAwareModel):
    """
    Lightweight key-value store for agent state that must survive
    between tasks (e.g. last-checked stock level, running totals).
    For vector/semantic memory, use the vector_store_namespace on AgentDefinition.
    """
    agent = models.ForeignKey(AgentDefinition, on_delete=models.CASCADE, related_name="memories")
    # Optional scoping to a specific user session
    user = models.ForeignKey(
        "party.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="agent_memories"
    )
    key = models.CharField(_("Key"), max_length=200)
    value = models.JSONField(_("Value"), default=dict)
    expires_at = models.DateTimeField(_("Expires At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Agent Memory")
        verbose_name_plural = _("Agent Memories")
        unique_together = ("agent", "user", "key")
        ordering = ["agent", "key"]

    def __str__(self):
        return f"{self.agent} memory: {self.key}"

    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Agent Alert  (condition-driven automatic task spawning)
# ─────────────────────────────────────────────────────────────────────────────

class AgentAlert(TenantAwareModel):
    """
    Declarative alert rule.  When the condition_expression evaluates True
    (evaluated by Celery beat), a new AgentTask is spawned automatically
    and, optionally, a Notification is broadcast.
    """
    SEVERITY_CHOICES = [
        ("info", _("Info")),
        ("warning", _("Warning")),
        ("error", _("Error")),
        ("critical", _("Critical")),
    ]

    agent = models.ForeignKey(AgentDefinition, on_delete=models.CASCADE, related_name="alerts")
    name = models.CharField(_("Alert Name"), max_length=100)
    description = models.TextField(blank=True)
    severity = models.CharField(_("Severity"), max_length=10, choices=SEVERITY_CHOICES, default="warning")

    # JSONLogic / Python-safe expression evaluated by the Celery alert-checker task
    condition_expression = models.JSONField(
        _("Condition Expression"), default=dict,
        help_text=_(
            "JSONLogic rule evaluated against ERP data snapshots.  "
            "Example: {\"<\": [{\"var\": \"inventory.qty_on_hand\"}, {\"var\": \"reorder_point\"}]}"
        )
    )
    # The prompt to send to the agent when condition triggers
    trigger_prompt = models.TextField(
        _("Trigger Prompt"),
        help_text=_("The prompt injected into the agent task when this alert fires.")
    )

    is_triggered = models.BooleanField(_("Currently Triggered"), default=False)
    last_triggered_at = models.DateTimeField(_("Last Triggered At"), null=True, blank=True)
    trigger_count = models.PositiveIntegerField(_("Trigger Count"), default=0)

    # Who gets notified when alert fires
    notify_users = models.ManyToManyField(
        "party.User", blank=True, related_name="watched_agent_alerts"
    )
    notification_template = models.ForeignKey(
        "notifications.NotificationTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="agent_alerts"
    )

    class Meta:
        verbose_name = _("Agent Alert")
        verbose_name_plural = _("Agent Alerts")
        ordering = ["severity", "name"]

    def __str__(self):
        return f"[{self.severity}] {self.name}"


# ─────────────────────────────────────────────────────────────────────────────
# Agent Schedule  (cron-driven periodic runs)
# ─────────────────────────────────────────────────────────────────────────────

class AgentSchedule(TenantAwareModel):
    """
    Periodic schedule for automated agent tasks (powered by Celery beat).
    cron_expression follows standard 5-field cron syntax (minute hour day month weekday).
    """
    agent = models.ForeignKey(AgentDefinition, on_delete=models.CASCADE, related_name="schedules")
    name = models.CharField(_("Schedule Name"), max_length=100)
    description = models.TextField(blank=True)
    cron_expression = models.CharField(
        _("Cron Expression"), max_length=50, default="0 8 * * 1-5",
        help_text=_("Standard 5-field cron. e.g. '0 8 * * 1-5' = weekdays at 08:00.")
    )
    prompt_template = models.TextField(
        _("Prompt Template"),
        help_text=_("The prompt sent to the agent on each run. Supports {{ date }} and {{ tenant }} vars.")
    )
    is_enabled = models.BooleanField(_("Enabled"), default=True)
    last_run_at = models.DateTimeField(_("Last Run At"), null=True, blank=True)
    next_run_at = models.DateTimeField(_("Next Run At"), null=True, blank=True)
    run_count = models.PositiveIntegerField(_("Run Count"), default=0)
    last_status = models.CharField(
        _("Last Run Status"), max_length=15,
        choices=AgentTask.STATUS_CHOICES, blank=True
    )

    class Meta:
        verbose_name = _("Agent Schedule")
        verbose_name_plural = _("Agent Schedules")
        ordering = ["agent", "name"]

    def __str__(self):
        enabled = "✓" if self.is_enabled else "✗"
        return f"{enabled} {self.agent} | {self.name} [{self.cron_expression}]"


# ─────────────────────────────────────────────────────────────────────────────
# Agent Feedback  (human-in-the-loop quality scoring)
# ─────────────────────────────────────────────────────────────────────────────

class AgentFeedback(TenantAwareModel):
    """
    Allows users to rate agent task outputs — feeds into fine-tuning pipeline.
    """
    task = models.OneToOneField(AgentTask, on_delete=models.CASCADE, related_name="feedback")
    rated_by = models.ForeignKey(
        "party.User", on_delete=models.SET_NULL, null=True, related_name="agent_feedback"
    )
    rating = models.PositiveSmallIntegerField(
        _("Rating (1-5)"), choices=[(i, str(i)) for i in range(1, 6)]
    )
    was_helpful = models.BooleanField(_("Helpful"), default=True)
    comment = models.TextField(blank=True)
    correct_output = models.TextField(
        _("Correct Output"), blank=True,
        help_text=_("If the agent was wrong, provide the ideal output here.")
    )

    class Meta:
        verbose_name = _("Agent Feedback")
        verbose_name_plural = _("Agent Feedback")

    def __str__(self):
        return f"Feedback on {self.task}: {self.rating}/5"
