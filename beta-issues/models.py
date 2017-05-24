from .database import db


class Issues(db.Model):
    id = db.Column('issue_id', db.Integer, primary_key=True)
    issue = db.Column(db.String(20))
    evektor = db.Column(db.Boolean(), default=False)
    description = db.Column(db.Text)
    details = db.Column(db.Text)
    author = db.Column(db.String(20))
    date_issued = db.Column(db.String(20))
    date_resolved = db.Column(db.String(20))
    version = db.Column(db.String(20))
    resolved = db.Column(db.Boolean(), default=False)

    def __repr__(self):
        return 'Issue({}): Eve({}) - DateIssued({}) - Res({})'.format(
            self.issue, self.evektor, self.date_issued, self.resolved)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    password = db.Column(db.String(50))
    email = db.Column(db.String(50))
    settings = db.Column(db.Text, default=None)

    def __repr__(self):
        return 'User({}): E-mail({})'.format(self.username, self.email)
