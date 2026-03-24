from release_notes_generator.categorizer import categorize_ticket, group_tickets_by_component
from release_notes_generator.models import Ticket

def _t(key="TT-1", issue_type="Bug", components=None):
    return Ticket(key=key, summary=f"Test {key}", issue_type=issue_type, components=components or [])

class TestCategorizeTicket:
    def test_bug(self): assert categorize_ticket(_t(issue_type="Bug")) == "Fixed"
    def test_story(self): assert categorize_ticket(_t(issue_type="Story")) == "Added"
    def test_new_feature(self): assert categorize_ticket(_t(issue_type="New Feature")) == "Added"
    def test_task(self): assert categorize_ticket(_t(issue_type="Task")) == "Changed"
    def test_improvement(self): assert categorize_ticket(_t(issue_type="Improvement")) == "Changed"
    def test_security(self): assert categorize_ticket(_t(issue_type="Security")) == "Security Fixes"
    def test_unknown(self): assert categorize_ticket(_t(issue_type="X")) == "Changed"

class TestGroupTicketsByComponent:
    def test_groups(self):
        g = group_tickets_by_component([_t("1", components=["Tyk Gateway"]), _t("2", components=["Tyk Gateway"]), _t("3", components=["Tyk Dashboard"])])
        assert len(g["Tyk Gateway"]) == 2 and len(g["Tyk Dashboard"]) == 1
    def test_multi_component(self):
        g = group_tickets_by_component([_t("1", components=["Tyk Gateway", "Tyk Dashboard"])])
        assert "1" in [t.key for t in g["Tyk Gateway"]] and "1" in [t.key for t in g["Tyk Dashboard"]]
    def test_unknown_skipped(self):
        assert len(group_tickets_by_component([_t(components=["Unknown"])])) == 0
    def test_empty_skipped(self):
        assert len(group_tickets_by_component([_t(components=[])])) == 0
