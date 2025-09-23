import sys
sys.path.append("/app")
from app.models import db, Family, Member

def test_add_family_with_members(app):
    with app.app_context():
        # Create a family
        family = Family(name="Astle")
        db.session.add(family)
        db.session.commit()

        # Add 3 members
        members = [
            Member(name="John", age=17, family_id=family.id),
            Member(name="Jane", age=12, family_id=family.id),
            Member(name="Mark", age=21, family_id=family.id),  # Adult
        ]
        db.session.add_all(members)
        db.session.commit()

        # Fetch family and verify
        saved_family = Family.query.filter_by(name="Astle").first()
        assert saved_family is not None
        assert len(saved_family.members) == 3

        # Check for adult member
        adult_members = [m for m in saved_family.members if m.age >= 18]
        assert len(adult_members) == 1
        assert adult_members[0].name == "Mark"
