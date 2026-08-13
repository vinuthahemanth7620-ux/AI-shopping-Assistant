from app import db


class TeamMember(db.Model):
    """
    TeamMember Model representing official project team members.
    Table: team_members
    Enforces strict data isolation: only records marked with is_official=True
    and matching official project configurations are displayed.
    """
    __tablename__ = 'team_members'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    contribution = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(20), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    is_official = db.Column(db.Boolean, default=False, nullable=False, index=True)

    @classmethod
    def seed_official_members(cls):
        """Seed the 2 official project team members if not present."""
        official_data = [
            {
                'name': 'VINUTHA',
                'role': 'AI & Python Backend Developer',
                'contribution': 'Contributes to the Flask backend, MySQL database, AI Shopping Assistant, authentication, and product management modules.',
                'email': 'vinuthahemanth7620@gmail.com',
                'phone': '7259886752',
                'github_url': 'https://github.com/vinuthahemanth7620',
                'linkedin_url': 'https://www.linkedin.com/in/vinutha467304310',
                'is_official': True
            },
            {
                'name': 'THANUSHREE P.H',
                'role': 'Frontend & UI/UX Developer',
                'contribution': 'Contributes to UI design, responsive frontend development, product catalog presentation, and overall user experience.',
                'email': 'thanushreeph14@gmail.com',
                'phone': '6363507368',
                'github_url': 'https://github.com/thanushreeph14-del',
                'linkedin_url': 'https://www.linkedin.com/in/thanushree-ph',
                'is_official': True
            }
        ]

        for data in official_data:
            member = cls.query.filter_by(email=data['email']).first()
            if not member:
                member = cls(**data)
                db.session.add(member)
            else:
                # Update to ensure fields match exact official specification
                member.name = data['name']
                member.role = data['role']
                member.contribution = data['contribution']
                member.phone = data['phone']
                member.github_url = data['github_url']
                member.linkedin_url = data['linkedin_url']
                member.is_official = True
        
        db.session.commit()
