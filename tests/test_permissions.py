from outdoor_planner.extensions import db
from outdoor_planner.models import Outing


def test_organizer_cannot_edit_or_delete_other_organizer_outing(
    app, client, make_user, make_outing, login
):
    owner_id = make_user("owner_org", "organizer")
    make_user("other_org", "organizer")
    outing_id = make_outing(owner_id)

    login("other_org")
    assert client.get(f"/outings/{outing_id}/edit").status_code == 403
    assert client.post(f"/outings/{outing_id}/edit", data={"title": "Hack"}).status_code == 403
    assert client.post(f"/outings/{outing_id}/delete").status_code == 403
    with app.app_context():
        assert db.session.get(Outing, outing_id).title == "Gita di prova"


def test_owner_can_delete_own_outing(app, client, make_user, make_outing, login):
    owner_id = make_user("owner_org", "organizer")
    outing_id = make_outing(owner_id)
    login("owner_org")
    assert client.get(f"/outings/{outing_id}/edit").status_code == 200
    assert client.post(f"/outings/{outing_id}/delete").status_code == 302
    with app.app_context():
        assert db.session.get(Outing, outing_id) is None


def test_participant_cannot_create_outing(client, make_user, login):
    make_user("part_user", "participant")
    login("part_user")
    assert client.get("/outings/new").status_code == 403


def test_comment_can_only_be_deleted_by_author(app, client, make_user, make_outing, login):
    owner_id = make_user("owner_org", "organizer")
    make_user("autore_c", "participant")
    make_user("altro_c", "participant")
    outing_id = make_outing(owner_id)

    login("autore_c")
    client.post(f"/outings/{outing_id}/comments", data={"body": "Ciao a tutti"})
    login("altro_c")
    assert client.post("/outings/comments/1/delete").status_code == 403
    login("autore_c")
    assert client.post("/outings/comments/1/delete").status_code == 302
