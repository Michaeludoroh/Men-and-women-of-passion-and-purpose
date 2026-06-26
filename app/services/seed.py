from ..extensions import db
from ..models import Leader


def seed_default_leaders():
    if Leader.query.first():
        return

    minister_joy = Leader(
        name="Minister Joy",
        role="Founder & Senior Pastor",
        title="Apostle of Prayer & Teacher of the Word",
        bio=(
            "Apostle of prayer, teacher of the Word, and spiritual mother to nations. "
            "Leading with fire, purpose, and divine wisdom for over 25 years."
        ),
        is_founder=True,
        display_order=1,
    )
    db.session.add(minister_joy)
    db.session.commit()
