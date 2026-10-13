from app.models import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    employees = db.relationship("Employee", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"
