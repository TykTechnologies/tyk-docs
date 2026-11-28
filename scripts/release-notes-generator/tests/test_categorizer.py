from release_notes_generator.categorizer import categorize_ticket, group_tickets_by_component, infer_component_from_fix_version
from release_notes_generator.models import Ticket

def _t(key="TT-1", issue_type="Bug", components=None, summary=None):
    return Ticket(key=key, summary=summary or f"Test {key}", issue_type=issue_type, components=components or [])

class TestCategorizeTicket:
    def test_bug(self): assert categorize_ticket(_t(issue_type="Bug")) == "Fixed"
    def test_story(self): assert categorize_ticket(_t(issue_type="Story")) == "Added"
    def test_new_feature(self): assert categorize_ticket(_t(issue_type="New Feature")) == "Added"
    def test_task(self): assert categorize_ticket(_t(issue_type="Task")) == "Changed"
    def test_improvement(self): assert categorize_ticket(_t(issue_type="Improvement")) == "Changed"
    def test_security(self): assert categorize_ticket(_t(issue_type="Security")) == "Security Fixes"
    def test_unknown(self): assert categorize_ticket(_t(issue_type="X")) == "Changed"

    # Keyword override tests: Stories that are really "Changed".
    def test_update_go_story_becomes_changed(self):
        t = _t(issue_type="Story", summary="Update Dashboard to Go 1.25")
        assert categorize_ticket(t) == "Changed"

    def test_upgrade_story_becomes_changed(self):
        t = _t(issue_type="Story", summary="Upgrade Redis client library")
        assert categorize_ticket(t) == "Changed"

    def test_bump_story_becomes_changed(self):
        t = _t(issue_type="Story", summary="Bump Go version to 1.25")
        assert categorize_ticket(t) == "Changed"

    def test_replace_story_becomes_changed(self):
        t = _t(issue_type="Story", summary="Replace legacy auth module")
        assert categorize_ticket(t) == "Changed"

    def test_real_feature_story_stays_added(self):
        t = _t(issue_type="Story", summary="Add support for OpenAPI 3.1")
        assert categorize_ticket(t) == "Added"

    def test_bug_not_affected_by_keyword_override(self):
        t = _t(issue_type="Bug", summary="Update breaks on restart")
        assert categorize_ticket(t) == "Fixed"

class TestInferComponentFromFixVersion:
    def test_portal(self): assert infer_component_from_fix_version("Tyk Portal 1.17.1") == "Tyk Portal"
    def test_gateway(self): assert infer_component_from_fix_version("Tyk Gateway 5.8.0") == "Tyk Gateway"
    def test_dashboard(self): assert infer_component_from_fix_version("Tyk Dashboard 5.12.0") == "Tyk Dashboard"
    def test_charts(self): assert infer_component_from_fix_version("Tyk Charts 5.1.1") == "Tyk Charts"
    def test_helm(self): assert infer_component_from_fix_version("Tyk Helm 2.0") == "Tyk Charts"
    def test_ambiguous(self): assert infer_component_from_fix_version("Tyk 5.13.0") is None
    def test_empty(self): assert infer_component_from_fix_version("") is None

class TestGroupTicketsByComponent:
    def test_groups(self):
        g = group_tickets_by_component([_t("1", components=["Tyk Gateway"]), _t("2", components=["Tyk Gateway"]), _t("3", components=["Tyk Dashboard"])])
        assert len(g["Tyk Gateway"]) == 2 and len(g["Tyk Dashboard"]) == 1

    def test_multi_component(self):
        g = group_tickets_by_component([_t("1", components=["Tyk Gateway", "Tyk Dashboard"])])
        assert "1" in [t.key for t in g["Tyk Gateway"]] and "1" in [t.key for t in g["Tyk Dashboard"]]

    def test_unknown_skipped_without_fix_version(self):
        assert len(group_tickets_by_component([_t(components=["Unknown"])])) == 0

    def test_empty_skipped_without_fix_version(self):
        assert len(group_tickets_by_component([_t(components=[])])) == 0

    def test_fallback_from_fix_version(self):
        """Tickets with no component get assigned based on fix version name."""
        g = group_tickets_by_component([_t("TT-1", components=[])], fix_version="Tyk Portal 1.17.1")
        assert "Tyk Portal" in g
        assert g["Tyk Portal"][0].key == "TT-1"

    def test_fallback_mixed(self):
        """Tickets with components are grouped normally; those without use fallback."""
        tickets = [
            _t("TT-1", components=["Tyk Portal"]),
            _t("TT-2", components=[]),
        ]
        g = group_tickets_by_component(tickets, fix_version="Tyk Portal 1.17.1")
        assert len(g["Tyk Portal"]) == 2

    def test_no_fallback_for_ambiguous_version(self):
        """'Tyk 5.13.0' is ambiguous — no fallback, ticket is skipped."""
        g = group_tickets_by_component([_t(components=[])], fix_version="Tyk 5.13.0")
        assert len(g) == 0
