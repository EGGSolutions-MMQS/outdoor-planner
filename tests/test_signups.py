from outdoor_planner.extensions import db
from outdoor_planner.models import Outing, Signup


def _count(app, outing_id):
    with app.app_context():
        return len(db.session.get(Outing, outing_id).signups)


def test_signup_beyond_available_seats_is_refused(app, client, make_user, make_outing, login):
    organizer_id = make_user("owner_org", "organizer")
    make_user("part_uno", "participant")
    make_user("part_due", "participant")
    outing_id = make_outing(organizer_id, seats=1)

    login("part_uno")
    client.post(f"/outings/{outing_id}/signup")
    login("part_due")
    response = client.post(f"/outings/{outing_id}/signup", follow_redirects=True)
    assert b"Posti esauriti" in response.data
    assert _count(app, outing_id) == 1


def test_double_signup_and_unsubscribe(app, client, make_user, make_outing, login):
    organizer_id = make_user("owner_org", "organizer")
    make_user("part_uno", "participant")
    outing_id = make_outing(organizer_id, seats=3)

    login("part_uno")
    client.post(f"/outings/{outing_id}/signup")
    client.post(f"/outings/{outing_id}/signup")
    assert _count(app, outing_id) == 1
    client.post(f"/outings/{outing_id}/unsubscribe")
    assert _count(app, outing_id) == 0


def test_organizer_cannot_sign_up(app, client, make_user, make_outing, login):
    organizer_id = make_user("owner_org", "organizer")
    outing_id = make_outing(organizer_id)
    login("owner_org")
    assert client.post(f"/outings/{outing_id}/signup").status_code == 403


def test_no_signup_or_comment_on_past_outing(app, client, make_user, make_outing, login):
    organizer_id = make_user("owner_org", "organizer")
    make_user("part_uno", "participant")
    outing_id = make_outing(organizer_id, days=-2)
    login("part_uno")
    client.post(f"/outings/{outing_id}/signup")
    client.post(f"/outings/{outing_id}/comments", data={"body": "Tardi"})
    assert _count(app, outing_id) == 0
    with app.app_context():
        assert db.session.query(Signup).count() == 0
        assert db.session.get(Outing, outing_id).comments == []
    assert client.get(f"/outings/{outing_id}").status_code == 200


def test_only_organizer_sees_attendee_list(client, make_user, make_outing, login):
    organizer_id = make_user("owner_org", "organizer")
    make_user("part_uno", "participant")
    outing_id = make_outing(organizer_id)
    login("part_uno")
    client.post(f"/outings/{outing_id}/signup")
    assert b"Iscritti (" not in client.get(f"/outings/{outing_id}").data
    login("owner_org")
    assert b"Iscritti (1)" in client.get(f"/outings/{outing_id}").data
