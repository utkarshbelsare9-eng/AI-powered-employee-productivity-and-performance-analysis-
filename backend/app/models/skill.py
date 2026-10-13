from app.models import db


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.Integer, default=50)  # 0-100

    def __repr__(self):
        return f"<Skill {self.name} ({self.proficiency}%)>"
