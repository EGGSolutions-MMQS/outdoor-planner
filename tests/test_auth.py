from outdoor_planner.extensions import db
from outdoor_planner.models import User


def test_register_stores_hashed_password(app, client):
    response = client.post(
        "/register",
        data={"username": "nuovo_utente", "password": "password-lunga-1", "role": "participant"},
    )
    assert response.status_code == 302
    with app.app_context():
        user = db.session.execute(db.select(User).filter_by(username="nuovo_utente")).scalar_one()
        assert user.role == "participant"
        assert user.password_hash != "password-lunga-1"
        assert user.check_password("password-lunga-1")


def test_register_rejects_duplicate_username_and_short_password(client):
    data = {"username": "doppio", "password": "password-lunga-1", "role": "organizer"}
    client.post("/register", data=data)
    assert b"gi\xc3\xa0 in uso" in client.post("/register", data=data).data
    short = client.post(
        "/register", data={"username": "altro", "password": "corta", "role": "organizer"}
    )
    assert short.status_code == 200


def test_register_rejects_unknown_role(client):
    response = client.post(
        "/register", data={"username": "furbo", "password": "password-lunga-1", "role": "admin"}
    )
    assert response.status_code == 200


def test_login_and_logout(make_user, client, login):
    make_user("marco_t", "participant")
    assert login("marco_t").status_code == 302
    assert client.get("/outings/new").status_code == 403  # logged in, wrong role
    client.post("/logout")
    assert client.get("/outings/new").status_code == 302  # anonymous -> login


def test_login_wrong_password(make_user, client):
    make_user("marco_t", "participant")
    response = client.post("/login", data={"username": "marco_t", "password": "sbagliata"})
    assert response.status_code == 200
    assert b"Credenziali non valide" in response.data
