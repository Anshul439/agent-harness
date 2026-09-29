from example import login


def test_login_with_user():
    assert login("anshul") == "logged in"


def test_login_without_user():
    assert login(None) == "login failed"
