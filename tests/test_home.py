def test_home_lists_only_future_outings_and_searches(client, make_user, make_outing):
    organizer_id = make_user("owner_org", "organizer")
    make_outing(organizer_id, days=5, title="Monte Alto")
    make_outing(organizer_id, days=6, title="Giro in bici")
    make_outing(organizer_id, days=-3, title="Gita passata")

    page = client.get("/").data
    assert b"Monte Alto" in page and b"Giro in bici" in page
    assert b"Gita passata" not in page

    found = client.get("/?q=bici").data
    assert b"Giro in bici" in found and b"Monte Alto" not in found
    assert b"Giro in bici" in client.get("/?q=bergamo").data  # matches location
    assert b"Nessuna uscita trovata" in client.get("/?q=%25").data  # % is literal


def test_footer_has_open_meteo_attribution(client):
    assert b"Dati meteo:" in client.get("/").data
    assert b"CC BY 4.0" in client.get("/").data
