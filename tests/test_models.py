import sys
sys.path.append("/app")

from datetime import date
from app.models import db, Family, Member

def test_add_family_with_members(app):
    with app.app_context():
        # Create a family
        family = Family(name="Astle")
        db.session.add(family)
        db.session.commit()

        # Add 3 members with DOBs
        members = [
            Member(name="John", dob=date(2008, 5, 1), family_id=family.id),  # age ~17
            Member(name="Jane", dob=date(2013, 8, 20), family_id=family.id), # age ~12
            Member(name="Mark", dob=date(2000, 1, 10), family_id=family.id), # age ~25
        ]
        db.session.add_all(members)
        db.session.commit()

        # Fetch family and verify
        saved_family = Family.query.filter_by(name="Astle").first()
        assert saved_family is not None

        # Fetch members via relationship or query
        member_list = Member.query.filter_by(family_id=saved_family.id).all()
        assert len(member_list) == 3

        # Check for adult member
        adult_members = [m for m in member_list if m.age >= 18]
        assert len(adult_members) == 1
        assert adult_members[0].name == "Mark"
